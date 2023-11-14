from agent import Agent
from vector_memory.models import Task, CodeFile
from vector_memory.pinecone_memory import PineconeMemory
from vector_memory.json_file_memory import JSONFileMemory
from vector_memory.memory import Memory
from utils.functions_setter import set_functions
from utils.chat_to_files import to_files
from utils.traverser import create_tree_with_contents
from DB import DBs, create_dbs
from utils.IOlog import IOlog
from config import Config
from typing import List
import subprocess
import re
import sys


CFG = Config()

if CFG.console_mode:
    from utils.io_classes import IO_console as IO
else:
    from utils.io_classes import IO_sockets as IO

dbs = create_dbs(CFG.sid)

# memory = Memory(PineconeMemory(dbs, CFG.pinecone_index, CFG.objective))
memory = Memory(JSONFileMemory(dbs))

def html_modyfing_agent(html, message, io: IO) -> str:
    output_stream = io.output_stream
    if not CFG.console_mode:
        io.output_stream = io.output_modified_html_stream
    ai = Agent(role='modify html', name='html_modyfing_agent', IOlog = None, io = io)
    
    sys_prompt = ai.fsystem(f"""You are an AI who modifies html files based on user's instruction.\n.""")
    user_prompt = ai.fuser(f"""Modify the following html file based on the user's instructions.
    Respond with JUST the modified html file. Do not include the instructions, nor reasoning, nor anything else.
    Don't add a dot at the end of the file. Don't add a newline at the end of the file.
    HTML file: {html}.\n User's instructions: {message}""")
    
    messages = [sys_prompt, user_prompt]
    response = ai.next(messages)
    
    io.output_stream = output_stream
    
    return response[-1]["content"]

def execution_agent(objective: str, task: Task, IOlog: IOlog, io: IO) -> str:
    """ Executes a task"""
    ai = Agent(role='execute task', name='execution_agent', IOlog = IOlog, io = io)
    set_functions(ai, [])

    sys_prompt = f"""
    You are an AI who performs one task based on the following objective: {objective}\n.
    Use the available functions to apply the changes to the workspace."""
    user = f"""Your task: {task.name}\n\nResponse:"""

    response = ai.start(system=sys_prompt, user=user)

    return response[-1]["content"]

def clarify_agent(objective: str = CFG.objective, dbs: DBs = dbs, IOlog: IOlog = None, io: IO = None):
    '''Ask the user if they want to clarify anything and save the results to the workspace'''
    ai = Agent(role='clarify project details with user', name='clarify_agent', IOlog = IOlog, io = io)

    messages = [ai.fsystem(dbs.prompts['qa'])]

    user_input = objective
    while True:
        messages = ai.next(messages, user_input)

        if messages[-1]["content"].strip() == "Nothing more to clarify.":
            break

        if messages[-1]["content"].strip().lower().startswith("no"):
            io.output("Nothing more to clarify.")
            break

        input_prompt = '\n(answer in text, or "c" to let contailigence make its own assumptions)\n'
        user_input = io.input(input_prompt)

        if not user_input or user_input == "c":
            io.output("(letting contailigence make its own assumptions)\n")
            messages = ai.next(
                messages,
                "Make your own assumptions and state them explicitly before starting, summarize clarified areas",
            )
            return messages

        user_input += (
            "\n\n"
            "Is anything else unclear? If yes, only answer in the form:\n"
            "{remaining unclear areas} remaining questions.\n"
            "{Next question}\n"
            'If everything is sufficiently clear, only answer "Nothing more to clarify.".'
        )

    io.output("\n********CLARIFY SUMMARY*********\n", IO.colors.BLUE)
    user = "Summarize everything that was clarified and make your own assumptions explicitly before starting."
    messages = ai.next(messages, user)
    return messages


