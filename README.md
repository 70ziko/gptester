# gptester
An AI agent for static code analysis, my engineering thesis. 
Capable of finding security vulnerabilities in the code and proposing fixes.
===

## Description
The program is a static code analysis agent, which uses the GPT-4 model to generate a report on the quality of the code and propose fixes. It's main focus is the security of the code, later this will be extended. The program is written in Python, and the GPT-4 model is provided by OpenAI. The program is designed to be run from the command line, and the results are saved in a markdown file. The program can be run with the following arguments:
```
 > ./main.py -h
usage: main.py [-h] [-v] [-m MODEL] [-o OUTPUT] [-t TESTS] [-c] [--command COMMAND] [--language LANGUAGE] directory

GPTESTER | Static Code Analysis Agent

positional arguments:
  directory             Path to the directory to scan

options:
  -h, --help            show this help message and exit
  -v, --verbose         Print out all the outputs and steps taken
  -m MODEL, --model MODEL
                        Choose the LLM model for code analysis, default: "gpt-4-1106-preview"
  -o OUTPUT, --output OUTPUT
                        Output the results to a file, default: "raports/{name_of_parent_folder}_{timestamp}_raport.md"
  -t TESTS, --tests TESTS
                        Provide a path to functional tests to run on the project
  -c, --codeql          Use codeql to enhance the scan, REQUIRED to install CodeQL-CLI console tool
  --command COMMAND     Provide a build command to run the project for codeql, if no cmake or other file present in the project root directory, default: "make"
  --language LANGUAGE   Provide a programming language of the project for codeql, default: "cpp"
```
===

## Installation
```bash

Workflow: 
1. Checkout the code
2. Set up Python
3. Install dependencies using pip
4. Run the GitHub Actions workflow

Command for running the GitHub Actions workflow:
```
./main.py --help
```
pip install -r requirements.txt
```

## Usage
```bash
cd gptester
python main.py -h
```
or 
```bash
cd gptester
chmod +x main.py
./main.py --help
```

===
## In development
- [x] Basic functionality
- [x] CodeQL integration
- [ ] LATEX and writing the thesis
- [ ] Updating the codebase with git and patch files - not practical for research purposes
- [ ] Adding more tests
- [ ] Adding more languages for codeql