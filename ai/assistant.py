import os
import asyncio
import json
import datetime
from openai import OpenAI

import tools
from utils.config import Config
from utils.io import IOlog
from utils.spinner import spinner

CFG = Config()
client = OpenAI()

class Assistant():
    def __init__(self, role: str, name: str = "Assistant", model: str = 'gpt-3.5-turbo-1106', iol: IOlog = None, tools = None, messages = None, target_dir:str='fixed', know_file="699.csv") -> None:
        """
        Initialize the AI object with empty lists of tool functions and default file for knowledge retrieval.
        """
        self.iol = iol
        self.target_dir = target_dir
        self.name = name
        self.instructions = role
        self.file_ids = []
        if CFG.retrieval: self.file_ids.append(self.upload_file(know_file).id)
        self.assistant = client.beta.assistants.create(
            name=name,
            instructions=self.instructions,
            model=model,
            # temperature=CFG.temperature,
            # seed=dbs.prompts['seed']
            # response_format='json_object',
            file_ids=self.file_ids,
            tools=tools if tools else [{"type": "code_interpreter"}, {"type": "retrieval"}]  
        )
        self.thread = client.beta.threads.create(messages = messages)


    def start(self, system: str, user: str) -> list[dict[str, str]]:
        user_msg = self.fuser(user)
        self.instructions = self.fsystem(system)

        return self.next([user_msg])
    
    def fassistant(self, msg: str) -> dict[str, str]:
        thread_message = client.beta.threads.messages.create(
            self.thread.id,
            role="assistant",
            content=msg,
            )
        return thread_message
    
    def fsystem(self, msg: str) -> dict[str, str]:
        self.assistant.instructions = msg
    
    def fuser(self, msg: str) -> dict[str, str]:
        thread_message = client.beta.threads.messages.create(
            self.thread.id,
            role="user",
            content=msg,
        )
        return thread_message
    
    def upload_file(self, file_path: str):  # -> OpenAI.File
        file = client.files.create(file=open(file_path, "rb"), purpose="assistants")
        return file
    
    def messages_to_thread(self, messages: list[dict[str, str]]):
        for message in messages:
            if isinstance(message, dict):
                if message['role'] == 'user':
                    self.fuser(message)
                elif message['role'] == 'assistant':
                    self.fassistant(message)
                elif message['role'] == 'system':
                    self.fsystem(message)
            else:
                return messages

    async def next(self, messages: list[dict[str, str]]=None, prompt=None, scan_dir: str = 'fixes'):
        if messages:
            self.messages_to_thread(messages)
            self.iol.print("Messages added to the thread.", color="bright_black", verbose_only=True)

        if prompt:
            self.fuser(self, prompt)
            self.iol.print("Prompt processed.", color="bright_black", verbose_only=True)


        try:
            run = client.beta.threads.runs.create(
                thread_id=self.thread.id,
                assistant_id=self.assistant.id,
                model=self.assistant.model if self.assistant.model else "gpt-4-1106-preview",
                instructions=self.instructions
            )
            self.iol.log(f"Run created with ID: {run.id}", color="bright_black", verbose_only=True)

            stop_signal = asyncio.Event()
            asyncio.create_task(spinner(" THINKING...", stop_signal))

            # Polling mechanism to see if runStatus is completed
            run_status = client.beta.threads.runs.retrieve(thread_id=self.thread.id, run_id=run.id)
            while run_status.status != "completed":
                # self.iol.log(f"run status: {run_status.status}", color="bright_black", verbose_only=True)
                await asyncio.sleep(2)
                run_status = client.beta.threads.runs.retrieve(thread_id=self.thread.id, run_id=run.id)

                tool_outputs = []
                # Check if there is a required action
                if run_status.required_action and run_status.required_action.type == "submit_tool_outputs":
                    self.iol.log("Required action detected: submit_tool_outputs", color="bright_black", verbose_only=True)
                    for tool_call in run_status.required_action.submit_tool_outputs.tool_calls:
                        name = tool_call.function.name
                        arguments = json.loads(tool_call.function.arguments)
                        self.iol.log(f"Processing tool call: {name}", color="bright_black", verbose_only=True)
                        if "filename" in arguments and self.name == "debug_agent": 
                            filename = os.path.basename(arguments["filename"])
                            arguments["filename"] = os.path.join(scan_dir, self.target_dir, filename)
                        elif "filename" in arguments and self.name == "test_agent":
                            filename = os.path.basename(arguments["filename"])
                            arguments["filename"] = os.path.join(scan_dir, "tests", filename)

                        if hasattr(tools, name):
                            function_to_call = getattr(tools, name)
                            response = await function_to_call(**arguments)

                            tool_outputs.append({"tool_call_id": tool_call.id, "output": response})
                            if response:
                                self.iol.log(f"{response.content[0].text.value} \n", verbose_only=True)

                if tool_outputs:
                    client.beta.threads.runs.submit_tool_outputs(
                        thread_id=self.thread.id,
                        run_id=run.id,
                        tool_outputs=tool_outputs
                    )
                    self.iol.print("Tool outputs submitted.", color="bright_black", verbose_only=True)

                if run_status.status == "failed":
                    raise Exception(f"Run failed with reason: {run_status.last_error}")
                
            stop_signal.set()

            messages = client.beta.threads.messages.list(thread_id=self.thread.id)
            response = [message for message in messages if message.run_id == run.id and message.role == "assistant"][-1]

            # if response:
            #     self.iol.log(f"{response.content[0].text.value} \n", verbose_only=True)

        except TypeError:
            self.iol.log(f"TypeError: agent: {self.name}, run: {run} ", color="red")
        
        self.iol.log(f"Agent {self.name} finished on Run ID: {run.id}", color="bright_black", verbose_only=True)
        return messages
    
    def replace_annotations(self, messages: list[dict[str, str]]) -> list[dict[str, str]]:
        message = client.beta.threads.messages.retrieve(
        thread_id=self.trhead.id,
        message_id="..."
        )

        message_content = message.content[0].text
        annotations = message_content.annotations
        citations = []

        for index, annotation in enumerate(annotations):
            message_content.value = message_content.value.replace(annotation.text, f' [{index}]')
            if (file_citation := getattr(annotation, 'file_citation', None)):
                cited_file = client.files.retrieve(file_citation.file_id)
                citations.append(f'[{index}] {file_citation.quote} from {cited_file.filename}')
            elif (file_path := getattr(annotation, 'file_path', None)):
                cited_file = client.files.retrieve(file_path.file_id)
                citations.append(f'[{index}] Click <here> to download {cited_file.filename}')
                # Note: File download functionality not implemented above for brevity

        message_content.value += '\n' + '\n'.join(citations)
    