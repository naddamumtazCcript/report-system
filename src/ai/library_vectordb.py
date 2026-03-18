"""
Library Vector DB - ChromaDB storage for admin-uploaded knowledge libraries
Collection: knowledge_library
Separate from client protocol collection (client_{client_id})
"""
import os
import json
import chromadb
from openai import OpenAI
from typing import List, Dict, Optional
from pathlib import Path


def _get_chroma_client():
    db_path = Path(__file__).parent.parent.parent / "vectordb" / "library_db"
    db_path.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(db_path))


def _get_collection():
    client = _get_chroma_client()
    return client.get_or_create_collection("knowledge_library")


def _embed(texts: List[str]) -> List[List[float]]:
    openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    response = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=texts
    )
    return [d.embedding for d in response.data]


def index_library(library_id: str, library_type: str, content: str) -> int:
    """
    Chunk and embed library content into ChromaDB.
    Deletes existing chunks for this library_id before re-indexing.
    Returns number of chunks stored.
    """
    # Remove existing chunks for this library
    delete_library(library_id)

    collection = _get_collection()

    # Split into chunks by paragraph (double newline)
    raw_chunks = [c.strip() for c in content.split('\n\n') if c.strip()]
    # Merge very short chunks with the next one
    chunks = []
    buffer = ""
    for chunk in raw_chunks:
        buffer = f"{buffer}\n\n{chunk}".strip() if buffer else chunk
        if len(buffer) >= 200:
            chunks.append(buffer)
            buffer = ""
    if buffer:
        chunks.append(buffer)

    if not chunks:
        return 0

    embeddings = _embed(chunks)
    ids = [f"{library_id}_chunk_{i}" for i in range(len(chunks))]
    metadatas = [{"library_id": library_id, "library_type": library_type, "chunk_index": i} for i in range(len(chunks))]

    collection.add(
        documents=chunks,
        embeddings=embeddings,
        metadatas=metadatas,
        ids=ids
    )
    return len(chunks)


def delete_library(library_id: str):
    """Delete all chunks for a given library_id from ChromaDB."""
    collection = _get_collection()
    results = collection.get(where={"library_id": library_id})
    if results and results.get('ids'):
        collection.delete(ids=results['ids'])


def query_library(query: str, library_types: Optional[List[str]] = None, n_results: int = 5) -> List[Dict]:
    """
    Query ChromaDB for relevant library chunks.
    Optionally filter by library_type (e.g. ['nutrition', 'supplement']).
    Returns list of {text, library_type, library_id} dicts.
    """
    collection = _get_collection()

    # Check if collection has any documents
    count = collection.count()
    if count == 0:
        return []

    where = {"library_type": {"$in": library_types}} if library_types else None

    query_embedding = _embed([query])[0]

    kwargs = {
        "query_embeddings": [query_embedding],
        "n_results": min(n_results, count),
    }
    if where:
        kwargs["where"] = where

    results = collection.query(**kwargs)

    formatted = []
    if results['documents'] and results['documents'][0]:
        for i, doc in enumerate(results['documents'][0]):
            meta = results['metadatas'][0][i] if results['metadatas'] else {}
            formatted.append({
                "text": doc,
                "library_type": meta.get("library_type", ""),
                "library_id": meta.get("library_id", "")
            })
    return formatted


def list_libraries() -> List[Dict]:
    """List all unique libraries stored in ChromaDB."""
    collection = _get_collection()
    results = collection.get()
    seen = {}
    for meta in (results.get('metadatas') or []):
        lid = meta.get('library_id')
        if lid and lid not in seen:
            seen[lid] = meta.get('library_type', '')
    return [{"library_id": k, "library_type": v} for k, v in seen.items()]
