import git
import os
import tempfile
import shutil

def generate_patch(original_dir, fixed_dir, patch_file_path):
    # Create a temporary directory to initialize a git repository
    with tempfile.TemporaryDirectory() as tempdir:
        # Initialize a git repository in the temporary directory
        repo = git.Repo.init(tempdir)

        # Copy original files to the temporary directory
        for file in os.listdir(original_dir):
            original_file_path = os.path.join(original_dir, file)
            temp_file_path = os.path.join(tempdir, file)
            if os.path.isfile(original_file_path):
                shutil.copy2(original_file_path, temp_file_path)
        
        # Add and commit the original files to the temporary git repository
        repo.git.add(A=True)
        repo.git.commit('-m', 'Initial commit with original files')

        # Overwrite the original files in the temporary directory with the fixed files
        for file in os.listdir(fixed_dir):
            fixed_file_path = os.path.join(fixed_dir, file)
            temp_file_path = os.path.join(tempdir, file)
            if os.path.isfile(fixed_file_path):
                shutil.copy2(fixed_file_path, temp_file_path)

        # Use git diff to create a patch for the changes
        patch_data = repo.git.diff('HEAD', cached=True)

        # Write the patch data to the specified patch file
        with open(patch_file_path, 'w') as patch_file:
            patch_file.write(patch_data)

        print(f'Patch file created at: {patch_file_path}')