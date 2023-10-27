from abc import ABC, abstractmethod
from typing import List
from vector_memory.models import Task, CodeFile

class MemoryBackend(ABC):
    """Abstract base class for a memory backend"""

    @abstractmethod
    def add_task(self, task, result):
        pass

    @abstractmethod
    def add_code_file(self, item: CodeFile):
        pass

    @abstractmethod
    def discard(self, item):
        pass

    @abstractmethod
    def get_task(self, task_id: int) -> Task:
        pass

    @abstractmethod
    def get_codefile(self, file_name: str) -> CodeFile:
        pass

    @abstractmethod
    def get_relevant_tasks(self, query: str, k: int) -> List[Task]:
        pass

    @abstractmethod
    def get_relevant_codefiles(self, query: str, k: int) -> List[CodeFile]:
        pass

    @abstractmethod
    def get_all_tasks(self) -> List[Task]:
        pass

class Memory:
    """Class to interact with the memory backend"""

    def __init__(self, backend: MemoryBackend):
        self.backend = backend

    def add_task(self, task: Task, result: str = None):
        if result and isinstance(task, Task):
            task.result = result
            self.backend.add_task(task)
            return
    
        task_dict = task if isinstance(task, dict) else {}
        if result:
            task_dict['result'] = result
        
        task = Task(
            task_dict.get('task_id', ''),
            task_dict.get('name', ''),
            task_dict.get('task_description', ''),
            task_dict.get('result', ''),
            task_dict.get('filename', '')
        )
        
        self.backend.add_task(task)

    def add_code_file(self, file_name: str, content: str):
        code_file = CodeFile(file_name, content)
        self.backend.add_code_file(code_file)

    def get_relevant_task(self, query: str):
        return self.backend.get_relevant_tasks(query)[0]

    def get_relevant_code_file(self, query: str):
        return self.backend.get_relevant_codefiles(query)[0]

    def get_relevant_tasks(self, query: str, k: int):
        return self.backend.get_relevant_tasks(query, k)

    def get_relevant_codefiles(self, query: str, k: int):
        return self.backend.get_relevant_codefiles(query, k)
    
    def popback(self):
        tasks = self.backend.get_relevant_tasks("", 1000)
        if not tasks:
            raise Exception("No tasks to pop in memory")
        
        last_task = max(tasks, key=lambda x: x.task_id)

        self.backend.discard(last_task)
        return last_task