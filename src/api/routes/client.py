"""
Client Chat API Routes
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
from api.config import CLIENT_PROTOCOLS_DIR
from ai.client_chat import ClientChat
from ai.client_context import ClientContext

router = APIRouter(prefix="/client", tags=["client"])

class ChatRequest(BaseModel):
    client_id: str
    message: str
    conversation_history: Optional[List[Dict]] = None

class ChatResponse(BaseModel):
    response: str
    sources: List[str]

class InitializeRequest(BaseModel):
    client_id: str
    protocol_content: str
    metadata: Optional[Dict] = None

@router.post("/initialize")
def initialize_client(request: InitializeRequest):
    """Initialize client protocol for chat"""
    try:
        
        # Save protocol
        context = ClientContext(request.client_id, CLIENT_PROTOCOLS_DIR)
        context.save_protocol(request.protocol_content, request.metadata)
        
        # Index for chat
        chat = ClientChat(request.client_id, CLIENT_PROTOCOLS_DIR)
        chunks = chat.initialize()
        
        return {
            "status": "success",
            "client_id": request.client_id,
            "chunks_indexed": chunks
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat", response_model=ChatResponse)
def chat_with_client(request: ChatRequest):
    """Chat with client about their protocol"""
    # Check if client exists first
    context = ClientContext(request.client_id, CLIENT_PROTOCOLS_DIR)
    if not context.exists():
        raise HTTPException(status_code=404, detail=f"Protocol not found for client {request.client_id}")
    
    try:
        chat = ClientChat(request.client_id, CLIENT_PROTOCOLS_DIR)
        result = chat.chat(request.message, request.conversation_history)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/protocol/{client_id}")
def get_client_protocol(client_id: str):
    """Get client protocol"""
    try:
        context = ClientContext(client_id, CLIENT_PROTOCOLS_DIR)
        
        if not context.exists():
            raise HTTPException(status_code=404, detail=f"Protocol not found for client {client_id}")
        
        protocol = context.load_protocol()
        metadata = context.load_metadata()
        
        return {
            "client_id": client_id,
            "protocol": protocol,
            "metadata": metadata
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
