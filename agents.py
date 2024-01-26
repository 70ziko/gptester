# from agent import Agent
from ai.assistant import Assistant as Agent
from vector_memory.models import Task, CodeFile
from DB import DBs, create_dbs
from utils.io import IOlog
from utils.config import Config

CFG = Config()

dbs = create_dbs()

# memory = Memory(PineconeMemory(dbs, CFG.pinecone_index, CFG.objective))
# memory = Memory(JSONFileMemory(dbs))

def execution_agent(objective: str, task: Task, IOlog: IOlog) -> str:
    """ Executes a task
        # not used
    """
    ai = Agent(role='execute task', name='execution_agent', iol = IOlog)

    sys_prompt = f"""
    You are an AI who performs one task based on the following objective: {objective}\n.
    Use the available functions to apply the changes to the workspace."""
    user = f"""Your task: {task.name}\n\nResponse:"""

    response = ai.start(system=sys_prompt, user=user)

    return response[-1]["content"]

def coding_agent(objective: str, task: Task, results: list[Task] = None, iol: IOlog = None):
    """
        # NOT USED
    """
    ai = Agent(role='create code', name='coding_agent', IOlog = IOlog)

    tasks = '\n'.join([f"{t.name}\n{t.result}" if hasattr(t, 'name') and hasattr(t, 'result') else str(t) for t in results])

    system = ai.fsystem(f"{dbs.prompts['code']}")

    user = ai.fuser(f"""The objective of the project: {objective}.\n
    Results of your team's work so far: \n{tasks}. 
    Always output the whole file with all code implemented and functional. No placeholders.
    You will code the following task needed to achieve the objective: {task.name}: {task.description}
    The file you will create is located at: {task.filename}""")

    messages = [system, user]
    iol.debug(messages)

    return ai.next(messages)[-1]["content"]


def code_modifying_agent(objective: str, file: CodeFile, task: Task, results: list[Task], iol: IOlog = None):
    ai = Agent(role='modify code', name='code_modifying_agent', iol = iol)

    tasks = '\n'.join([f"{t.name}\n{t.result}" if hasattr(t, 'name') and hasattr(t, 'result') else str(t) for t in results])

    system = ai.fsystem(f"""{dbs.prompts['modify_code']}""")
    user = ai.fuser(f"""You are tasked with modifying the {file.name} that's located at: {file.path} file to achieve the ultimate objective of your team: {objective}. 
    Results of your team's work so far: \n{tasks}. 
    The current implementation of the file containing is as follows:\n 
    {file.name}\n```\n{file.content}\n```\n
    Based on this information, modify the file to accomplish the following task: {task.name}: {task.description}. """)

    messages = [system, user]
    return ai.next(messages)[-1]["content"]


async def debug_agent(input: str, iol: IOlog = None, model: str = 'gpt-4-1106-preview', directory: str = 'fixes') -> str:
    """An agent used to debug the project
    Capabililties: 
        - Working on error messages - With the user (in the future it should be able to run the project and fix it on its own)
        - writing missing code files """


    write_file_json = {
        "name": "write_file",
        "description": "Writes content to a specified file.",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {"type": "string"},
                "content": {"type": "string"}
            },
            "required": ["filename", "content"]
        }
    }

    tools=[
        {"type": "code_interpreter"},
        {"type": "retrieval"},
        {"type": "function", "function": write_file_json},
    ]

    ai = Agent(role=f"{dbs.prompts['debug']}", name='debug_agent', iol = iol, tools=tools, model=model)
    
    user = ai.fuser(msg=f"""The project codebase:\n{input}. List all the vulnerabilities present in the codebase.
                        Then output possible solutions to fix these vulnerabilities.""")
    
    messages = [user]
    return await ai.next(messages, directory=directory)

async def test_agent(input: str, test: str, iol: IOlog = None, model: str = 'gpt-4-1106-preview', directory: str = 'tests') -> str:
    """An agent used to test the supplied project
    Capabililties: 
        - Execution of tests 
        - writing missing test files """

    write_file_json = {
        "name": "write_file",
        "description": "Writes content to a specified file.",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {"type": "string"},
                "content": {"type": "string"}
            },
            "required": ["filename", "content"]
        }
    }

    run_tests_json = {
        "name": "run_tests",
        "description": "Executes test commands for specified programming languages using subprocesses.",
        "parameters": {
            "type": "object",
            "properties": {
                "language": {
                "type": "string",
                "enum": ["cpp", "java", "python", "ruby", "php"]
                },
                "executable": {
                "type": "string",
                "description": "Path to the executable for C++ tests or additional command parameters for other languages."
                }
            },
            "required": ["language"]
        }
    }


    tools=[
        {"type": "code_interpreter"},
        {"type": "retrieval"},
        {"type": "function", "function": write_file_json},
        {"type": "function", "function": run_tests_json},
    ]

    ai = Agent(role=f"{dbs.prompts['test']}", name='test_agent', iol = iol, tools=tools, model=model)
    
    user = ai.fuser(msg=f"""The project codebase:\n{input}. User provided the following argument for tests: {test} 
                    Please run the appropriate tests for the project. If tests are not provided, please write them.
                    Save them to a file and then run them. Use provided functions to do so.""")
    
    messages = [user]
    return await ai.next(messages, directory=directory)
