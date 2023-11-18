from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from config import Config

CFG = Config()

# This class represents a simple database that stores its data as files in a directory.
class DB:
    """A simple key-value store, where keys are filenames and values are file contents."""

    def __init__(self, path):
        self.path = Path(path).absolute()

        self.path.mkdir(parents=True, exist_ok=True)

    def __contains__(self, key):
        return (self.path / key).is_file()

    def __getitem__(self, key):
        full_path: Path = self.path / key

        if not full_path.is_file():
            raise KeyError(f"File '{key}' could not be found in '{self.path}'")
        with full_path.open("r", encoding="utf-8") as f:
            return f.read()

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def __setitem__(self, key, val):
        full_path: Path = self.path / key
        full_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            if isinstance(val, str):
                full_path.write_text(val, encoding="utf-8")
                print(f"Wrote to '{full_path}'")
            else:
                # If val is neither a string nor bytes, raise an error.
                raise TypeError("val must be either a str or bytes")
        except IsADirectoryError:
            print(f"Could not write to '{full_path}'. It is a directory.")


# dataclass for all dbs:
@dataclass
class DBs:
    prompts: DB
    workspace: DB

def create_dbs(project: str = None) -> DBs:
    """Create the DBs for the project"""
    return DBs(workspace=DB(f'{project}_gptester'),
               prompts=DB(Path(__file__).parent / "prompts"))