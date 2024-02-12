# from agent import Agent   #ChatCompletion
from ai.assistant import Assistant as Agent
from DB import create_dbs
from utils.io import IOlog
from utils.config import Config

CFG = Config()

dbs = create_dbs()

async def debug_agent(input: str, scan_dir: str, iol: IOlog = None, model: str = 'gpt-4-1106-preview', fixed_dir:str='fixed', file_to_know: str = '699.csv') -> str:
    """An agent used to analyze the project """

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
    append_to_csv = {
        "name": "append_to_csv",
        "description": "Appends a row to an existing CSV file using a semicolon as the delimiter.",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "The path to the CSV file to which the row will be appended."
                },
                "row_data": {
                    "type": "array",
                    "description": "A list of values to be formatted into a CSV row and appended to the file.",
                    "items": {
                        "type": "string"
                    }
                }
            },
            "required": ["file_path", "row_data"]
        }
    }
    tools=[
        {"type": "code_interpreter"},
        {"type": "function", "function": write_file_json},
    ]
    if CFG.output_format=='csv': tools.append({"type": "function", "function": append_to_csv})
    if CFG.retrieval: tools.append({"type": "retrieval"})

    # prompt in prompts directory - debug
    system_prompt = f"{dbs.prompts['debug-csv']}" if CFG.output_format=="csv" else f"{dbs.prompts['debug']}"
    ai = Agent(role=system_prompt, name='debug_agent', iol = iol, tools=tools, model=model, target_dir=fixed_dir, know_file=file_to_know)
    
    user = ai.fuser(msg=f"""The project codebase:\n{input}. 
List all the vulnerabilities present in the codebase, when finished write their number. 
Then output possible solutions to fix these vulnerabilities.""")
    
    messages = [user]
    return await ai.next(messages, scan_dir=scan_dir)

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
    return await ai.next(messages, scan_dir=directory)
