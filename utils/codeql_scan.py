import subprocess
import sys

def run_codeql_scan(directory, language="cpp", command="make"):
    # Replace this with the actual command to initialize the CodeQL database
    init_cmd = ["codeql", "database", "create", f"--language={language}", f"--command={command}" "db", "--source-root", directory]
    # Replace this with the actual command to run the analysis
    analyze_cmd = ["codeql", "database", "analyze", "db", "--format=csv", "--output=results.csv"]

    try:
        # Initialize CodeQL database
        subprocess.run(init_cmd, check=True)
        # Run the analysis
        subprocess.run(analyze_cmd, check=True)
        # Read the results
        with open("results.csv", "r") as results_file:
            results = results_file.read()
        return results
    except subprocess.CalledProcessError as e:
        sys.exit(f"An error occurred while running CodeQL: {e}")
    except FileNotFoundError:
        sys.exit("Could not find the results file. Did the analysis run correctly?")

run_codeql_scan('Vulnerable-Code-Snippets/Buffer_Overflow')
    return results