def propose_structure_agent(objective: str, specification: str, project_structure: str, IOlog: IOlog = None, io: IO = None) -> str:
    output_stream = io.output_stream
    if not CFG.console_mode:
        io.output_stream = io.output_directory_content_stream

    ai = Agent(role='propose suitable project structure', name='structure_agent', IOlog = IOlog, io = io)


    sys_prompt = ai.fsystem(f"""{dbs.prompts['structure']}""")
    # Here are the results of the previous tasks performed by your team: \n{tasks}          (Old memory managment)
    user_prompt = ai.fuser(f""" 
    The objective of the project is: {objective}
    Here is the specification of the project: \n{specification}

    These are the current contents of the current working directory in JSON format: \n{project_structure}

    With the current working directory as the project's directory, carefully select and move the necessary    
    files into the correct directories to construct the ideal project structure in line with the team's
    objective. Create the structure trying to minimize the number of files to just those essential and necessary for the project to function.

    Follow the best programming practices to maintain consistency in file organization and function naming.   
    Ensure that the new structure includes all the required files (code files, html, css, etc.) stored in the 
    appropriate locations for the successful operation of the project. Remember, filenames are case sensitive.

    Provide the desired structure in JSON format.    
    """)

    messages = [sys_prompt, user_prompt]

    response = ai.next(messages)
    
    io.output_stream = output_stream

    return response[-1]["content"]

def implement_structure_agent(seeds_contents: str, project_structure: str, IOlog: IOlog = None, io: IO = None) -> str:
    ai = Agent(role='implement the project structure wwth bash commands', name='structure_agent', IOlog = IOlog, io = io)
    
    sys_prompt = ai.fsystem("You are a super smart system administrator. Your task is to create a set of bash commands, that will create a project structure based on a given JSON file. \
                            You will be given the contents of the current working directory and the target project structure in JSON format.  \
                            The bash commands you write should create the target project structure in the current working directory. \
                            Some files in the current working directory can be useful for our project, so make sure to move them instead of creating. \
                            ")
    
    user_prompt = ai.fuser(f"""Based on the json containing the project structure and current contents of the directory, create a series of bash commands that would create this 
    structure. Each command should be written on a new line.     

    When writing these commands, make sure to:

    • Preserve the original files as much as possible, preferably using the 'mv' command. 
    • Write one command per line.
    • Remove all unneeded files and directories using the 'rm' command, retaining only files necessary for project functionality. 
    • Remove all the seed directories that are not part of the project.
    • Use the current working directory as the directory for the project. 
    • Rely on relative paths rather than using a dot to reference the current working directory.        
    • Avoid the 'cd' command, resorting to paths relative to the workspace directory as much as possible.
                           
    The current contents of the current working directory in JSON format: \n{seeds_contents} 
    
    The project structure is as follows: \n{project_structure}""")
    
    messages = [sys_prompt, user_prompt]
    response = ai.next(messages)
    return response[-1]["content"]

def technical_plan_agent(objective: str, specification: str, structure: str, IOlog: IOlog = None, io: IO = None) -> str:
    ai = Agent(role='create technical plan', name='technical_plan_agent', IOlog = IOlog, io = io)

    sys_prompt = ai.fsystem(dbs.prompts['technical_plan'])

    user_prompt = ai.fuser(f"""We are creating a program following the specification: \n{specification}
    The objective of the program is: {objective}
    The current project structure is as follows:\n{structure}
    Based on that information create a technical plan for the project.""")

    messages = [sys_prompt, user_prompt]
    return ai.next(messages)[-1]["content"]

def dependency_agent(IOlog: IOlog = None, io: IO = None, dbs=dbs) -> str:
    ai = Agent(role='create dependency map', name='dependency_agent', IOlog = IOlog, io = io, model='gpt-4')

    specification = dbs.workspace['specification.md']
    technical = dbs.workspace['technical_plan.md']

    tasks = f'Specification of the project: \n{specification} + \nTechnical part of the specification: \n{technical}'

    sys_prompt = ai.fsystem(dbs.prompts['dependency'])

    user_prompt = ai.fuser(f"""These are the previous results of your team's tasks: \n{tasks}
Based on that information return a file dependency map in a json format""")
    
    messages = [sys_prompt, user_prompt]
    io.debug(messages)
    return ai.next(messages)[-1]["content"]


