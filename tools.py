import os
import csv
from utils.io import IOlog
from utils.tests_runner import TestRunner, RunCppTestsCommand, RunJavaTestsCommand, RunPythonTestsCommand, RunRubyTestsCommand, RunPhpTestsCommand

iol = IOlog('testing') # singleton

async def write_file(filename, content):
    """{
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
    }"""
    try:
        iol.log(f'Writing file {filename}...', color="orange")
        iol.log(f'content: \n {content}...', color="orange", verbose_only=True)

        if os.path.isdir(filename):
            raise Exception(f"Cannot write file: A directory with the name '{filename}' already exists.")


        os.makedirs(os.path.dirname(filename), exist_ok=True)

        with open(filename, 'w') as file:
            file.write(content)

        iol.log(f"File '{filename}' written successfully.", color="green")
        return f"File '{filename}' written successfully."
    except Exception as e:
        iol.log(f"Error writing file: {e}", color="red")
        return f"Error writing file: {e}"


async def append_to_csv(file_path, row_data):
    """{
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
    }"""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    next_id = 1

    # Check if file exists before reading
    if os.path.exists(file_path):
        with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile, delimiter=';', quotechar='*')
            for row in reader:
                next_id += 1
    else:
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile, delimiter=';', quotechar='*', quoting=csv.QUOTE_MINIMAL)
            writer.writerow("Lp.;Vulnerability;File;Line;Severity;Description;Solution")

    with open(file_path, 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile, delimiter=';', quotechar='*', quoting=csv.QUOTE_MINIMAL)
        writer.writerow([next_id] + row_data)
        return f"Row appended to '{file_path}'."
        

async def run_tests(language, executable=None):
    """{
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
    }"""
    test_runner = TestRunner()
    command = None

    if language == 'cpp':
        command = RunCppTestsCommand(executable)
    elif language == 'java':
        command = RunJavaTestsCommand()
    elif language == 'python':
        command = RunPythonTestsCommand()
    elif language == 'ruby':
        command = RunRubyTestsCommand()
    elif language == 'php':
        command = RunPhpTestsCommand()

    if command:
        try:
            test_runner.run_test(command)
        except:
            return {"status": "error", "output": "Tests failed"}
        return {"status": "success", "output": "Tests executed for " + language + " project with " + executable}
    else:
        return {"status": "error", "output": "Unsupported language"}
