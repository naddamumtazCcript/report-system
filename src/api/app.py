"""
Main API Application - Merged
"""
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import library, upload, generate, client, practitioner, lab_extraction, pdf_to_json

app = FastAPI(
    title="Be Balanced Protocol API",
    version="1.0.0",
    description="API for protocol generation and knowledge base management"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Knowledge Base Management
app.include_router(library.router, prefix="/api/library", tags=["Knowledge Base"])

# Protocol Generation
app.include_router(upload.router, prefix="/api", tags=["Upload"])
app.include_router(generate.router, prefix="/api", tags=["Generate"])

# Client Chat
app.include_router(client.router, prefix="/api", tags=["Client Chat"])

# Comprehensive Protocol Generation
# app.include_router(generate_comprehensive.router) - removed, use /generate-from-json instead

# Practitioner Agent
app.include_router(practitioner.router, prefix="/api", tags=["Practitioner Agent"])

# Lab Extraction
app.include_router(lab_extraction.router, prefix="/api", tags=["Lab Extraction"])

# PDF to JSON Converter
app.include_router(pdf_to_json.router, prefix="/api", tags=["PDF to JSON"])

@app.get("/")
async def root():
    """Health check"""
    return {"status": "online", "service": "Be Balanced Protocol API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
