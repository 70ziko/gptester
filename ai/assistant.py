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
    
    def write_file(self, file_path: str, content: str):
        with open(file_path, 'w') as file:
            file.write(content)
            else:
                return messages

    async def next(self, messages: list[dict[str, str]]=None, prompt=None, directory: str = 'fixes'):
        if messages:
            self.messages_to_thread(messages)
            self.iol.log("Messages added to the thread.", color="bright_black", verbose_only=True)

        if prompt:
            self.fuser(self, prompt)
            self.iol.log("Prompt processed.", color="bright_black", verbose_only=True)


        try:
            run = client.beta.threads.runs.create(
                thread_id=self.thread.id,
                assistant_id=self.assistant.id,
                model=self.assistant.model if self.assistant.model else "gpt-4-1106-preview",
                instructions=self.instructions
            )
            self.iol.log(f"Run created with ID: {run.id}", color="bright_black", verbose_only=True)

            # Polling mechanism to see if runStatus is completed
            stop_signal = asyncio.Event()
            spinner_task = asyncio.create_task(spinner(" THINKING...", stop_signal))
            run_status = client.beta.threads.runs.retrieve(thread_id=self.thread.id, run_id=run.id)
            while run_status.status != "completed":
                # self.iol.log(f"run status: {run_status.status}", color="bright_black", verbose_only=True)
                await asyncio.sleep(2)  # Sleep for 2 seconds before polling again
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
                            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            arguments["filename"] = os.path.join(directory, 'GPTester', f'fixed_{timestamp}', filename)

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
                    self.iol.log("Tool outputs submitted.", color="bright_black", verbose_only=True)

                if run_status.status == "failed":
                    raise Exception(f"Run failed with reason: {run_status.last_error}")
                
            stop_signal.set()

            messages = client.beta.threads.messages.list(thread_id=self.thread.id)
            response = [message for message in messages if message.run_id == run.id and message.role == "assistant"][-1]

            # if response:
            #     self.iol.log(f"{response.content[0].text.value} \n", verbose_only=True)

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
    