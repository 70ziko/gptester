#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import argparse

# obsługa programu poprzez argumenty przekazywane w konsoli
parser = argparse.ArgumentParser(description='Static Code Analysis Agent\n')
parser.add_argument('directory', type=str, help='Path to the directory to scan')
parser.add_argument('-v', '--verbose', help='Zawrzyj opisy podatności w wyniku, wypisz wszystkie wykonywane kroki', action='store_true')

args = parser.parse_args()

print(args.directory)


args=parser.parse_args()

def main():
    if args.directory:
        print("Directory: " + args.directory)

if __name__ == "__main__":
    main()