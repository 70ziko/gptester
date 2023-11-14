from openai import OpenAI
import asyncio
from config import Config
from utils.io import IOlog

CFG = Config()
client = OpenAI()

class Assistant():

    
    def __init__(self, role: str, name: str = "Assistant", model: str = CFG.llm_model, IOlog: IOlog = None, tools = None, messages = None) -> None:
        """
        Initialize the AI object with empty lists of functions, and performance evaluations.
        """
        self.IOlog = IOlog
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


    @staticmethod
    def start(self, system: str, user: str) -> list[dict[str, str]]:
        user_msg = self.fuser(user)
        self.instructions = self.fsystem(system)

        return self.next([user_msg])
    
    @staticmethod
    def fassistant(self, msg: str) -> dict[str, str]:
        thread_message = client.beta.threads.messages.create(
            self.thread.id,
            role="assistant",
            content=msg,
            )
        return thread_message
    
    @staticmethod
    def fsystem(self, msg: str) -> dict[str, str]:
        self.assistant.instructions = msg
    
    @staticmethod
    def fuser(self, msg: str) -> dict[str, str]:
        thread_message = client.beta.threads.messages.create(
            self.thread.id,
            role="user",
            content=msg,
        )
        return thread_message
    
    def messages_to_thread(self, messages: list[dict[str, str]]):
        for message in messages:
            if message['role'] == 'user':
                self.fuser(message)
            elif message['role'] == 'assistant':
                self.fassistant(message)
            elif message['role'] == 'system':
                self.fsystem(message)

    def next(self, messages: list[dict[str, str]]=None, prompt=None):
        if messages:
            self.messages_to_thread(messages)

        if prompt:
            self.fuser(self, prompt)

        try:
            run = client.beta.threads.runs.create(
                thread_id=self.thread.id,
                assistant_id=self.assistant.id,
                model=self.assistant.model if self.assistant.model else "gpt-4-1106-preview",
                instructions="additional instructions",
                tools=[{"type": "code_interpreter"}, {"type": "retrieval"}]
            )

            # Polling mechanism to see if runStatus is completed
            run_status = client.beta.threads.runs.retrieve(thread_id=self.thread.id, run_id=run.id)
            while run_status.status != "completed":
                asyncio.sleep(2)  # Sleep for 2 seconds before polling again
                run_status = client.beta.threads.runs.retrieve(thread_id=self.thread.id, run_id=run.id)

            # Get the last assistant message from the messages list
            messages = client.beta.threads.messages.list(thread_id=self.thread.id)
            response = [message for message in messages if message.run_id == run.id and message.role == "assistant"][-1]

            # If an assistant message is found, print it
            if response:
                print(f"{response.content[0].text.value} \n")

        except TypeError:
            print(f"TypeError: run[-1][\"content\"]: {run[-1]['content']}")

        # if self.IOlog:
        #     self.IOlog.log(message=response[-1]['content'], description="AI response to user")
            # response_tokens = num_tokens_from_messages(response)
            # output_tokens = response_tokens - message_tokens
            # self.io.output_tokens_used({"input_tokens": message_tokens, "output_tokens": output_tokens})
            # self.IOlog.log(message=f'Number of tokens in conversation: {response_tokens}, in gpt response: {output_tokens}', description="Number of tokens in conversation")
            # self.IOlog.log("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")

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
    