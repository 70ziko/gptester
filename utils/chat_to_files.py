import re
import os

def workspace_dirs(workspace):      
    """Find all subdirectories in workspace."""    
    return [os.path.join(workspace, d) for d in os.listdir(workspace) if os.path.isdir(os.path.join(workspace, d))] 
      
def parse_chat(chat):
    print(f'chat: {chat}')
    regex = r"(\S+)\n\s*```(\w+)?[^\n]*\n(.+?)```"
    matches = re.finditer(regex, chat, re.DOTALL)    
    print(f'matches: {matches}')
    excluded_languages = ['bash', 'markdown']   
      
    files = []
    for match in matches:    
        language_type = match.group(2)
      
        # Skip the files of excluded languages
        if language_type in excluded_languages:      
            continue 
      
        # Strip the filename of any non-allowed characters and convert / to \
        path = re.sub(r'[<>"|?*]', "", match.group(1))

        # Remove leading and trailing brackets
        path = re.sub(r"^\[(.*)\]$", r"\1", path)

        # Remove leading and trailing backticks
        path = re.sub(r"^`(.*)`$", r"\1", path)

        # Remove trailing ]
        path = re.sub(r"\]$", "", path)

        path = eval_path(workspace_dirs('workspace'), path)
      
        code = match.group(3)
        
        files.append((path, code))
    
    return files

def eval_path(directories, path=None):
    """Check path againt all dirs in workspace"""
    for dir in directories:
        if dir.endswith(path):
            return os.path.join(dir, path)
    return path
      
      
def to_files(chat, workspace):      
    """Parse chat and save files to workspace."""
    files = parse_chat(chat) 
    print(files)
    for file_name, file_content in files:    
        workspace[file_name] = file_content  

def validate_schema(output):
    pattern = r"(\S+)\n\s*```(\w+)?[^\n]*\n(.+?)```"
    match = re.search(pattern, output, re.DOTALL)
    if match is None:
        raise ValueError("Output does not match required schema.")