import subprocess 
class TestCommand:
    def execute(self):
        raise NotImplementedError("Execute method should be implemented by subclasses.")

class RunCppTestsCommand(TestCommand):
    def __init__(self, cpp_test_executable):
        self.cpp_test_executable = cpp_test_executable

    def execute(self):
        subprocess.run([self.cpp_test_executable])

class RunJavaTestsCommand(TestCommand):
    def execute(self):
        subprocess.run(["mvn", "test"])

class RunPythonTestsCommand(TestCommand):
    def execute(self):
        subprocess.run(["python", "-m", "unittest", "discover"])

class RunRubyTestsCommand(TestCommand):
    def execute(self):
        subprocess.run(["rspec", "--format", "documentation"])

class RunRubyTestsCommand(TestCommand):
    def execute(self):
        subprocess.run(["rspec", "--format", "documentation"])

class RunPhpTestsCommand(TestCommand):
    def execute(self):
        subprocess.run(["phpunit"])

class RunPhpTestsCommand(TestCommand):
    def execute(self):
        subprocess.run(["phpunit"])

class TestRunner:
    def run_test(self, command):
        command.execute()

if __name__ == "__main__":
    test_runner = TestRunner()

    cpp_test_command = RunCppTestsCommand()
    test_runner.run_test(cpp_test_command)

    java_test_command = RunJavaTestsCommand()
    test_runner.run_test(java_test_command)

    python_test_command = RunPythonTestsCommand()
    test_runner.run_test(python_test_command)

    ruby_test_command = RunRubyTestsCommand()
    test_runner.run_test(ruby_test_command)

    php_test_command = RunPhpTestsCommand()
    test_runner.run_test(php_test_command)
