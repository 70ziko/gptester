import git
import os
import tempfile
import shutil
import subprocess

def generate_patch(original_dir: str, fixed_dir: str, patch_file_path: str):
    """Generates a patch file for the changes between the original and fixed files. Uses a temporary git repository to create the patch file.

    Args:
        original_dir (str): directory containing the original files, use args['directory']
        fixed_dir (str): directory containing the fixed files, use args['main.fixed_dir']
        patch_file_path (str): location for the patch file, use args['patch_file']
    """

    with tempfile.TemporaryDirectory() as tempdir:
        repo = git.Repo.init(tempdir)

        for file in os.listdir(original_dir):
            original_file_path = os.path.join(original_dir, file)
            temp_file_path = os.path.join(tempdir, file)
            if os.path.isfile(original_file_path):
                shutil.copy2(original_file_path, temp_file_path)
        
        # commit original files
        repo.git.add(all=True)
        og_commit = repo.git.commit('-m', 'Initial commit with original files')

        for file in os.listdir(fixed_dir):
            fixed_file_path = os.path.join(fixed_dir, file)
            temp_file_path = os.path.join(tempdir, file)
            if os.path.isfile(fixed_file_path):
                shutil.copy2(fixed_file_path, temp_file_path)
        
        # commit fixed files
        repo.git.add(all=True)
        fix_commit = repo.git.commit('-m', 'Commit with fixed files')

        # create diff
        # t = repo.head.commit.tree
        patch_data = repo.git.diff('HEAD~1', 'HEAD')
        print(f'patch_data: {patch_data}')

        if not os.path.exists(patch_file_path): 
            open(patch_file_path, 'w').close()
        with open(patch_file_path, 'w') as patch_file: 
            patch_file.write(patch_data)

        print(f'Patch file created at: {patch_file_path}')


def check_patch(patch_file_path, iol):
    # Construct the git apply command with the --check flag
    command = ["git", "apply", "--check", patch_file_path]

    try:
        # Run the command using subprocess
        result = subprocess.run(command, check=True, capture_output=True, text=True)

        # If the command was successful, there are no errors, and the patch can be applied cleanly
        if result.returncode == 0:
            iol.log("The patch can be applied cleanly.")
        else:
            # This branch might not be reached because a non-zero return code will raise a CalledProcessError
            iol.log("There might be issues applying the patch.")
            iol.log(result.stdout)
            iol.log(result.stderr)

    except subprocess.CalledProcessError as e:
        # If there's an error (e.g., patch cannot be applied), print the error message
        iol.log(f"Error checking patch: {e.stderr}")

def apply_patch(patch_file_path):
    # Construct the git apply command
    command = ["git", "apply", patch_file_path]

    try:
        # Run the command using subprocess
        result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        # If the command was successful, print the output
        if result.returncode == 0:
            print(result.stdout)

    except subprocess.CalledProcessError as e:
        # If there's an error (e.g., patch cannot be applied), print the error message
        print(f"Error applying patch: {e.stderr}")

def main():
    generate_patch('Vulnerable-Code-Snippets/Buffer_Overflow', 'Vulnerable-Code-Snippets/Buffer_Overflow/GPTested/fixed_2024-01-28_23:21:00', 'patch.txt')
    check_patch('patch.txt')
    # apply_patch('patch.txt')

if __name__ == '__main__':
    main()