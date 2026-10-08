import os
import uuid
import logging
from typing import List, Dict, Any, Optional, Union, Tuple

from backend.config import settings

logger = logging.getLogger(__name__)

# Fallback in-memory vector store implementation
class SimpleInMemoryVectorStore:
    def __init__(self):
        self.vectors: List[Tuple[str, List[float], Dict[str, Any], str]] = []  # (id, embedding, metadata, document_text)

    def add(self, ids: List[str], embeddings: List[List[float]], metadatas: List[Dict[str, Any]], documents: List[str]):
        for i, doc_id in enumerate(ids):
            self.vectors.append((doc_id, embeddings[i], metadatas[i], documents[i]))

    def get_all(self):
        return self.vectors


_global_in_memory_store = SimpleInMemoryVectorStore()
_embedding_model_instance = None


def _get_embedding(text: str) -> List[float]:
    """
    Generate vector embedding using HuggingFace API (if API key provided),
    sentence-transformers locally, or a deterministic hash fallback.
    """
    global _embedding_model_instance
    if not text:
        return [0.0] * 384

    # 1. Try Hugging Face Inference API if HUGGINGFACE_API_KEY is set
    hf_api_key = settings.HUGGINGFACE_API_KEY
    if hf_api_key:
        try:
            import requests
            model_name = settings.HUGGINGFACE_EMBEDDING_MODEL or "sentence-transformers/all-MiniLM-L6-v2"
            url = f"https://api-inference.huggingface.co/pipeline/feature-extraction/{model_name}"
            headers = {"Authorization": f"Bearer {hf_api_key}"}
            response = requests.post(url, headers=headers, json={"inputs": text, "options": {"wait_for_model": True}}, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                # API returns list of floats or list of token vectors
                if isinstance(data, list):
                    if len(data) > 0 and isinstance(data[0], list):
                        # Mean pooling over token embeddings
                        token_vecs = data[0]
                        dim = len(token_vecs[0]) if isinstance(token_vecs[0], list) else len(token_vecs)
                        if isinstance(token_vecs[0], list):
                            avg_vec = [sum(col) / len(token_vecs) for col in zip(*token_vecs)]
                            return avg_vec
                        return token_vecs
                    elif isinstance(data[0], (int, float)):
                        return data
                logger.info("Successfully fetched embedding from HuggingFace API")
            else:
                logger.warning(f"HuggingFace API returned status code {response.status_code}: {response.text}")
        except Exception as e:
            logger.warning(f"HuggingFace API call failed: {e}. Falling back to local model.")

    # 2. Try local SentenceTransformers model
    try:
        if _embedding_model_instance is None:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL_NAME}")
            _embedding_model_instance = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
        
        embedding = _embedding_model_instance.encode(text).tolist()
        return embedding
    except Exception as e:
        logger.warning(f"SentenceTransformer embedding generation failed: {e}. Using deterministic hash vector fallback.")
        import hashlib
        h = hashlib.sha256(text.encode('utf-8')).digest()
        floats = []
        for i in range(384):
            byte_val = h[i % len(h)]
            floats.append((byte_val / 127.5) - 1.0)
        return floats


def _get_pinecone_index():
    """Get Pinecone index instance if PINECONE_API_KEY is configured."""
    api_key = settings.PINECONE_API_KEY
    if not api_key:
        return None

    try:
        from pinecone import Pinecone
        pc = Pinecone(api_key=api_key)
        index_name = settings.PINECONE_INDEX_NAME or "claimpilot-index"
        index = pc.Index(index_name)
        return index
    except Exception as e:
        logger.warning(f"Pinecone initialization failed: {e}")
        return None


def _get_chroma_collection():
    """Get or create ChromaDB collection if chromadb is available and configured."""
    if settings.VECTOR_DB_TYPE.lower() not in ["chroma", "all"]:
        return None

    try:
        import chromadb
        if settings.VECTOR_DB_PATH == ":memory:":
            client = chromadb.Client()
        else:
            os.makedirs(settings.VECTOR_DB_PATH, exist_ok=True)
            client = chromadb.PersistentClient(path=settings.VECTOR_DB_PATH)
        
        collection = client.get_or_create_collection(name="claimpilot_embeddings")
        return collection
    except Exception as e:
        logger.warning(f"ChromaDB initialization failed: {e}.")
        return None


