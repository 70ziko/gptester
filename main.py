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
timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")

banner = f"""
                  ___  ___  _____           _             
                 / __|| _ \|_   _| ___  ___| |_  ___  _ _ 
                | (_ ||  _/  | |  / -_)(_-/|  _|/ -_)| '_|
                 \___||_|    |_|  \___|/__/ \__|\___||_|  

         The static code analysis agent, version: {CFG.version}\n\n"""

# obsługa programu poprzez argumenty przekazywane w konsoli
parser = argparse.ArgumentParser(description=banner, formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('directory', type=str, help='Path to the directory to scan\n')
parser.add_argument('-v', '--verbose', help='Print out all the outputs and steps taken\n', action='store_true')
parser.add_argument('-m', '--model', help='Choose the LLM model for code analysis, default: "gpt-4-1106-preview"', default="gpt-4-1106-preview")
parser.add_argument('-r', '--retrieval', help='Turn on Retrieval Augmented Generation for code analysis, default: False\n', action='store_true', default=False)
parser.add_argument('-f', '--file-to-know', help='Point to a file to be uploaded to the knowledge base for retrieval\n default: "699.csv" - CVE database in csv \n!CURRENT VERSION SUPPORTS ONE FILE!\n', default="699.csv")
parser.add_argument('-i', '--ignore', help='Provide a path to a .gitignore file to ignore files from the scan, \na typical lists of files will be ignored by default\n')
parser.add_argument('-p', '--patch-file', help='Provide a path for the generated patch file \ndefault: "{your_project_dir}/GPTested/{timestamp}_patch.diff"\n', default=f"GPTested/{timestamp}_patch.diff")
parser.add_argument('-o', '--output', help='Output the results to a specified directory\n')
parser.add_argument('-t', '--tests', help='Provide a path to functional tests to run on the project \nif you want to generate tests provide a prompt for the LLM like "generate"\n')
parser.add_argument('-c', '--codeql', help='!IN TESTING!NOT STABLE! Use codeql to enhance the scan \nREQUIRED to install CodeQL-CLI console tool\n', action='store_true', default=False)
parser.add_argument('--command', help='Provide a build command to run the project for codeql if no configuration file, \nlike cmake present in the project root directory, default: "make"\n', default="make")
parser.add_argument('--language', help='Provide a programming language of the project for codeql, default: "cpp"\n', default="cpp")


# Inicjalizacja
args = parser.parse_args()

project_name = os.path.basename(args.directory.rstrip('/'))
iol = IOlog(args.directory, verbose=args.verbose, name=project_name)

# Import agents after iol is ready and singletonned
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
    fixed_dir = f'GPTested/fixed_{timestamp}'
    
    print(banner)

    iol.log(f"Beginning scan for {args.directory}", color="pink")

    ignore_content = open(args.ignore, 'r').read() if args.ignore else '.gitignore'
    dir_content = walk_directory(args.directory, ignore_content)    

    iol.log(f"Found {len(dir_content)} files to scan", color="cyan", verbose_only=False)
    iol.log(f'Tokens inside the directory: {num_tokens_from_string(dir_content)}', color='bright_cyan')
    iol.log(f"Using model: {args.model}", color="white")
    iol.print(f"Beginning code analysis...", color="white")

    if args.codeql:
        iol.log(f"CodeQL is enabled, I will now begin the scan using CodeQL", color="red")
        # run_codeql_scan(args.directory, args.language, args.command)

    chunks = split_content(dir_content, CFG.token_limit)                                # Assistant API ogranicza liczbę ZNAKÓW do 32k XD! 
    iol.log(f"Splitting the content into {len(chunks)} chunks", color="bright_cyan")    # więc nie ma sensu liczyć tokenów XDD
    
    await run_agents(args, iol, chunks, fixed_dir)

    print()
    iol.log(f"\tSCAN COMPLETE!\n", color="green")
    print(f"\nCheck the generated raport in {iol.log_file} and fixed files in the {fixed_dir}\n")

    iol.print(f"Generating patch file...", color="bright_black", verbose_only=True)
    generate_patch(args.directory, os.path.join(args.directory, fixed_dir), os.path.join(args.directory, args.patch_file))
    iol.log(f"Patch generated in {args.patch_file}", color="bright_cyan")

    iol.print(f"To apply the changes with a git commit, run: \ngit am --directory={args.directory} {args.patch_file}\n", color="bright_cyan", timestamp=False)
    iol.print(f"or:\n\t cd {args.directory} \n\t git am {args.patch_file}", color="bright_cyan", timestamp=False)
    iol.print(f"To apply the changes overwritting the file contents !ORIGINAL CONTENT WILL BE LOST!, run: \n\tgit apply --directory={args.directory} {args.patch_file}", color='red', timestamp=False)

    iol.print(f"Thank you for using the static code analysis agent!", color="bright_cyan")
    # input("If you want to run tests on fixed code (not available in current version), press enter... (or ctrl+c to exit)")


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()