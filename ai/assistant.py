import os
import asyncio
import json
import datetime
from openai import OpenAI

import tools
from utils.config import Config
from utils.io import IOlog

CFG = Config()
client = OpenAI()

class Assistant():

    
    def __init__(self, role: str, name: str = "Assistant", model: str = 'gpt-3.5-turbo-1106', iol: IOlog = None, tools = None, messages = None) -> None:
        """
        Initialize the AI object with empty lists of functions, and performance evaluations.
        """
        self.iol = iol
        self.instructions = role
        self.assistant = client.beta.assistants.create(
            name=name,
            instructions=self.instructions,
            model=model,
            # seed=dbs.prompts['seed']
            # response_format='json_object',
            tools=tools if tools else [{"type": "code_interpreter"}, {"type": "retrieval"}]    # przerzucić do argumentów
        )
        self.thread = client.beta.threads.create(messages = messages)


    # @staticmethod
    def start(self, system: str, user: str) -> list[dict[str, str]]:
        user_msg = self.fuser(user)
        self.instructions = self.fsystem(system)

        return self.next([user_msg])
    
    # @staticmethod
    def fassistant(self) -> dict[str, str]:
        client.beta.threads.messages.create(
            self.thread.id,
            role="assistant",
            content=self.instructions,
        )
    
    # @staticmethod
    def fsystem(self, msg: str) -> dict[str, str]:
        self.assistant.instructions = msg
    
    # @staticmethod
    def fuser(self, msg: str) -> dict[str, str]:
        thread_message = client.beta.threads.messages.create(
            self.thread.id,
            role="user",
            content=msg,
        )
        return thread_message
    
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

    async def next(self, messages: list[dict[str, str]]=None, prompt=None, directory: str = 'fixes'):
    def fassistant(self) -> dict[str, str]:
        client.beta.threads.messages.create(
            self.thread.id,
            role="assistant",
            content=self.instructions,
        )
        client.beta.threads.messages.create(
            self.thread.id,
            role="assistant",
            content=self.instructions,
        )

        if prompt:
            self.fuser(self, prompt)

        try:
            run = client.beta.threads.runs.create(
                thread_id=self.thread.id,
                assistant_id=self.assistant.id,
                model=self.assistant.model if self.assistant.model else "gpt-4-1106-preview",
                instructions=self.instructions
            )

            # Polling mechanism to see if runStatus is completed
            run_status = client.beta.threads.runs.retrieve(thread_id=self.thread.id, run_id=run.id)
            while run_status.status != "completed":
                await asyncio.sleep(2)  # Sleep for 2 seconds before polling again
                run_status = client.beta.threads.runs.retrieve(thread_id=self.thread.id, run_id=run.id)

                tool_outputs = []
                # Check if there is a required action
                if run_status.required_action and run_status.required_action.type == "submit_tool_outputs":
                    for tool_call in run_status.required_action.submit_tool_outputs.tool_calls:
                        name = tool_call.function.name
                        arguments = json.loads(tool_call.function.arguments)
                        if "filename" in arguments: 
                            filename = os.path.basename(arguments["filename"])
                            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            arguments["filename"] = os.path.join(directory, f'fixed_{timestamp}', filename)

                        # Check if the function exists in the tools module
                        if hasattr(tools, name):
                            function_to_call = getattr(tools, name)
                            response = await function_to_call(**arguments)

                            # Collect tool outputs
                            tool_outputs.append({"tool_call_id": tool_call.id, "output": response})


                # Submit tool outputs back
                if tool_outputs:
                    client.beta.threads.runs.submit_tool_outputs(
                        thread_id=self.thread.id,
                        run_id=run.id,
                        tool_outputs=tool_outputs
                    )
                if run_status.status == "failed":
                    raise Exception(f"Run failed with reason: {run_status.last_error}")

            # Get the last assistant message from the messages list
            messages = client.beta.threads.messages.list(thread_id=self.thread.id)
            response = [message for message in messages if message.run_id == run.id and message.role == "assistant"][-1]

            # If an assistant message is found, iol.log it
            if response:
                self.iol.log(f"{response.content[0].text.value} \n")

        except TypeError:
            self.iol.log(f"TypeError: run[-1][\"content\"]: {run[-1]['content']}")


        return messages
    
    def replace_annotations(self, messages: list[dict[str, str]]) -> list[dict[str, str]]:
        # Retrieve the message object
        message = client.beta.threads.messages.retrieve(
        thread_id=self.trhead.id,
        message_id="..."
        )

        # Extract the message content
        message_content = message.content[0].text
        annotations = message_content.annotations
        citations = []

        # Iterate over the annotations and add footnotes
        for index, annotation in enumerate(annotations):
            # Replace the text with a footnote
            message_content.value = message_content.value.replace(annotation.text, f' [{index}]')

            # Gather citations based on annotation attributes
            if (file_citation := getattr(annotation, 'file_citation', None)):
                cited_file = client.files.retrieve(file_citation.file_id)
                citations.append(f'[{index}] {file_citation.quote} from {cited_file.filename}')
            elif (file_path := getattr(annotation, 'file_path', None)):
                cited_file = client.files.retrieve(file_path.file_id)
                citations.append(f'[{index}] Click <here> to download {cited_file.filename}')
                # Note: File download functionality not implemented above for brevity

        # Add footnotes to the end of the message before displaying to user
        message_content.value += '\n' + '\n'.join(citations)
    