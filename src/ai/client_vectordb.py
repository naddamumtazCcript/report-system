"""
Client Vector Database - Index client protocols for RAG
"""
import json
import chromadb
from openai import OpenAI
import os
from pathlib import Path
from typing import List, Dict

class ClientVectorDB:
    """Manages client-specific protocol indexing in ChromaDB"""
    
    def __init__(self, db_path: Path = Path("vectordb/client_db")):
        self.client = chromadb.PersistentClient(path=str(db_path))
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using OpenAI"""
        response = self.openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding
    
    def index_protocol(self, client_id: str, protocol_content):
        """Index client protocol (dict or JSON string) into ChromaDB"""
        collection_name = f"client_{client_id}"
        
        try:
            self.client.delete_collection(collection_name)
        except:
            pass
        
        collection = self.client.create_collection(collection_name)
        
        data = protocol_content if isinstance(protocol_content, dict) else json.loads(protocol_content)
        chunks = self._chunk_protocol(data)
        
        # Add to collection with pre-generated embeddings
        collection.add(
            documents=[chunk['text'] for chunk in chunks],
            embeddings=[self._generate_embedding(chunk['text']) for chunk in chunks],
            metadatas=[chunk['metadata'] for chunk in chunks],
            ids=[f"{client_id}_{i}" for i in range(len(chunks))]
        )
        
        return len(chunks)
    
    def search(self, client_id: str, query: str, n_results: int = 3) -> List[Dict]:
        """Search client protocol for relevant content"""
        collection_name = f"client_{client_id}"
        
        try:
            collection = self.client.get_collection(collection_name)
        except:
            return []
        
        results = collection.query(
            query_embeddings=[self._generate_embedding(query)],
            n_results=n_results
        )
        
        # Format results
        formatted = []
        if results['documents'] and results['documents'][0]:
            for i, doc in enumerate(results['documents'][0]):
                formatted.append({
                    'text': doc,
                    'metadata': results['metadatas'][0][i] if results['metadatas'] else {}
                })
        
        return formatted
    
    def _chunk_protocol(self, data: dict) -> List[Dict]:
        """Split protocol JSON into searchable chunks — one chunk per top-level key"""
        import json as _json
        chunks = []
        for key, value in data.items():
            text = f"{key}: {_json.dumps(value) if isinstance(value, (dict, list)) else value}"
            if text.strip():
                chunks.append({'text': text, 'metadata': {'section': key}})
        return chunks
