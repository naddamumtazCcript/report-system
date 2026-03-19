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

        # Build search query: include only the immediately prior turn so a topic
        # switch doesn't drag stale context into the vector search
        search_query = message
        if conversation_history and len(conversation_history) >= 2:
            last_user = conversation_history[-2].get("content", "")
            search_query = f"{last_user} {message}"

        # Retrieve relevant protocol sections
        relevant_sections = self.vectordb.search(self.client_id, search_query, n_results=4)

        if not relevant_sections:
            return {
                'response': "I don't have enough information in your protocol to answer that question. Please contact your practitioner for more details.",
                'sources': []
            }

        # If a list section is partially retrieved, pull all chunks from that section
        relevant_sections = self._expand_list_sections(relevant_sections)

        # Generate response with strict prompt
        response = self._generate_response(message, relevant_sections, conversation_history)

        return {
            'response': response,
            'sources': list(dict.fromkeys(s['metadata'].get('section', 'Unknown') for s in relevant_sections))
        }

    def _expand_list_sections(self, sections: List[Dict]) -> List[Dict]:
        """If any retrieved chunk belongs to a list section, fetch all chunks from that section."""
        hit_sections = {s['metadata'].get('section') for s in sections}
        expanded = list(sections)
        seen_texts = {s['text'] for s in sections}

        for section_name in hit_sections:
            # Only expand if the section name looks like a list key (supplements, goals, etc.)
            all_in_section = self.vectordb.get_by_section(self.client_id, section_name)
            if len(all_in_section) > 1:  # it's a multi-chunk section
                for chunk in all_in_section:
                    if chunk['text'] not in seen_texts:
                        expanded.append(chunk)
                        seen_texts.add(chunk['text'])

        return expanded
    
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
2. If the retrieved protocol sections do not contain enough information to answer the question, say: "I don't have that specific information in your protocol. Please contact your practitioner."
3. If the question is completely unrelated to health, wellness, or the client's protocol (e.g. movies, sports, coding), respond: "I can only help with questions about your health protocol."
4. Do NOT give general health advice beyond what is in the protocol
5. Do NOT make up recommendations not present in the protocol
6. Be professional, supportive, and concise
7. Always cite which section you're referencing

PROTOCOL SECTIONS:
{context}

Remember: If the answer is in the protocol sections above, use it. Only deflect if the sections genuinely don't contain the answer."""

        # Build messages
        messages = [{"role": "system", "content": system_prompt}]
        
        if conversation_history:
            messages.extend(conversation_history[-10:])  # cap at last 10 messages
        
        messages.append({"role": "user", "content": message})
        
        # Call OpenAI
        response = self.openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.3,
            max_tokens=500
        )
        
        return response.choices[0].message.content
