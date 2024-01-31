import ast
import os
import re
import json
from pathlib import Path
from utils.config import Config
from utils.utils import num_tokens_from_string


CFG = Config()

class CodeAnalyzer(ast.NodeVisitor):
    def __init__(self):
        self.classes = []
        self.funcs = []
        self.vars = []
        self.imports = []
        self.regex_funcs = []       

    def visit_ClassDef(self, node): 
        self.classes.append(node.name)    
        return self.generic_visit(node)   

    def visit_FunctionDef(self, node):    
        self.funcs.append(node.name)
        for arg in node.args.args:  
            self.vars.append(arg.arg)     
        return self.generic_visit(node)   

    def visit_Assign(self, node):   
        for target in node.targets: 
            if isinstance(target, ast.Name):
                self.vars.append(target.id)
                self.generic_visit(node)

    def visit_Import(self, node):
        for alias in node.names:
            self.imports.append(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):     
        for alias in node.names:    
            self.imports.append(alias.name) 
        self.generic_visit(node)    

    def do_regex(self, code):       
        function_pattern = re.compile(r'def\s+(\w+)\s*\(([^)]*)\)')
        functions = function_pattern.findall(code)    

        self.regex_funcs = [        
            f"{func[0]}({func[1]})" 
            for func in functions   
        ]     

def analyze_python(code):
    analyzer = CodeAnalyzer()       

    try:    
        tree = ast.parse(code)      
        analyzer.visit(tree)        
        analyzer.do_regex(code)     
    except SyntaxError as e:        
        print(f'Syntax error: {e}') 

    return {
        'classes': analyzer.classes,
        'functions': analyzer.funcs,
        'variables': analyzer.vars, 
        'imports': analyzer.imports,
        'regex_functions': analyzer.regex_funcs 
    }     

def parse_js_file(file_path: str):     
    with open(file_path, 'r') as js_file:           
        js_code = js_file.read() 
 
    function_pattern = re.compile(r'function\s+(\w+)\s*\(([^)]*)\)')  
    functions = function_pattern.findall(js_code)   
    function_results = [         
        f"{func[0]}({func[1]})"  
        for func in functions    
    ]         
 
    let_variable_pattern = re.compile(r'let\s+(\w+)')           
    let_variables = let_variable_pattern.findall(js_code)       
    let_variable_results = [     
        f"{variable}"            
        for variable in let_variables  
    ]         
 
    const_variable_pattern = re.compile(r'const\s+(\w+)')       
    const_variables = const_variable_pattern.findall(js_code)   
    const_variable_results = [   
        f"{variable}"            
        for variable in const_variables
    ]         
 
    class_pattern = re.compile(r'class\s+(\w+)')    
    classes = class_pattern.findall(js_code)        
    class_results = [            
        f"{cls}"    
        for cls in classes       
    ]         
 
    import_pattern = re.compile(r'import\s+.*?from\s+.*?;')     
    imports = import_pattern.findall(js_code)       
    import_results = [           
        f"{import_}"
        for import_ in imports   
    ]         
 
    export_pattern = re.compile(r'export\s+.*?;')   
    exports = export_pattern.findall(js_code)       
    export_results = [           
        f"{export}" 
        for export in exports    
    ]         
 
    return {  
        "functions": function_results, 
        "let_variables": let_variable_results,      
        "const_variables": const_variable_results,  
        "classes": class_results,
        "imports": import_results,     
        "exports": export_results,     
    }   
 
def depends_on(file_path: str):
    dependencies = []

    import_patterns = {      
            ".py": [  
                re.compile(r'import\s+([\w\.]+)'),   
                re.compile(r'from\s+([\w\.]+)\s+import\s+([\w\., \(\)]+)')      
            ], 
            ".js": [  
                re.compile(r'import\s+.*?from\s*["\'](.*?)["\']'),
                re.compile(r'require\s*?\(["\'](.*?)["\']\)')  
            ], 
            ".cpp": [re.compile(r'#include\s*["<](.*?)["\']>')]
        }
    
    file_extension = os.path.splitext(file_path)[-1] 
    
    with open(file_path, 'r') as file:   
        file_content = file.read()  
    
        if file_extension in import_patterns:   
            for pattern in import_patterns[file_extension]:
                matches = re.findall(pattern, file_content)
                for match in matches:    
                    if isinstance(match, tuple):
                        # If match is a tuple, get the first element and strip it
                        dependencies.append(match[0].strip())  
                    else:    
                        # If match is a single string, strip it
                        dependencies.append(match.strip()) 

    return dependencies 

