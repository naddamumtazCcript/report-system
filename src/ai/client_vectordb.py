"""
Client Vector Database - Index client protocols for RAG
"""
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
    
    def index_protocol(self, client_id: str, protocol_content: str):
        """Index client protocol into ChromaDB"""
        collection_name = f"client_{client_id}"
        
        # Delete existing collection if exists
        try:
            self.client.delete_collection(collection_name)
        except:
            pass
        
        # Create new collection
        collection = self.client.create_collection(collection_name)
        
        # Split into chunks by section
        chunks = self._chunk_protocol(protocol_content)
        
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
    
    def _chunk_protocol(self, content: str) -> List[Dict]:
        """Split protocol into searchable chunks by section"""
        chunks = []
        current_section = "header"
        current_content = []
        
        for line in content.split('\n'):
            if line.startswith('## '):
                # Save previous section
                if current_content:
                    text = '\n'.join(current_content).strip()
                    if text:
                        chunks.append({
                            'text': text,
                            'metadata': {'section': current_section}
                        })
                # Start new section
                current_section = line.replace('## ', '').strip()
                current_content = [line]
            else:
                current_content.append(line)
        
        # Save last section
        if current_content:
            text = '\n'.join(current_content).strip()
            if text:
                chunks.append({
                    'text': text,
                    'metadata': {'section': current_section}
                })
        
        return chunks
