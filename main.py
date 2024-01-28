#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import asyncio
import argparse
import datetime

from utils.io import IOlog
from utils.traverser import walk_directory, split_content
from utils.utils import num_tokens_from_string
from utils.git_pytcher import generate_patch
from utils.config import Config

CFG = Config()

banner = f"""
                  ___  ___  _____           _             
                 / __|| _ \|_   _| ___  ___| |_  ___  _ _ 
                | (_ ||  _/  | |  / -_)(_-/|  _|/ -_)| '_|
                 \___||_|    |_|  \___|/__/ \__|\___||_|  

           The static code analysis agent, version: {CFG.version}\n\n"""

# obsługa programu poprzez argumenty przekazywane w konsoli
parser = argparse.ArgumentParser(description=banner, formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('directory', type=str, help='Path to the directory to scan')
parser.add_argument('-v', '--verbose', help='Print out all the outputs and steps taken', action='store_true')
parser.add_argument('-m', '--model', help='Choose the LLM model for code analysis, default: "gpt-4-1106-preview"', default="gpt-4-1106-preview")
parser.add_argument('-r', '--retrieval', help='Turn on Retrieval Augmented Generation for code analysis, default: False', action='store_true', default=False)
parser.add_argument('-f', '--file_to_know', help='Point to a file to be uploaded to the knowledge base for retrieval, default: "699.csv" - CVE database in csv \n!CURRENT VERSION SUPPORTS ONE FILE!', default="699.csv")
parser.add_argument('-o', '--output', help='Output the results to a file, default: "raports/{name_of_parent_folder}_{timestamp}_raport.md"')
parser.add_argument('-t', '--tests', help='Provide a path to functional tests to run on the project, if not supplied or found in the workspace directory, the tests will be generated or skipped')
parser.add_argument('-c', '--codeql', help='Use codeql to enhance the scan, REQUIRED to install CodeQL-CLI console tool', action='store_true', default=False)
parser.add_argument('--command', help='Provide a build command to run the project for codeql, if no cmake or similiar file present in the project root directory, default: "make"', default="make")
parser.add_argument('--language', help='Provide a programming language of the project for codeql, default: "cpp"', default="cpp")


# Inicjalizacja
args = parser.parse_args()

project_name = os.path.basename(args.directory.rstrip('/'))
iol = IOlog(args.directory, verbose=args.verbose, name=project_name)

# Import the agents after iol is ready and singletonned
import agents


CFG.set_retrieval(args.retrieval)

async def run_agents(args, iol, chunks, fixed_dir):
    tasks = []

    # If tests are provided, add the test agent task
    if args.tests:
        iol.log(f"Functional tests provided, I will now run them", color="red")
        test_task = asyncio.create_task(
            retry_task(agents.test_agent, chunks[0], args.tests, iol, args.model, args.directory)
        )   # chunks[0] - only the first chunk is used for tests, this needs changing and rethinking
        tasks.append(test_task)

    # Add debug agent tasks for each chunk using retry mechanism
    for chunk in chunks:
        task = asyncio.create_task(
            retry_task(agents.debug_agent, chunk, args.directory, iol, args.model, fixed_dir, args.file_to_know)
        )
        tasks.append(task)

    # Wait for all tasks to complete
    for completed_task in asyncio.as_completed(tasks):
        output = await completed_task

        for message in output:   
            if message.role == "assistant":
                for content_item in message.content:
                    text = content_item.text.value
                    iol.log("\n\n" + text + '\n', color="white")

# The retry_task function remains the same as in the previous example

async def retry_task(coroutine_func, *args, max_retries=CFG.restart_limit, delay=2):    # CFG.restart_limit = 3 in config.py
    """
    Retries a coroutine function if it fails.
    :param coroutine_func: The coroutine function to execute.
    :param args: Arguments to pass to the coroutine function.
    :param max_retries: Maximum number of retries.
    :param delay: Delay between retries in seconds.
    """
    for attempt in range(max_retries):
        try:
            return await coroutine_func(*args)
        except Exception as e:
            if attempt < max_retries - 1:
                iol.log(f"Task failed with {e}, retrying... (Attempt {attempt + 1}/{max_retries})", color="yellow")
                await asyncio.sleep(delay)
            else:
                iol.log(f"Task failed after {max_retries} attempts", color="red")
                raise



async def main():
    print(banner)

    iol.log(f"Beginning scan for {args.directory}", color="pink")
    dir_content = walk_directory(args.directory)    # excluding directories starting with 'fixed' and other typical .gitignore files
                                                    # in future it will be possible to point to a custom .gitignore file
    fixed_dir = f'fixed_{datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")}'

    iol.log(f"Found {len(dir_content)} files to scan", color="cyan", verbose_only=False)

    iol.log(f'Tokens inside the directory: {num_tokens_from_string(dir_content)}', color='bright_cyan')


    iol.log(f"Using model: {args.model}", color="white")
    iol.log(f"Beginning code analysis...", color="white")

    if args.codeql:
        iol.log(f"CodeQL is enabled, I will now begin the scan using CodeQL", color="red")
        # run_codeql_scan(args.directory, args.language, args.command)

    chunks = split_content(dir_content, CFG.token_limit)
    iol.log(f"Splitting the content into {len(chunks)} chunks", color="bright_cyan", verbose_only=True)
    
    await run_agents(args, iol, chunks, fixed_dir)

    print()
    iol.log(f"\tSCAN COMPLETE!\n", color="green")
    iol.log(f"Check the generated raport in {iol.log_file}", color="bright_cyan")

    iol.log(f"Generating patch...", color="bright_cyan")
    generate_patch(args.directory, iol.log_file)

    iol.log(f"Thank you for using the static code analysis agent!", color="bright_cyan")
    # input("If you want to run tests on fixed code (not available in current version), press enter... (or ctrl+c to exit)")


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()