"""Configuration class to store the state of bools for different scripts access."""
import os
from dotenv import load_dotenv
import abc

load_dotenv(override=True, verbose=True)

class Singleton(abc.ABCMeta, type):
    """
    Singleton metaclass for ensuring only one instance of a class.
    """

    _instances = {}

    def __call__(cls, *args, **kwargs):
        """Call method for the singleton metaclass."""
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class Config(metaclass=Singleton):
    """
    Configuration class to store the state of bools for different scripts access.
    """

    def __init__(self) -> None:
        """Initialize the Config class"""
        self.debug_mode = False
        self.speak_mode = False
        self.workspace = os.getenv("WORKSPACE_DIRECTORY", "workspace")
        self.restart_limit = int(os.getenv("RESTART_LIMIT", "3"))
        self.llm_model = os.getenv("LLM_MODEL", "gpt-4")
        self.token_limit = int(os.getenv("TOKEN_LIMIT", 4097))
        self.browse_chunk_max_length = int(os.getenv("BROWSE_CHUNK_MAX_LENGTH", 3000))
        self.browse_spacy_language_model = os.getenv(
            "BROWSE_SPACY_LANGUAGE_MODEL", "en_core_web_sm"
        )

        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.temperature = float(os.getenv("TEMPERATURE", "0"))
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4")
        self.execute_local_commands = (
            os.getenv("EXECUTE_LOCAL_COMMANDS", "False") == "True"
        )
        self.restrict_to_workspace = (
            os.getenv("RESTRICT_TO_WORKSPACE", "True") == "True"
        )

        self.pinecone_api_key = os.getenv("PINECONE_API_KEY")
        # assert self.pinecone_api_key, "Missing PINECONE_API_KEY environment variable"
        self.pinecone_region = os.getenv("PINECONE_ENVIRONMENT", "")
        # assert (
        #     self.pinecone_region
        # ), "PINECONE_ENVIRONMENT environment variable is missing from .env"

        self.pinecone_index = os.getenv("PINECONE_INDEX", "")
        # assert self.pinecone_index, "PINECONE_INDEX environment variable is missing from .env"

        self.redis_host = os.getenv("REDIS_HOST", "localhost")
        self.redis_port = os.getenv("REDIS_PORT", "6379")
        self.redis_password = os.getenv("REDIS_PASSWORD", "")
        self.wipe_redis_on_start = os.getenv("WIPE_REDIS_ON_START", "True") == "True"
        # Note that indexes must be created on db 0 in redis, this is not configurable.

        self.memory_backend = os.getenv("MEMORY_BACKEND", "local")
        # Initialize the OpenAI API client
        # raise Exception("The 'openai.api_key' option isn't read in the client API. You will need to pass it when you instantiate the client, e.g. 'OpenAI(api_key=self.openai_api_key)'")

    def set_llm_model(self, value: str) -> None:
        """Set the smart LLM model value."""
        self.llm_model = value

    def set_token_limit(self, value: int) -> None:
        """Set the fast token limit value."""
        self.fast_token_limit = value

    def set_browse_chunk_max_length(self, value: int) -> None:
        """Set the browse_website command chunk max length value."""
        self.browse_chunk_max_length = value

    def set_openai_api_key(self, value: str) -> None:
        """Set the OpenAI API key value."""
        self.openai_api_key = value

    def set_pinecone_api_key(self, value: str) -> None:
        """Set the Pinecone API key value."""
        self.pinecone_api_key = value

    def set_pinecone_region(self, value: str) -> None:
        """Set the Pinecone region value."""
        self.pinecone_region = value

    def set_debug_mode(self, value: bool) -> None:
        """Set the debug mode value."""
        self.debug_mode = value