def create_tree_with_contents(directory, exclude=['node_modules']): 
    tree = {}  

    if directory in exclude:  
        return tree 

    for item in os.listdir(directory):  
        item_path = os.path.join(directory, item)     
        if os.path.isdir(item_path):    
            tree[item] = create_tree_with_contents(item_path, exclude)     
        else:  
            try:    
                with open(item_path, "r", encoding="utf-8") as file:
                    content = file.read()      
                    tree[item] = content
            except IOError as e: 
                tree[item] = f"Error reading file: {e}"   
            except UnicodeDecodeError as e:    
                tree[item] = f"Error reading file: {e}"   

    return tree

def extractJSON(string: str):
    try:
        start = min(string.find('{'), string.find('['))
        end = max(string.rfind('}'), string.rfind(']')) + 1
        json_str = string[start:end]
        data = json.loads(json_str)

    except Exception as e:
        print(f"extractJSON_error: {e}")
        data = json_str
    return data

def create_code_map(directory: str):
    code_map = {}  
  
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
  
            dependencies = depends_on(file_path)
         
            code_map[file_path] = dependencies  

    return code_map  

def scan_directory(directory):      
    contents = os.listdir(directory)
    data = []   

    for item in contents:
        item_path = os.path.join(directory, item)     
        item_data = {}   

        if os.path.isfile(item_path):     
            if item.endswith(".py"):
                item_data["type"] = "File"
                item_data["name"] = item  
                with open(item_path, 'r') as f: 
                    code = f.read() 
                item_data["properties"] = analyze_python(code)
                item_data["depends_on"] = depends_on(item_path)
            elif item.endswith(".js") or item.endswith(".jsx") or item.endswith(".ts") or item.endswith(".tsx"):  
                item_data["type"] = "File"
                item_data["name"] = item
                # if "bundle" not in item:
                item_data["parameters"] = parse_js_file(item_path)
                item_data["depends_on"] = depends_on(item_path)
            else:        
                item_data["type"] = "File"
                item_data["name"] = item  
        elif os.path.isdir(item_path) and not item.startswith("node_modules") and not item.startswith("build"):      
            item_data["type"] = "Directory" 
            item_data["name"] = item
            item_data["contents"] = scan_directory(item_path)      

        data.append(item_data)      

    return data 

def read_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        return "File not found."
    except Exception as e:
        return f"An error occurred: {e}"

def walk_directory(directory, append_ignore:str=None):
    image_extensions = [
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".bmp",
        ".svg",
        ".ico",
        ".tif",
        ".tiff",
        ".md",
        ".pdf",
        ".properties",
    ] + [f".{ext}" for ext in CFG.ignore_extensions]
    exclude_list = ["GPTested","GPTester", "tests", "node_modules", "build", "dist", "venv", "env", "migrations", ".git", ".vscode", ".idea", ".pytest_cache", 
                    ".cache", ".tox", "docs", "doc", "static", "media", "assets", "logs", "log", "raports", "staticfiles"]
    if append_ignore: exclude_list.append(append_ignore)
    code_contents = {}
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if not d.startswith('fixed') and d not in exclude_list]
        
        for file in files:
            if not any(file.endswith(ext) for ext in image_extensions) and file not in exclude_list:
                try:
                    relative_filepath = os.path.relpath(
                        os.path.join(root, file), directory
                    )
                    code_contents[relative_filepath] = read_file(
                        os.path.join(root, file)
                    )
                except Exception as e:
                    code_contents[
                        relative_filepath
                    ] = f"Error reading file {file}: {str(e)}"
    return code_contents

def split_content_char(dir_content, max_chars):
    """Split directory content into chunks of max_chars"""
    chunks = []
    chunk = {}
    current_chars = 0
    for filename, content in dir_content.items():
        chars = len(content)
        if chars > max_chars:
            # Handle the case where a single file exceeds max_chars
            content_chunks = split_file_into_chunks_char(content, max_chars)
            for content_chunk in content_chunks:
                chunks.append({filename: content_chunk})
        elif current_chars + chars <= max_chars:
            chunk[filename] = content
            current_chars += chars
        else:
            chunks.append(chunk)
            chunk = {filename: content}
            current_chars = chars
    chunks.append(chunk)
    return chunks

