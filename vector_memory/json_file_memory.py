import json
import os
from typing import List, Union
from vector_memory.memory import MemoryBackend
from vector_memory.models import Task, CodeFile

class JSONFileMemory(MemoryBackend):
    """Memory backend that uses a JSON file to store and retrieve tasks and code files"""

    def __init__(self, dbs):
        self.memory_path = dbs.memory.path
        self.tasks = os.path.join(self.memory_path, 'tasks.json')
        self.codes = os.path.join(self.memory_path, 'codes.json')
        if not os.path.isdir(self.memory_path):
            os.mkdir(self.memory_path)

        with open(self.tasks, 'w') as f:
            json.dump([], f)
        
        with open(self.codes, 'w') as f:
            json.dump([], f)

    def _load_tasks(self):
        with open(self.tasks, 'r') as f:
            items = json.load(f)
            return [Task(**item) for item in items]

    def _load_codes(self):
        with open(self.codes, 'r') as f:
            items = json.load(f)
            return [CodeFile(**item) for item in items]

    def _save_items(self, items):
        file_path = self.tasks if isinstance(items[0], Task) else self.codes
        with open(file_path, 'w') as f:
            json.dump([item.__dict__ for item in items], f)

    def add(self, item: Task|CodeFile):
        items = self._load_tasks() if isinstance(item, Task) else self._load_codes()
        items.append(item)
        self._save_items(items)
    
    def add_task(self, task, result: str = None):
        self.add(task) if result is None else self.add(task, result)

    def add_code_file(self, item: CodeFile):
        self.add(item)

    def discard(self, item: Union[Task, CodeFile]):
        items = self._load_tasks() if isinstance(item, Task) else self._load_codes()
        items = [i for i in items if i != item]
        self._save_items(items)

    def get_task(self, query: str) -> Union[Task, None]:
        tasks = self._load_tasks()
        if not tasks:
            return None
        most_relevant_task = max(tasks, key=lambda task: task.relevance_for(query))
        return most_relevant_task if most_relevant_task.relevance_for(query) > 0 else None

    def get_relevant_tasks(self, query: str, k: int) -> List[Task]:
        tasks = self._load_tasks()
        sorted_tasks = sorted(tasks, key=lambda task: task.relevance_for(query), reverse=True)
        top_k_tasks = sorted_tasks[:k]

        relevant_tasks = [task for task in top_k_tasks if task.relevance_for(query) > 0]
        return relevant_tasks
    
    def get_relevant_codefiles(self, query: str, k: int) -> List[CodeFile]:
        code_files = self._load_codes()
        sorted_code_files = sorted(code_files, key=lambda code: code.relevance_for(query), reverse=True)
        top_k_code_files = sorted_code_files[:k]

        relevant_code_files = [code for code in top_k_code_files if code.relevance_for(query) > 0]
        return relevant_code_files

    def get_all_tasks(self) -> List[Task]:
        return self._load_tasks()
    
    def get_codefile(self, file_name: str) -> CodeFile:
        return super().get_codefile(file_name)

    def upsert_project(self, project_files):
        # Upsert new project files to JSON file
        for file_name, content in project_files.items():
            self.add(CodeFile(file_name, content))

    def retrieve_project(self):
        # Retrieve the entire project data
        items = self._load_items()
        return {item.file_name: item for item in items if isinstance(item, CodeFile)}