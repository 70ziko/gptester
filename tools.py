import os
from utils.io import IOlog
from utils.tests_runner import TestRunner, RunCppTestsCommand, RunJavaTestsCommand, RunPythonTestsCommand, RunRubyTestsCommand, RunPhpTestsCommand

iol = IOlog() # singleton

async def write_file(filename, content):
    """
    Writes the provided content to a file.
    
    Args:
    filename (str): The name of the file to write.
    content (str): The content to write into the file.
    
    Returns:
    str: A message indicating success or failure.
    """
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
    
# JSON for openai tool calling
write_file_json = {
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
    }


def run_tests(language, executable=None):
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


# JSON for openai tool calling

run_tests_json = {
  "function": {
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
    },
    "returns": {
      "type": "object",
      "properties": {
        "status": {
          "type": "string",
          "description": "The status of the test execution."
        },
        "output": {
          "type": "string",
          "description": "Output generated by the test command."
        }
      }
    }
  }
}
