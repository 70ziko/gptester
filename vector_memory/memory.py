from abc import ABC, abstractmethod
from typing import List
from vector_memory.models import Raport, CodeFile

class MemoryBackend(ABC):
    """Abstract base class for a memory backend
    Wektorowa baza danych - pochodzenie: mój wcześniejszy projekt, kod w trakcie modyfikacji"""

    @abstractmethod
    def add_raport(self, raport, result):
        pass

    @abstractmethod
    def add_code_file(self, item: CodeFile):
        pass

    @abstractmethod
    def discard(self, item):
        pass

    @abstractmethod
    def get_raport(self, raport_id: int) -> Raport:
        pass

    @abstractmethod
    def get_codefile(self, file_name: str) -> CodeFile:
        pass

    @abstractmethod
    def get_relevant_raports(self, query: str, k: int) -> List[Raport]:
        pass

    @abstractmethod
    def get_relevant_codefiles(self, query: str, k: int) -> List[CodeFile]:
        pass

    @abstractmethod
    def get_all_raports(self) -> List[Raport]:
        pass

class Memory:
    """Class to interact with the memory backend
    Wektorowa baza danych - pochodzenie: mój wcześniejszy projekt, kod obecnie w procesie integracji"""

    def __init__(self, backend: MemoryBackend):
        self.backend = backend

    def add_raport(self, raport: Raport, result: str = None):
        if result and isinstance(raport, Raport):
            raport.result = result
            self.backend.add_raport(raport)
            return
    
        raport_dict = raport if isinstance(raport, dict) else {}
        if result:
            raport_dict['result'] = result
        
        raport = raport(
            raport_dict.get('raport_id', ''),
            raport_dict.get('name', ''),
            raport_dict.get('raport_description', ''),
            raport_dict.get('result', ''),
            raport_dict.get('filename', '')
        )
        
        self.backend.add_raport(raport)

    def add_code_file(self, file_name: str, content: str):
        code_file = CodeFile(file_name, content)
        self.backend.add_code_file(code_file)

    def get_relevant_raport(self, query: str):
        return self.backend.get_relevant_raports(query)[0]

    def get_relevant_code_file(self, query: str):
        return self.backend.get_relevant_codefiles(query)[0]

    def get_relevant_raports(self, query: str, k: int):
        return self.backend.get_relevant_raports(query, k)

    def get_relevant_codefiles(self, query: str, k: int):
        return self.backend.get_relevant_codefiles(query, k)
    
    def popback(self):
        raports = self.backend.get_relevant_raports("", 1000)
        if not raports:
            raise Exception("No raports to pop in memory")
        
        last_raport = max(raports, key=lambda x: x.raport_id)

        self.backend.discard(last_raport)
        return last_raport