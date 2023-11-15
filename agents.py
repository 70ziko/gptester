# from agent import Agent
from ai.assistant import Assistant as Agent
from vector_memory.models import Task, CodeFile
from vector_memory.json_file_memory import JSONFileMemory
from vector_memory.memory import Memory
# from utils.chat_to_files import to_files
from DB import DBs, create_dbs
from utils.io import IOlog
from config import Config

CFG = Config()

dbs = create_dbs()

# memory = Memory(PineconeMemory(dbs, CFG.pinecone_index, CFG.objective))
memory = Memory(JSONFileMemory(dbs))

def execution_agent(objective: str, task: Task, IOlog: IOlog) -> str:
    """ Executes a task"""
    ai = Agent(role='execute task', name='execution_agent', IOlog = IOlog, io = io)

    sys_prompt = f"""
    You are an AI who performs one task based on the following objective: {objective}\n.
    Use the available functions to apply the changes to the workspace."""
    user = f"""Your task: {task.name}\n\nResponse:"""

    response = ai.start(system=sys_prompt, user=user)

    return response[-1]["content"]

def coding_agent(objective: str, task: Task, results: list[Task] = None, IOlog: IOlog = None):
    ai = Agent(role='create code', name='coding_agent', IOlog = IOlog)

    tasks = '\n'.join([f"{t.name}\n{t.result}" if hasattr(t, 'name') and hasattr(t, 'result') else str(t) for t in results])

    system = ai.fsystem(f"{dbs.prompts['code']}")

    user = ai.fuser(f"""The objective of the project: {objective}.\n
    Results of your team's work so far: \n{tasks}. 
    Always output the whole file with all code implemented and functional. No placeholders.
    You will code the following task needed to achieve the objective: {task.name}: {task.description}
    The file you will create is located at: {task.filename}""")

    messages = [system, user]
    io.debug(messages)

    return ai.next(messages)[-1]["content"]


def code_modifying_agent(objective: str, file: CodeFile, task: Task, results: list[Task], IOlog: IOlog = None):
    ai = Agent(role='modify code', name='code_modifying_agent', IOlog = IOlog, io = io)

    tasks = '\n'.join([f"{t.name}\n{t.result}" if hasattr(t, 'name') and hasattr(t, 'result') else str(t) for t in results])

    system = ai.fsystem(f"""{dbs.prompts['modify_code']}""")
    user = ai.fuser(f"""You are tasked with modifying the {file.name} that's located at: {file.path} file to achieve the ultimate objective of your team: {objective}. 
    Results of your team's work so far: \n{tasks}. 
    The current implementation of the file containing is as follows:\n 
    {file.name}\n```\n{file.content}\n```\n
    Based on this information, modify the file to accomplish the following task: {task.name}: {task.description}. """)

    messages = [system, user]
    return ai.next(messages)[-1]["content"]


async def debug_agent(input: str, iol: IOlog = None, model: str = 'gpt-4-1106-preview') -> str:
    """An agent used to debug the project
    Capabililties: 
        - Working on error messages - With the user (in the future it should be able to run the project and fix it on its own)
        - writing missing code files """

    ai = Agent(role=f"{dbs.prompts['debug']}", name='debug_agent', iol = iol)

    # system = ai.fsystem(f"{dbs.prompts['debug']}")

    # The output of running the program with run.sh: {output} \n
    user = ai.fuser(msg=f"""The project codebase:\n{input}. Please list all the vulnerabilities present in the codebase.
                    Then output possible solutions to fix these vulnerabilities.""")
    
    messages = [user]
    return await ai.next(messages)

    # while True:
    #     messages = ai.next(messages)
    #     io.output(messages[-1]['content'])

    #     if messages[-1]['content'] == "No more errors.":
    #         return messages[-1]['content']
        
    #     confirm = io.input("Do you want to implement those changes? (y/n or enter text as feedback)")
    #     if confirm in ["n", "no"]:
    #         return messages[-1]['content']
    #     elif confirm in ['', "y", "yes"]:
    #         to_files(messages[-1]['content'], dbs.workspace)

    #     result = execute_entrypoint(dbs, io)

    #     user_input = io.input("Do you want to continue debugging? (y/n or enter text as feedback)")
    #     if user_input in ["n", "no"]:
    #         break
    #     elif user_input in ['', "y", "yes"]:
    #         continue
    #     else:
    #         result += user_input

    #     messages.append(ai.fuser(result))

    # return messages[-1]['content']
