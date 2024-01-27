import json
import os
from typing import List, Union
from vector_memory.memory import MemoryBackend
from vector_memory.models import Raport, CodeFile

    # Wektorowa baza danych - pochodzenie: mój wcześniejszy projekt, kod w trakcie modyfikacji

class JSONFileMemory(MemoryBackend):
    """Memory backend that uses a JSON file to store and retrieve raports and code files
    Wektorowa baza danych - kod pochodzi z mojego wcześniejszego projektu  W PROCESIE INTEGRACJI"""

    def __init__(self, dbs):
        self.memory_path = dbs.memory.path
        self.raports = os.path.join(self.memory_path, 'raports.json')
        self.codes = os.path.join(self.memory_path, 'codes.json')
        if not os.path.isdir(self.memory_path):
            os.mkdir(self.memory_path)

        with open(self.raports, 'w') as f:
            json.dump([], f)
        
        with open(self.codes, 'w') as f:
            json.dump([], f)

    def _load_raports(self):
        with open(self.raports, 'r') as f:
            items = json.load(f)
            return [Raport(**item) for item in items]

    def _load_codes(self):
        with open(self.codes, 'r') as f:
            items = json.load(f)
            return [CodeFile(**item) for item in items]

    def _save_items(self, items):
        file_path = self.raports if isinstance(items[0], Raport) else self.codes
        with open(file_path, 'w') as f:
            json.dump([item.__dict__ for item in items], f)

    def add(self, item: Raport|CodeFile):
        items = self._load_raports() if isinstance(item, Raport) else self._load_codes()
        items.append(item)
        self._save_items(items)
    
    def add_raport(self, raport, result: str = None):
        self.add(raport) if result is None else self.add(raport, result)

    def add_code_file(self, item: CodeFile):
        self.add(item)

    def discard(self, item: Union[Raport, CodeFile]):
        items = self._load_raports() if isinstance(item, Raport) else self._load_codes()
        items = [i for i in items if i != item]
        self._save_items(items)

    def get_raport(self, query: str) -> Union[Raport, None]:
        raports = self._load_raports()
        if not raports:
            return None
        most_relevant_raport = max(raports, key=lambda raport: raport.relevance_for(query))
        return most_relevant_raport if most_relevant_raport.relevance_for(query) > 0 else None

    def get_relevant_raports(self, query: str, k: int) -> List[Raport]:
        raports = self._load_raports()
        sorted_raports = sorted(raports, key=lambda raport: raport.relevance_for(query), reverse=True)
        top_k_raports = sorted_raports[:k]

        relevant_raports = [raport for raport in top_k_raports if raport.relevance_for(query) > 0]
        return relevant_raports
    
    def get_relevant_codefiles(self, query: str, k: int) -> List[CodeFile]:
        code_files = self._load_codes()
        sorted_code_files = sorted(code_files, key=lambda code: code.relevance_for(query), reverse=True)
        top_k_code_files = sorted_code_files[:k]

        relevant_code_files = [code for code in top_k_code_files if code.relevance_for(query) > 0]
        return relevant_code_files

    def get_all_raports(self) -> List[Raport]:
        return self._load_raports()
    
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