def split_file_into_chunks_char(content, max_chars):
    "split one file if exceeds the char limit"
    words = content.split(' ')
    chunks = []
    current_chunk = []
    current_chars = 0

    for word in words:
        chars = len(word)
        if current_chars + chars + 1 > max_chars:  # +1 for the space
            chunks.append(' '.join(current_chunk))
            current_chunk = [word]
            current_chars = chars
        else:
            current_chunk.append(word)
            current_chars += chars + 1  # +1 for the space

    chunks.append(' '.join(current_chunk))

    return chunks

def split_content(dir_content, max_tokens):
    """Split directory content into chunks of max_tokens"""
    chunks = []
    chunk = {}
    current_tokens = 0
    for filename, content in dir_content.items():
        tokens = num_tokens_from_string(content)
        if tokens > max_tokens:
            # Handle the case where a single file exceeds max_tokens
            content_chunks = split_content_into_chunks(content, max_tokens)
            for content_chunk in content_chunks:
                chunks.append({filename: content_chunk})
        elif current_tokens + tokens <= max_tokens:
            chunk[filename] = content
            current_tokens += tokens
        else:
            chunks.append(chunk)
            chunk = {filename: content}
            current_tokens = tokens
    chunks.append(chunk)
    return chunks

def split_content_into_chunks(content, max_tokens):
    "split one file if exceeds the token limit"
    words = content.split(' ')
    chunks = []
    current_chunk = []
    current_tokens = 0

    for word in words:
        tokens = len(word.split(' '))
        if current_tokens + tokens > max_tokens:
            chunks.append(' '.join(current_chunk))
            current_chunk = [word]
            current_tokens = tokens
        else:
            current_chunk.append(word)
            current_tokens += tokens

    chunks.append(' '.join(current_chunk))

    return chunks

def get_directory_content(directory: str) -> dict:
    """
    Returns the contents of a directory.
    
    Args:
        directory (str): The path to the directory.
    
    Returns:
        list: A json representation of the directory contents.
    """
    contents = os.listdir(directory)
    data = []
    
    for item in contents:
        item_path = os.path.join(directory, item)
        item_data = {}
        
        if os.path.isfile(item_path): 
            if item.endswith(".py") or item.endswith(".js") or item.endswith(".jsx") or item.endswith(".ts") or item.endswith(".tsx"):  
                item_data["type"] = "File"
                item_data["name"] = item
                # if "bundle" not in item:
                item_data["functions"] = list_functions_from_js(item_path)
            else:
                item_data["type"] = "File"
                item_data["name"] = item
        elif os.path.isdir(item_path) and not item.startswith("node_modules") and not item.startswith("build"):  
            item_data["type"] = "Directory"
            item_data["name"] = item
            item_data["contents"] = get_directory_content(item_path)
        
        data.append(item_data)
    
    return data

def list_functions_from_js(file_path: str):
    """Returns a list of functions from a JavaScript file."""
    with open(file_path, 'r') as js_file:
        js_code = js_file.read()

    function_pattern = re.compile(r'function\s+(\w+)\s*\(([^)]*)\)')
    functions = function_pattern.findall(js_code)
    
    formatted_functions = [
        f"{func[0]}({func[1]})"
        for func in functions
    ]
    return formatted_functions                                                                                                                

def get_js_function_code(filename: str, function_name: str) -> str:
    """Returns the source code of a JavaScript function. """
    with open(filename, 'r') as file:
        file_content = file.read()

    function_pattern = re.compile(rf'function {function_name}\s*\(([^)]*)\)')
    match = function_pattern.search(file_content)

    if not match:
        return None

    start_index = match.start()
    brace_stack = []
    end_index = -1

    for i in range(start_index, len(file_content)):
        if file_content[i] == '{':
            brace_stack.append(i)
        elif file_content[i] == '}':
            brace_stack.pop()
            if not brace_stack:
                end_index = i
                break

    function_source = file_content[start_index:end_index + 1]
    return function_source

def main():    
    path = Path(CFG.workspace+'/6bx5URh6xk-SyXcDAAAB/RecipeSharingWebApp').absolute()
    result = create_tree_with_contents(path)
    print(json.dumps(result, indent=4)) 
    # print(f'tokens: {num_tokens_from_messages(str(result))}') # Django project - całkiem duży, zajmuje 5306 tokenów 

if __name__ == "__main__": 
    main()  