def feedback_agent(message: list[dict[str, str]], user_feedback: str, IOlog: IOlog = None, io: IO = None):
    ai = Agent(role='acknowledge feedback', name='feedback_agent', IOlog = IOlog, io = io)

    system_message = ai.fsystem(f"""Your task is to read the user feedback in the context of your previous message and based on them
    modify the message to account for the feedback.""")

    assistant_message = ai.fassistant(message)

    user_message = ai.fuser(f"""Use the following user feedback to your message and return a new version of the message the feedback
    concerns based on the feedback: {user_feedback}""")

    messages = [system_message, assistant_message, user_message]
    response = ai.next(messages)

    return response[-1]["content"]

def plan_tasks_agent(structure, objective: str, IOlog: IOlog = None, io: IO = None, dbs = dbs):
    """ Writes the initial task list based on clarified information, specification, project structure, and objective"""
    
    # te output_stream'y można by jako parametr (obiektu/funkcji) przekazywać, a nie powtarzać kod...
    output_stream = io.output_stream
    if not CFG.console_mode:
        io.output_stream = io.output_task_list_stream

    ai = Agent(role='create task list', name='task_agent', IOlog = IOlog, io = io, model='gpt-4')

    query = objective

    # # będą to 4 pierwsze ponieważ tylko 4 istnieją
    # similiar_results = memory.get_relevant_tasks(query, 4)
    tasks = ''
    # for t in similiar_results:
    #     tasks += 'Task: \n' + str(t.name) + '\nResult:\n' + str(t.result) + '\n'
    
    tasks += f'Project structure: \n{structure}\n'

    specification = dbs.workspace['specification.md']
    technical_plan = dbs.workspace['technical_plan.md']
    tasks += f'Specification: \n{specification}\nTechnical plan: \n{technical_plan}'

    sys_prompt = ai.fsystem(f"""{dbs.prompts['plan']}""")

    user_prompt = ai.fuser(f"""Previous relevant tasks have following results: \n{tasks}
Based on the information above, create a task list that will accomplish the objective of your team: {objective}.
Always include the filename that is influenced by the task. Each task should be a dictionary with the following keys: task_id, name, description, filename. 
A description should contain a description of the task, it's purpose and what it should accomplish, make it understandable for non-technical users.
Return a complete task list that will accomplish the objective of your team in the following format: """ + 
'[{"task_id": 1, "name": "Name of the task", "description":"Detailed description of why the task has to be completed and what is accomplishes, so the user knows what is happening.", "filename": "full/path/to/file"}, {"task_id": 2, "name": "Detailed description of the second task", "description":"Detailed description of why the task has to be completed and what is accomplishes, so the user knows what is happening.", "filename": "full/path/to/file"}]'
+ 'Make sure you finish the task list with }]')
      
    messages = [sys_prompt, user_prompt]
    io.debug(messages)

    response = ai.next(messages)[-1]["content"]
    
    io.output_stream = output_stream
    
    if CFG.continuous_mode:
        return response

    if CFG.continuous_limit > 0:
        CFG.continuous_limit -= 1
        return response

    return response


def specification_agent(objective: str, IOlog: IOlog = None, io: IO = None, add_messages: list[dict[str, str]] = None):
    """ Writes the initial project specification based on clarified information, project structure, and objective"""
    output_stream = io.output_stream
    if not CFG.console_mode:
        io.output_stream = io.output_specification_stream

    ai = Agent(role='specify the project details', name='specification_agent', IOlog = IOlog, io = io)


    sys_prompt = ai.fsystem(f"""{dbs.prompts['specification']}""")

    user_prompt = ai.fuser(f"""Create project specification for the following objective: {objective}.
This specification will be used later as the basis for the implementation. Return the specification using github markdown format.
""")

    messages = [sys_prompt, user_prompt]
    if add_messages:
        messages += add_messages

    io.debug(f'Messages: \n{messages}\n\n')

    response = ai.next(messages)[-1]["content"]

    io.output_stream = output_stream
    return response


def coding_agent(objective: str, task: Task, results: list[Task] = None, IOlog: IOlog = None, io: IO = None):
    ai = Agent(role='create code', name='coding_agent', IOlog = IOlog, io = io)

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


