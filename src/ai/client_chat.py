"""
Client Chat Engine - RAG-based chat with guardrails
"""
import os
from openai import OpenAI
from typing import List, Dict, Optional
from .client_vectordb import ClientVectorDB
from .client_context import ClientContext

class ClientChat:
    """Chat engine for client questions with strict guardrails"""
    
    def __init__(self, client_id: str, protocols_dir):
        self.client_id = client_id
        self.context = ClientContext(client_id, protocols_dir)
        self.vectordb = ClientVectorDB()
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Load client metadata
        self.metadata = self.context.load_metadata()
        self.client_name = self.metadata.get('name', 'Client')
    
    def initialize(self):
        """Index client protocol for RAG"""
        if not self.context.exists():
            raise FileNotFoundError(f"Protocol not found for client {self.client_id}")
        
        protocol = self.context.load_protocol()
        chunks = self.vectordb.index_protocol(self.client_id, protocol)
        return chunks
    
    def chat(self, message: str, conversation_history: Optional[List[Dict]] = None) -> Dict:
        """Process client message and return response"""
        
        # Retrieve relevant protocol sections
        relevant_sections = self.vectordb.search(self.client_id, message, n_results=3)
        
        if not relevant_sections:
            return {
                'response': "I don't have enough information in your protocol to answer that question. Please contact your practitioner for more details.",
                'sources': []
            }
        
        # Generate response with strict prompt
        response = self._generate_response(message, relevant_sections, conversation_history)
        
        return {
            'response': response,
            'sources': [s['metadata'].get('section', 'Unknown') for s in relevant_sections]
        }
    
    def _generate_response(self, message: str, relevant_sections: List[Dict], 
                          conversation_history: Optional[List[Dict]] = None) -> str:
        """Generate response using GPT with strict guardrails"""
        
        # Build context from relevant sections
        context = "\n\n".join([
            f"[{s['metadata'].get('section', 'Section')}]\n{s['text']}"
            for s in relevant_sections
        ])
        
        # System prompt with strict boundaries
        system_prompt = f"""You are a health assistant for {self.client_name}.

STRICT RULES:
1. Answer ONLY based on the protocol sections provided below
2. If the question is NOT related to health, nutrition, or wellness, respond: "I can only help with questions about your health protocol. Please ask about your nutrition plan, supplements, lifestyle recommendations, or health concerns."
3. If the answer is NOT in the protocol, say: "I don't have that information in your protocol. Please contact your practitioner."
4. Do NOT give general health advice beyond the protocol
5. Do NOT make up recommendations
6. Be professional, supportive, and concise
7. Always cite which section you're referencing

PROTOCOL SECTIONS:
{context}

Remember: Only answer from the protocol above. No external knowledge."""

        # Build messages
        messages = [{"role": "system", "content": system_prompt}]
        
        if conversation_history:
            messages.extend(conversation_history)
        
        messages.append({"role": "user", "content": message})
        
        # Call OpenAI
        response = self.openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.3,
            max_tokens=500
        )
        
        return response.choices[0].message.content
