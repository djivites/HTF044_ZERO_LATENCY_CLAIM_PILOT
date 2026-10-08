<<<<<<< HEAD
DOC_RELIABILITY = {
    "inspection_report": 1.0,
    "warranty_terms": 0.95,
    "contract": 0.95,
    "invoice": 0.9,
    "receipt": 0.9,
    "company_response": 0.7,
    "photo": 0.6,
    "email_thread": 0.6,
    "other": 0.4,
}
DEFAULT_RELIABILITY = 0.4
SEVERITY_WEIGHT = {"high": 1.0, "medium": 0.6, "low": 0.3}
SEVERITY_RANK = {"high": 0, "medium": 1, "low": 2}
SCORE_WEIGHTS = {"support": 0.35, "contradiction": 0.30, "completeness": 0.20, "timeline": 0.15}
CONTRADICTION_SATURATION = 3.0
SCORE_BANDS = [(80, "Strong"), (60, "Moderate"), (40, "Mixed"), (0, "Weak")]
MAX_FINDINGS_IN_LETTER = 5
MAX_LETTER_RETRIES = 2
=======
import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file if available
load_dotenv()

class Settings:
    # Gemma AI configuration
    GEMMA_API_KEY: str = os.getenv("GEMMA_API_KEY", "")
    GEMMA_MODEL_NAME: str = os.getenv("GEMMA_MODEL_NAME", "gemma-4-31b-it")
    GEMMA_API_URL: Optional[str] = os.getenv("GEMMA_API_URL", None)

    # Embedding & Vector Database configuration
    # 1024-dim model matching the Pinecone index dimension
    EMBEDDING_MODEL_NAME: str = os.getenv("EMBEDDING_MODEL_NAME", "BAAI/bge-large-en-v1.5")
    HUGGINGFACE_API_KEY: str = os.getenv("HUGGINGFACE_API_KEY", "")
    HUGGINGFACE_EMBEDDING_MODEL: str = os.getenv("HUGGINGFACE_EMBEDDING_MODEL", "BAAI/bge-large-en-v1.5")
    PINECONE_DIMENSION: int = int(os.getenv("PINECONE_DIMENSION", "1024"))
    PINECONE_API_KEY: str = os.getenv("PINECONE_API_KEY", "")
    PINECONE_INDEX_NAME: str = os.getenv("PINECONE_INDEX_NAME", "claimpilot-index")
    PINECONE_ENVIRONMENT: str = os.getenv("PINECONE_ENVIRONMENT", "us-east-1")
    VECTOR_DB_TYPE: str = os.getenv("VECTOR_DB_TYPE", "pinecone")
    VECTOR_DB_PATH: str = os.getenv("VECTOR_DB_PATH", "./vector_db_data")

    # Document upload / processing config
    MAX_CHUNK_SIZE: int = int(os.getenv("MAX_CHUNK_SIZE", "500"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "50"))

settings = Settings()
>>>>>>> feature/claimpilot-core-services
