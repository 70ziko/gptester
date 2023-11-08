from openai import OpenAI
import asyncio
from config import Config
from utils.logger import Logger
from utils.utils import openai_call, openai_call_functions, num_tokens_from_messages, prompt_function_call

CFG = Config()


if CFG.console_mode:
    from utils.io_classes import IO_console as IO
else:
    from utils.io_classes import IO_sockets as IO

class Assistant():

    self.client = OpenAI()
    
    def __init__(self, role: str, name: str = "AI", model: str = CFG.llm_model, logger: Logger = None, io: IO = None, tools: list(dict) = None) -> None:
        """
        Initialize the AI object with empty lists of functions, and performance evaluations.
        """
        self.logger = logger
        self.io = io
        self.assistant = self.client.beta.assistants.create(
            name=name,
            description=role,
            model=model,
            tools=[{"type": "code_interpreter"}]    # przerzucić do argumentów
        )
        self.thread = self.client.beta.threads.create(messages = self.messages)


    @staticmethod
    def start(self, system: str, user: str) -> list[dict[str, str]]:
        messages = [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ]

        return self.next(messages)
    
    @staticmethod
    def fassistant(msg: str) -> dict[str, str]:
        return {"role": "assistant", "content": msg}
    
    @staticmethod
    def fsystem(msg: str) -> dict[str, str]:
        return {"role": "system", "content": msg}
    
    @staticmethod
    def fuser(msg: str) -> dict[str, str]:
        return {"role": "user", "content": msg}

    def next(self, messages: list[dict[str, str]], prompt=None):
        if prompt:
            self.client.Message.create(
                thread_id=self.thread.id,
                role="user",
                content=prompt
            )

        message_tokens = num_tokens_from_messages(messages)
        if self.logger:
            self.logger.log(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
            self.logger.log(message=f"name: {self.name}, role: {self.role}", description="AI info")
            self.logger.log(message=messages[-1]['content'], description="User messages to ai")
            self.logger.log(message=f'Input tokens: {message_tokens}', description="Number of input tokens in messages")

        max_tokens = int(self.token_limit - message_tokens*1.1)

        try:
            run = self.client.beta.threads.runs.create(
                thread_id=self.thread.id,
                assistant_id=self.assistant.id,
                model=self.model if self.model else "gpt-4-1106-preview",
                instructions="additional instructions",
                tools=[{"type": "code_interpreter"}, {"type": "retrieval"}]
            )

            # Polling mechanism to see if runStatus is completed
            run_status = self.client.beta.runs.retrieve(thread_id=self.thread.id, run_id=run.id)
            while run_status.status != "completed":
                asyncio.sleep(2)  # Sleep for 2 seconds before polling again
                run_status = self.client.Run.retrieve(thread_id=self.thread.id, run_id=run.id)

            # Get the last assistant message from the messages list
            messages = self.client.Message.list(thread_id=self.thread.id)
            last_message_for_run = [message for message in messages if message.run_id == run.id and message.role == "assistant"][-1]

            # If an assistant message is found, print it
            if last_message_for_run:
                print(f"{last_message_for_run.content[0].text.value} \n")

        except TypeError:
            print(f"TypeError: run[-1][\"content\"]: {run[-1]['content']}")

        if self.logger:
            self.logger.log(message=response[-1]['content'], description="AI response to user")
            response_tokens = num_tokens_from_messages(response)
            output_tokens = response_tokens - message_tokens
            self.io.output_tokens_used({"input_tokens": message_tokens, "output_tokens": output_tokens})
            self.logger.log(message=f'Number of tokens in conversation: {response_tokens}, in gpt response: {output_tokens}', description="Number of tokens in conversation")
            self.logger.log("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
        return run.messages
    
    def replace_annotations(self, messages: list[dict[str, str]]) -> list[dict[str, str]]:
        # Retrieve the message object
        message = self.client.beta.threads.messages.retrieve(
        thread_id="...",
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
                cited_file = self.client.files.retrieve(file_citation.file_id)
                citations.append(f'[{index}] {file_citation.quote} from {cited_file.filename}')
            elif (file_path := getattr(annotation, 'file_path', None)):
                cited_file = self.client.files.retrieve(file_path.file_id)
                citations.append(f'[{index}] Click <here> to download {cited_file.filename}')
                # Note: File download functionality not implemented above for brevity

        # Add footnotes to the end of the message before displaying to user
        message_content.value += '\n' + '\n'.join(citations)
    
    def ask(self, messages: list[dict[str, str]]) -> list[dict[str, str]]:
        "Funkcja służąca do wywołania zapytania o feedback i zwrócenia odpowiedzi, działa na tej samej liście wiadomości a nie różnej jak w przypadku feedback_agent"

        def parse_feedback_input(user_input: str):
            '''Parse the user input for feedback and accept count'''
            matches = re.search(r"-([0-9]+)", user_input)
            if matches:
                CFG.continuous_limit = int(matches.group(1))
                user_input = user_input.replace(matches.group(0), '').strip()
            return user_input
        
        while True:
            user_input = self.io.input(
                '\nDo you accept this solution? (y/n) Or enter text as feedback\n')
            feedback_from_user = parse_feedback_input(user_input)
            if feedback_from_user:
                break

        if feedback_from_user == 'y':
            return messages

        if feedback_from_user == 'n':
            # Should we actually exit here?
            self.io.output('Exiting...')
            return

        messages += self.fuser(feedback_from_user)
        messages += self.fassistant(self.next(messages))
        return messages


    def add_function(self, function_name: str, function_description: str, parameters: dict) -> None:
        """
        Add a function to the functions list with a label, name, and parameters.

        Args:
            function_name (str): The name of the function.
            function_description (str): The label of the function.
            parameters (dict): A dictionary containing the function's parameters.
        """
        function = {
            "name": function_name,
            "description": function_description,
            "parameters": {
                "type": "object",
                "properties": parameters,
                "required": list(parameters.keys()),
            },
        }

        # function_json = json.loads(json.dumps(function))
        self.functions.append(function)

    def display_functions(self) -> str:
        """
        Returns a string representation of the functions list.
        """
        function_strings = []
        for function in self.functions:
            function_name = function["name"]
            function_description = function["description"]
            parameters = function["parameters"]["properties"]
            parameter_strings = []
            for parameter_name, parameter_type in parameters.items():
                parameter_strings.append(f"{parameter_name} ({parameter_type})")
            parameter_string = ", ".join(parameter_strings)
            function_string = f"{function_name}: {function_description} ({parameter_string})"
            function_strings.append(function_string)
        return "\n".join(function_strings)