#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import asyncio
import argparse
from utils.io import IOlog
from utils.traverser import scan_directory, walk_directory
import agents

# obsługa programu poprzez argumenty przekazywane w konsoli
parser = argparse.ArgumentParser(description='GPTESTER | Static Code Analysis Agent\n')
parser.add_argument('directory', type=str, help='Path to the directory to scan')
parser.add_argument('-v', '--verbose', help='Wypisz opisy podatności w konsoli, wypisz wszystkie wykonywane kroki', action='store_true')
parser.add_argument('-c', '--codeql', help='Use codeql to enhance the scan, REQUIRED to install CodeQL-CLI console tool', action='store_true')
# parser.add_argument('-n', '--name', help='Name the generated raport, default: "test"', default="test")
parser.add_argument('-m', '--model', help='Choose the LLM model for code analysis, default: "gpt-4"', default="gpt-4")


# Inicjalizacja
args = parser.parse_args()
project_name = os.path.basename(args.directory.rstrip('/'))
iol = IOlog(verbose=args.verbose, name=project_name)

async def main():
    iol.log(f"Welcome to gptester: the Static Code Analysis Agent", color="bright_cyan")
    iol.log(f"I will now begin scanning: {args.directory}, name: {project_name}", color="pink")

    iol.log(f"Beginning scan...", color="bright_cyan")
    dir_content = walk_directory(args.directory)

    iol.log(f"Found {len(dir_content)} files to scan", color="cyan")
    for key, value in dir_content.items():
        iol.log(f"File: {key}, \n```\n{value}\n```", color="green")

    iol.log(f"Beginning code analysis...", color="red")
    iol.log(f"Using model: {args.model}", color="red")

    if args.codeql:
        iol.log(f"CodeQL is enabled, I will now begin the scan using CodeQL", color="red")

    output = await agents.debug_agent(dir_content, iol, args.model, args.directory)
    for message in output:
    # Each message can have multiple content items, so loop through them
        for content_item in message.content:
            text = content_item.text.value
            iol.log(text, color="white")

    
    iol.log(f"Scan complete!", color="bright_cyan", verbose_only=True)

if __name__ == "__main__":
    asyncio.run(main())