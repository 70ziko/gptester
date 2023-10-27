import hashlib
from utils.utils import get_embedding
from openai.embeddings_utils import cosine_similarity

class Task:
    """Task object containing the task details as well as its result"""
    
    __next_id__ = 1
    
    def __init__(self, task_id: int = None, name: str = 'no_name', description: str = '', result: str = "Uncompleted", filename: str = '', score: float = 0.0, **kwargs):
        self.task_id = Task.__next_id__ if not task_id else task_id
        Task.__next_id__ += 1
        self.name = name
        self.description = description
        self.result = result
        #self.__embedding__ = self._get_embedding()     # błędnie myślałem że ada jest 0,- xdd
        self.score = score
        self.filename = filename

    def _get_embedding(self):
        return get_embedding(str(self.result))

    def relevance_for(self, query: str) -> float:
        embedding = get_embedding(query)
        task = get_embedding(self.name)
        score = cosine_similarity(task, embedding)
        return score
    
    def to_dict(self):
        return {
            'task_id': self.task_id,
            'name': self.name,
            'task_description': self.description,
            'result': self.result,
            'filename': self.filename,
        }


class CodeFile:
    """CodeFile object containing the file name and its content"""

    def __init__(self, file_path: str, content: str, score: float = 0.0):
        self.path = file_path
        self.name = file_path.split('/')[-1]
        self.content = content
        self.embedding = self._get_embedding()
        self.score = score
        self.hash = self.calculate_hash()

    def _get_embedding(self):
        return get_embedding(self.content)

    def calculate_hash(self):
        self.hash = hashlib.sha256(self.content.encode()).hexdigest()

    def _set_content(self, content: str):
        self.content = content
        self.hash = hashlib.sha256(self.content.encode()).hexdigest()
        self.embedding = self._get_embedding()
    
    def relevance_for(self, query: str):
        embedding = get_embedding(query)
        file = get_embedding(self.name)
        score = cosine_similarity(file, embedding)
        return score
    