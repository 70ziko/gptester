import os
import pinecone
import hashlib
from vector_memory.memory import MemoryBackend
from typing import Union, List
from vector_memory.models import Raport, CodeFile
from utils.config import Config
from DB import DBs
from utils.utils import get_embedding

CFG = Config()

class PineconeMemory(MemoryBackend):
    """Memory backend that uses Pinecone to store and retrieve raports and code files
    Wektorowa baza danych - kod pochodzi z mojego wcześniejszego projektu, W PROCESIE INTEGRACJI"""

    def __init__(self, dbs: DBs, index_name: str, namespace: str):
        self.dbs = dbs
        self.index_name = index_name
        self.raports_namespace = "raports_"+namespace
        self.codefiles_namespace = "codefiles_"+namespace
        self.all_raports_ids = []

        pinecone.init(api_key=CFG.pinecone_api_key, environment=CFG.pinecone_region)
        # Create Pinecone index
        dimension = 1536
        metric = "cosine"
        pod_type = "p1"
        if self.index_name not in pinecone.list_indexes():
            pinecone.create_index(
                self.index_name, dimension=dimension, metric=metric, pod_type=pod_type
            )

        # Connect to the index
        self.index = pinecone.Index(self.index_name)

        # Clear the codefiles namespace
        self.clear_codefiles()
        self.clear_raports()

    def clear_codefiles(self):
        self.index.delete(deleteAll='true', namespace=self.codefiles_namespace)
    
    def clear_raports(self):
        self.index.delete(deleteAll='true', namespace=self.raports_namespace)

    def add_raport(self, raport: Raport):

        enriched_result = {
            "data": str(raport.result)
        }  # This is where you should enrich the result if needed

        vector = get_embedding(
            enriched_result["data"]
        )  # get vector of the actual result extracted from the dictionary

        # Upsert the raport to the raports namespace
        self.index.upsert(
            [(str(raport.raport_id), vector, {"raport": str(raport.name), "result": enriched_result["data"]})],
            namespace=self.raports_namespace
        )

        # Add the raport ID to the list of all raports IDs
        self.all_raports_ids.append(raport.raport_id)

        return enriched_result

    def add_code_file(self, file_name: str, content: str) -> None:

        vector = get_embedding(content)
        content_hash = hashlib.sha256(content.encode()).hexdigest()


        self.index.upsert(
            [(file_name, vector, {"content": content, "hash": content_hash})],
            namespace=self.codefiles_namespace
        )


    def discard(self, item: Union[Raport, CodeFile]):
        # Remove the item from the Pinecone index here
        item_id = f"{item.__class__.__name__.lower()}_{item.raport_id if isinstance(item, Raport) else item.file_name}"
        # self.index.delete([item_id], namespace=namespace)

    def get_raport(self, raport_id: int) -> Raport:
        result_id = f"raport_{raport_id}"

        item = self.index.fetch(
            ids=[result_id], 
            namespace=self.raports_namespace
        )[0]

        return Raport(int(item.id.split('_')[1]), item.metadata['name'], item.metadata['result'])


    def get_codefile(self, file_name: str) -> CodeFile:

        try:
            item = self.index.fetch(
                ids=[file_name], 
                namespace=self.codefiles_namespace
            )[0]


            return CodeFile(item.id, item.metadata['content'])
        
        except TypeError:
            print(f'File {file_name} not found in Pinecone index')
            return None
    
    def get_hash(self, file_name: str) -> str:
        # Fetch the item from the code files namespace
        try:
            # item = self.index.fetch(
            #     ids=[file_name], 
            #     namespace=self.codefiles_namespace
            # )[0]
            # # Return the hash from the metadata
            # return item.metadata.get('hash', None)
            item = self.index.fetch_metadata(file_name, namespace=self.codefiles_namespace)
            return item.get('hash', None)
        
        except KeyError:
            # If the file is not in the Pinecone index, return None
            print(f'File {file_name} not found in Pinecone index')
            return None
        
    def get_relevant_raports(self, query: str, k: int) -> List[Raport]:
        # Get vector representation of the query
        query_vector = get_embedding(query)
        
        relevant_raports = []

        results = self.index.query(
            vector=query_vector,
            top_k=k, 
            namespace=self.raports_namespace,  
            include_metadata=True 
        )
        
        # For each match, create a raport object and add it to the list
        for match in results['matches']:
            relevant_raports.append(Raport(match['metadata']['raport'], result=match['metadata']['result'], score=match['score']))
        
        return relevant_raports

    def get_relevant_codefiles(self, query: str, k: int) -> List[CodeFile]:
        # Get vector representation of the query
        query_vector = get_embedding(query)
        
        relevant_codefiles = []

        results = self.index.query(
            vector=query_vector,
            top_k=k,  
            namespace=self.codefiles_namespace,  
            include_metadata=True 
        )
        
        for match in results['matches']:
            relevant_codefiles.append(CodeFile(match['id'], match['metadata']['content'], match['score']))
        
        return relevant_codefiles
    
    def get_raport(self, name: str) -> Raport:
        # Create result_id from raport_id
        result_id = f"raport_{name}"

        # Fetch the item from the raports namespace
        item = self.index.fetch(
            ids=[result_id], 
            namespace=self.raports_namespace
        )[0]

        # Return a raport object
        return Raport(int(item.id.split('_')[1]), item.metadata['name'], item.metadata['result'])
    
    def get_all_raports(self) -> List[Raport]:
        # Get all raports from the raports namespace
        raports_raw = self.index.fetch(
            ids=self.all_raports_ids,
            namespace=self.raports_namespace
        )

        raports = []
        if raports_raw and hasattr(raports_raw, '__iter__'):
            for raport in raports_raw:
                raports.append(raport(int(raport.raport_id), raport.metadata['name'], raport.metadata['result']))

        return raports

    def upsert_project(self, workspace_path: str = CFG.workspace):
        # Upsert new project files to Pinecone index
        print('Upserting project files to Pinecone index...')
        
        EXCLUDED_DIRS = {'node_modules', 'build'}
        
        project_files = {}
        for root, dirs, files in os.walk(workspace_path):

            dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]

            for file in files:
                file_path = os.path.abspath(os.path.join(root, file))
                try:
                    if 'package' not in file_path:
                        with open(file_path, 'r') as f:
                            content = f.read()
                        project_files[file_path] = content
                except UnicodeDecodeError:
                    print(f"Couldn't read file {file_path}. It might be a binary file.")
        
        for file_path, content in project_files.items():
            print(f'Upserting file {file_path}')
            self.add_code_file(file_path, content)

    def retrieve_project(self) -> dict:
        # Retrieve the entire project data
        # Boilerplate code, replace with retrieving from pinecone
        project_contents = {}

        files = os.listdir(self.dbs.workspace.path)
        for file in files:
            with open(os.path.join(self.dbs.workspace.path, file), 'r') as f:
                project_contents[file] = f.read()

        return project_contents
    
    def update_project(self, workspace_path: str) -> None:
        """Update the project with the new contents of the workspace based on the hash of the files
        Args:
            workspace_path (str): The path to the workspace
        """
        print('Updating project files in Pinecone index...')
        
        # Exclude certain directories
        EXCLUDED_DIRS = {'node_modules', 'build'}

        # Walk through all files in the workspace
        for root, dirs, files in os.walk(workspace_path):
            # Exclude directories
            dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]

            for file in files:
                file_path = os.path.join(root, file)
                try:
                    if 'package' not in file_path:
                        # Compute the hash of the new content
                        with open(file_path, 'r') as f:
                            new_content = f.read()
                        new_hash = hashlib.sha256(new_content.encode()).hexdigest()

                except UnicodeDecodeError:
                    print(f"Couldn't read file {file_path}. It might be a binary file.")
                    continue

                try:
                    current_hash = self.get_hash(file_path)
                except KeyError:
                    current_hash = None
                except AttributeError:
                    current_hash = None

                if new_hash != current_hash:
                    self.add_code_file(file_path, new_content)
                    print(f'Upserted file {file_path}')
