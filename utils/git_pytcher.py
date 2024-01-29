import git
import os
import tempfile
import shutil
import subprocess

def generate_patch(original_dir: str, fixed_dir: str, patch_file_path: str):
    """Generates a patch file for the changes between the original and fixed files. Uses a temporary git repository to create the patch file.

    Args:
        original_dir (str): directory containing the original files, use args.directory
        fixed_dir (str): directory containing the fixed files, use main.fixed_dir
        patch_file_path (str): location for the patch file, use args.patch_file
    """

    with tempfile.TemporaryDirectory() as tempdir:
        repo = git.Repo.init(tempdir)

        for file in os.listdir(original_dir):
            original_file_path = os.path.join(original_dir, file)
            temp_file_path = os.path.join(tempdir, file)
            if os.path.isfile(original_file_path):
                shutil.copy2(original_file_path, temp_file_path)
        
        # commit original files
        repo.git.add(A=True)
        repo.git.commit('-m', 'Initial commit with original files')

        for file in os.listdir(fixed_dir):
            fixed_file_path = os.path.join(fixed_dir, file)
            temp_file_path = os.path.join(tempdir, file)
            if os.path.isfile(fixed_file_path):
                shutil.copy2(fixed_file_path, temp_file_path)

        # create diff
        patch_data = repo.git.diff('HEAD', cached=True)

        if not os.path.exists(patch_file_path): 
            open(patch_file_path, 'w').close()
        with open(patch_file_path, 'w') as patch_file: 
            patch_file.write(patch_data)

        print(f'Patch file created at: {patch_file_path}')


def check_patch(patch_file_path):
    # Construct the git apply command with the --check flag
    command = ["git", "apply", "--check", patch_file_path]

    try:
        # Run the command using subprocess
        result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        # If the command was successful, there are no errors, and the patch can be applied cleanly
        if result.returncode == 0:
            print("The patch can be applied cleanly.")
        else:
            # This branch might not be reached because a non-zero return code will raise a CalledProcessError
            print("There might be issues applying the patch.")
            print(result.stdout)
            print(result.stderr)

    except subprocess.CalledProcessError as e:
        # If there's an error (e.g., patch cannot be applied), print the error message
        print(f"Error checking patch: {e.stderr}")
