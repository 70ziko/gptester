import os
from utils.io import IOlog

iol = IOlog()

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
        iol.log(f'Writing file {filename}...')
        iol.log(f'content: \n {content}...')

        if os.path.isdir(filename):
            raise Exception(f"Cannot write file: A directory with the name '{filename}' already exists.")


        os.makedirs(os.path.dirname(filename), exist_ok=True)

        with open(filename, 'w') as file:
            file.write(content)

        iol.log(f"File '{filename}' written successfully.")
        return f"File '{filename}' written successfully."
    except Exception as e:
        iol.log(f"Error writing file: {e}")
        return f"Error writing file: {e}"

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