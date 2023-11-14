from agents.assistant import Assistant
from config import Config
from utils.logger import Logger
import asyncio
from utils.io_classes import IO_console
from init import create_dbs

# Define the main function to handle the chat
async def main():
    # Initialize the logger
    logger = Logger()
    dbs = create_dbs('chat-test-assistant')

    # Initialize the Assistant with the console IO
    # assistant = Assistant(name="Math Tutor", role="You will help the user solve any math problem, explain it in detail and return the correct value using code interpreter",
    #                       model="gpt-4-1106-preview", logger=logger, io=IO_console())

    assistant = Assistant(name="Docker filer", role=dbs.prompts['setup'],
                          model="gpt-4-1106-preview", logger=logger)

    # Greet the user
    print("Welcome to the AI assistant. Type 'quit' to exit.")

    # Main chat loop
    while True:
        # Get input from the user
        user_input = input("You: ")
        if user_input.lower() == 'quit':
            break

        # Process the input using the Assistant
        # messages = assistant.start(system="Your system message here", user=user_input)
        messages = assistant.next(prompt=user_input)

# Entry point of the script
if __name__ == "__main__":
    asyncio.run(main())