def write_file(filename, content):
    """
    Writes the provided content to a file.
    
    Args:
    filename (str): The name of the file to write.
    content (str): The content to write into the file.
    
    Returns:
    str: A message indicating success or failure.
    """
    try:
        print(f'Writing file {filename}...')
        print(f'content: \n {content}...')

        with open(filename, 'w') as file:
            file.write(content)
        return f"File '{filename}' written successfully."
    except Exception as e:
        print(f"Error writing file: {e}")
        return f"Error writing file: {e}"
