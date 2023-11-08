#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse

# obsługa programu poprzez argumenty przekazywane w konsoli
parser = argparse.ArgumentParser(description='Program porównujący zainstalowane oprogramowanie z bazą danych podatności \n')
parser.add_argument('-v','--verbose', help='Zawrzyj opisy podatności w wyniku, wypisz wszystkie wykonywane kroki', action='store_true')
parser.add_argument('-d','--csv', type=str , help='Określ ścieżkę projektu przeznaczonego do skanowania', default=".", metavar='PATH')


args=parser.parse_args()

def main():
    if args.NVD and args.verbose:
        print("Przeszukiwanie bazy danych podatności NVD")

if __name__ == "__main__":
    main()