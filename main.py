#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import asyncio
import argparse

from utils.io import IOlog
from utils.traverser import scan_directory, walk_directory
from utils.utils import num_tokens_from_string
# from utils.codeql_scan import run_codeql_scan
import agents

# obsługa programu poprzez argumenty przekazywane w konsoli
parser = argparse.ArgumentParser(description='GPTESTER | Static Code Analysis Agent\n')
parser.add_argument('directory', type=str, help='Path to the directory to scan')
parser.add_argument('-v', '--verbose', help='Print out all the outputs and steps taken', action='store_true')
parser.add_argument('-m', '--model', help='Choose the LLM model for code analysis, default: "gpt-4-1106-preview"', default="gpt-4-1106-preview")
parser.add_argument('-o', '--output', help='Output the results to a file, default: "raports/{name_of_parent_folder}_{timestamp}_raport.md"')
parser.add_argument('-t', '--tests', help='Provide a path to functional tests to run on the project')
parser.add_argument('-c', '--codeql', help='Use codeql to enhance the scan, REQUIRED to install CodeQL-CLI console tool', action='store_true', default=False)
parser.add_argument('--command', help='Provide a build command to run the project for codeql, if no cmake or other file present in the project root directory, default: "make"', default="make")
parser.add_argument('--language', help='Provide a programming language of the project for codeql, default: "cpp"', default="cpp")
# parser.add_argument('-n', '--name', help='Name the generated raport, default: "test"', default="test")


# Inicjalizacja
args = parser.parse_args()
project_name = os.path.basename(args.directory.rstrip('/'))
iol = IOlog(verbose=args.verbose, name=project_name)

async def main():
    iol.log(f"Welcome to gptester: the Static Code Analysis Agent", color="bright_cyan")
    iol.log(f"I will now begin scanning: {args.directory}, name: {project_name}", color="pink")

    iol.log(f"Beginning scan...", color="bright_cyan")
    dir_content = walk_directory(args.directory)

    iol.log(f"Found {len(dir_content)} files to scan", color="cyan", verbose_only=True)
    for key, value in dir_content.items():
        iol.log(f"File: {key}, \n```\n{value}\n```", color="green")

    iol.log(f'Tokens inside the directory: {num_tokens_from_string(dir_content)}', color='bright_cyan')

    iol.log(f"Beginning code analysis...", color="red")
    iol.log(f"Using model: {args.model}", color="red")

    if args.codeql:
        iol.log(f"CodeQL is enabled, I will now begin the scan using CodeQL", color="red")
        # run_codeql_scan(args.directory, args.language, args.command)

    output = await agents.debug_agent(dir_content, iol, args.model, args.directory)
    for message in output:
        for content_item in message.content:
            text = content_item.text.value
            iol.log(text, color="white")

    iol.log(f"Scan complete!", color="bright_cyan", verbose_only=True)

if __name__ == "__main__":
    asyncio.run(main())