def code_modifying_agent(objective: str, file: CodeFile, task: Task, results: list[Task], IOlog: IOlog = None, io: IO = None):
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


def setup_agent(directory_contents: str, dbs: DBs, IOlog: IOlog = None, io: IO = None, add_messages: list[dict[str, str]] = None):
    ai = Agent(
        role='finish up the project and give instructions on how to set it up', name='setup_agent', IOlog=IOlog, io=io)

    specification = dbs.workspace['specification.md']
    technical = dbs.workspace['technical_plan.md']

    structure = f'The current project contents are as follows:\n{directory_contents}.'

    system = ai.fsystem(f"""{dbs.prompts['setup']}""")
    user = ai.fuser(f"""The specification of the program is as follows: \n{specification} + \nTechnical part of the specification: \n{technical}
    You will write the docker-compose file for this project. {structure}
    Output needs to have both docker-compose.yml and Dockerfile. When writing those files remember about the correct root directory. 
    Docker will start the project from the current working directory, so make sure that the cwd is the one that contains the docker-compose.yml file and there are correct paths for source files in the Dockerfile. 
    Remember that you have to setup the container with the right permissions for the server to be able to read the contents.
    Then you will output all the commands and steps needed to set up the project. 
    At the end write bash commands that will move files that are in the wrong location to the right one.""")
    
    messages = [system, user]
    if add_messages:
        messages += add_messages  # Include any additional messages
    
    io.debug(messages)
    response = ai.next(messages)[-1]["content"]

    if CFG.continuous_mode:
        return response

    if CFG.continuous_limit > 0:
        CFG.continuous_limit -= 1
        return response

    feedback_response = feedback_agent(response, IOlog=IOlog, io=io)
    return feedback_response


def execute_entrypoint(dbs: DBs, IOlog: IOlog,  io: IO) -> List[dict]:
    command = dbs.workspace["run.sh"]

    io.output("Do you want to execute this code?")
    
    io.output(command)
    
    io.output('If yes, press enter. Otherwise, type "no"')
    
    if input() not in ["", "y", "yes"]:
        io.output("Ok, not executing the code.")
        return []
    io.output("Executing the code...")
    
    io.output(
            "Note: If it does not work as expected, consider running the code"
            + " in another way than above.", io.colors.RED
        )
    
    io.output("You can press ctrl+c *once* to stop the execution.")
    

    p = subprocess.run("bash run.sh", shell=True, cwd=dbs.workspace.path, capture_output=True, text=True)  
    try:
        p.wait()
    except KeyboardInterrupt:
        io.output("Stopping execution.\n")
        io.output("Execution stopped.\n")
        p.kill()
        return []

    return p.stdout or p.stderr  


def entrypoint_agent(workspace_full_path: str, dbs: DBs, IOlog: IOlog, io: IO) -> List[dict]:
    ai = Agent(role="Generate entrypoint", name='entrypoint_agent', IOlog = IOlog, io = io)

    messages = ai.start(
        system=(
            "You will get information about a codebase that is currently on disk in "
            "the current folder.\n"
            "From this you will answer with code blocks that includes all the necessary "
            "unix terminal commands to "
            "a) install dependencies "
            "b) run all necessary parts of the codebase (in parallel if necessary).\n"
            "Do not install globally. Do not use sudo.\n"
            "Do not explain the code, just give the commands.\n"
            "Do not use placeholders, use example values (like . for a folder argument) "
            "if necessary.\n"
        ),
        user="Information about the codebase:\n\n" + str(create_tree_with_contents(workspace_full_path)),
    )


    regex = r"```\S*\n(.+?)```"
    matches = re.finditer(regex, messages[-1].content.strip(), re.DOTALL)
    dbs.workspace["run.sh"] = "\n".join(match.group(1) for match in matches)
    return messages