def _store_vectors(ids: List[str], embeddings: List[List[float]], metadatas: List[Dict[str, Any]], documents: List[str]) -> str:
    """
    Stores vectors using Pinecone (if configured/active), ChromaDB, or fallback in-memory store.
    """
    # 1. Try Pinecone if VECTOR_DB_TYPE is pinecone or PINECONE_API_KEY is set
    pinecone_index = _get_pinecone_index()
    if pinecone_index is not None:
        try:
            vectors_to_upsert = []
            for i in range(len(ids)):
                meta = dict(metadatas[i])
                meta["text"] = documents[i]  # Preserve original text in payload
                vectors_to_upsert.append({
                    "id": ids[i],
                    "values": embeddings[i],
                    "metadata": meta
                })
            pinecone_index.upsert(vectors=vectors_to_upsert)
            logger.info(f"Successfully stored {len(ids)} vectors in Pinecone index '{settings.PINECONE_INDEX_NAME}'")
            return "pinecone"
        except Exception as e:
            logger.error(f"Pinecone upsert failed: {e}. Falling back to secondary vector storage.")

    # 2. Try ChromaDB
    collection = _get_chroma_collection()
    if collection is not None:
        try:
            collection.upsert(
                ids=ids,
                embeddings=embeddings,
                metadatas=metadatas,
                documents=documents
            )
            logger.info(f"Successfully stored {len(ids)} vectors in ChromaDB")
            return "chroma"
        except Exception as e:
            logger.error(f"ChromaDB upsert failed: {e}. Falling back to in-memory store.")

    # 3. Fallback in-memory store
    _global_in_memory_store.add(ids, embeddings, metadatas, documents)
    logger.info(f"Stored {len(ids)} vectors in in-memory vector store")
    return "memory"


def _chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """Split long document text into overlapping chunks."""
    if not text or len(text) <= chunk_size:
        return [text] if text else []

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        if end >= len(text):
            break
        start += (chunk_size - overlap)
    return chunks


def store_document_embeddings(
    processed_document: Dict[str, Any],
    text_chunks: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Responsibilities:
    1. Receive processed document text.
    2. Split long documents into appropriate chunks.
    3. Generate embeddings using configured embedding model.
    4. Store embeddings & metadata in vector database.
    5. Preserve original text alongside every vector.
    """
    doc_id = processed_document.get("document_id", f"doc_{uuid.uuid4().hex[:8]}")
    doc_name = processed_document.get("filename") or processed_document.get("source", "document")
    full_text = processed_document.get("text", "")

    if not full_text and not text_chunks:
        logger.warning(f"No text content found for document {doc_id}")
        return {"status": "skipped", "stored_count": 0, "document_id": doc_id}

    chunks = text_chunks if text_chunks is not None else _chunk_text(
        full_text, 
        chunk_size=settings.MAX_CHUNK_SIZE, 
        overlap=settings.CHUNK_OVERLAP
    )

    ids = []
    embeddings = []
    metadatas = []
    documents = []

    for i, chunk in enumerate(chunks):
        chunk_id = f"chunk_{doc_id}_{i+1:03d}"
        vec = _get_embedding(chunk)
        
        meta = {
            "document_id": doc_id,
            "document_name": doc_name,
            "chunk_id": chunk_id,
            "chunk_index": i,
            "type": "document",
            "source": doc_name
        }

        ids.append(chunk_id)
        embeddings.append(vec)
        metadatas.append(meta)
        documents.append(chunk)

    target_store = _store_vectors(ids, embeddings, metadatas, documents)

    return {
        "status": "success",
        "stored_count": len(ids),
        "document_id": doc_id,
        "chunk_ids": ids,
        "store": target_store
    }


def store_evidence_embeddings(extracted_evidence_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Responsibilities:
    1. Receive structured evidence extracted by Gemma.
    2. Generate embeddings for the evidence text.
    3. Store them in the vector database with metadata.
    4. Preserve metadata (evidence_id, document_id, type="evidence", source).
    """
    if not extracted_evidence_list:
        return {"status": "skipped", "stored_count": 0}

    ids = []
    embeddings = []
    metadatas = []
    documents = []

    for item in extracted_evidence_list:
        ev_id = item.get("evidence_id") or f"evidence_{uuid.uuid4().hex[:8]}"
        ev_text = item.get("text", "")
        doc_id = item.get("document_id", "unknown_doc")
        source = item.get("source", "unknown_source")

        if not ev_text.strip():
            continue

        vec = _get_embedding(ev_text)
        meta = {
            "evidence_id": ev_id,
            "document_id": doc_id,
            "type": "evidence",
            "source": source,
            "confidence": str(item.get("confidence", 1.0))
        }

        ids.append(ev_id)
        embeddings.append(vec)
        metadatas.append(meta)
        documents.append(ev_text)

    if not ids:
        return {"status": "skipped", "stored_count": 0}

    target_store = _store_vectors(ids, embeddings, metadatas, documents)

    return {
        "status": "success",
        "stored_count": len(ids),
        "evidence_ids": ids,
        "store": target_store
    }
