import unittest
import sys
import subprocess

def run_python_tests(test_path):
    # Create a test loader
    loader = unittest.TestLoader()
    # Discover and load tests
    suite = loader.discover(test_path)

    # Create a test runner that outputs to sys.stderr
    runner = unittest.TextTestRunner(sys.stderr)
    # Run the tests
    result = runner.run(suite)
    return result.wasSuccessful()

def run_node_tests():
    # Define the command to run your Node.js tests
    # This is typically "npm test" or "node <test-runner-script>"
    command = ["npm", "test"]

    # Run the command
    result = subprocess.run(command, capture_output=True, text=True)

    # Output the results
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)

    # Check if the tests were successful
    if result.returncode == 0:
        print("Tests passed successfully.")
    else:
        print("Tests failed.")

def run_cpp_tests(command):
    command = [command]  # Adjust with your test command
    result = subprocess.run(command, capture_output=True, text=True)
    print(result.stdout)
    if result.returncode == 0:
        print("C++ tests passed successfully.")
    else:
        print("C++ tests failed.")

def run_java_tests():
    command = ["mvn", "test"]  # Maven command to run tests
    result = subprocess.run(command, capture_output=True, text=True)
    print(result.stdout)
    if result.returncode == 0:
        print("Java tests passed successfully.")
    else:
        print("Java tests failed.")