def debugging_agent(output: str, IOlog: IOlog = None, io: IO = None) -> str:
    """An agent used to debug the project
    Capabililties: 
        - Working on error messages - With the user (in the future it should be able to run the project and fix it on its own)
        - writing missing code files """

    ai = Agent(role="Debug the project with the user", name='debug_agent', IOlog = IOlog, io = io)

    system = ai.fsystem(f"{dbs.prompts['debug']}")


    project = create_tree_with_contents(workspace_full_path)

    user = ai.fuser(f"""The project codebase:\n{project}. The output of running the program with run.sh: {output} \n
Please fix the codebase so that it runs correctly. You can use bash commands to move files around, create new files, delete files, etc.""")
    
    messages = [system, user]

    while True:
        messages = ai.next(messages)
        io.output(messages[-1]['content'])

        if messages[-1]['content'] == "No more errors.":
            return messages[-1]['content']
        
        confirm = io.input("Do you want to implement those changes? (y/n or enter text as feedback)")
        if confirm in ["n", "no"]:
            return messages[-1]['content']
        elif confirm in ['', "y", "yes"]:
            to_files(messages[-1]['content'], dbs.workspace)

        result = execute_entrypoint(dbs, io)

        user_input = io.input("Do you want to continue debugging? (y/n or enter text as feedback)")
        if user_input in ["n", "no"]:
            break
        elif user_input in ['', "y", "yes"]:
            continue
        else:
            result += user_input

        messages.append(ai.fuser(result))

    return messages[-1]['content']


def clarify_specification_agent(specification: str, IOlog: IOlog = None, io: IO = None):
    output_stream = io.output_stream
    if not CFG.console_mode:
        io.output_stream = io.output_questions_from_ai_stream
    ai = Agent(role='clarify specification with user', name='clarify_specification_agent', IOlog = IOlog, io = io)
    
    system_message = ai.fsystem(f"""You are a part of an AI, that creates code from project specifications. Your jobs is to
    look at the specification document and ask for more information that you need to create the project, 
    and to clarify the specification with the user if you think something is unclear or contradictory.""")
    
    user_message = ai.fuser(f"""Look at the following project specification and ask for more information or clarification
    that is necesseary to create the project. Start each question with its number, and end it with a % sign, like so
    1. here goes the first question%
    2. here goes the second question%
    etc.
    Try avoiding questions you would ask a developer, because the users won't understand them. \
    Specification: {specification}""")
    
    messages = [system_message, user_message]
    response = ai.next(messages)
    response = response[-1]["content"]
    
    io.output_stream = output_stream
    io.output_questions_from_ai_stream_done()
    # feedback_response = ask_feedback(response, IOlog=IOlog, io=io)
    
    return response


def define_objective_agent(specification: str, IOlog: IOlog = None, io: IO = None):
    output_stream = io.output_stream
    if not CFG.console_mode:
        io.output_stream = io.output_objective_stream
    ai = Agent(role='define objective from specification', name='define_objective_agent', IOlog = IOlog, io = io)
    
    system_message = ai.fsystem(f"""You are a part of an AI, that creates code from project specifications. Your jobs is to
    read a specification provided by user, and define the objective of the project from it.""")

    user_message = ai.fuser(f"""Use the user-provided specification to define the objective of the project.\
    Specification: {specification}""")

    messages = [system_message, user_message]
    response = ai.next(messages)

    io.output_stream = output_stream
    return response[-1]["content"]

def ask_feedback(message: list[dict[str, str]], IOlog: IOlog = None, io: IO = None):
    '''Ask the user for feedback on the AI's response'''

    while True:
        user_input = io.input(
            '\nDo you accept this solution? (y/n) Or enter text as feedback\n')
        feedback_from_user = parse_feedback_input(user_input)
        if feedback_from_user:
            break

    if feedback_from_user == 'y':
        return message

    if feedback_from_user == 'n':
        # Should we actually exit here?
        sys.exit()

    feedback_from_agent = feedback_agent(message, feedback_from_user, IOlog, io)

    return ask_feedback(feedback_from_agent, IOlog, io)


def parse_feedback_input(user_input: str):
    '''Parse the user input for feedback and accept count'''
    matches = re.search(r"-([0-9]+)", user_input)
    if matches:
        CFG.continuous_limit = int(matches.group(1))
        user_input = user_input.replace(matches.group(0), '').strip()
    return user_input