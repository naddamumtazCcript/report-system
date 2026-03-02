"""
Knowledge Base Library Management Routes
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from datetime import datetime
import shutil
from api.config import KB_DIR, SYSTEM_FILES, MAX_FILE_SIZE
from utils.pdf_to_text_converter import convert_pdf_to_text, convert_knowledge_base_pdfs

router = APIRouter()

@router.post("/upload")
async def upload_library(file: UploadFile = File(...)):
    """Upload PDF to knowledge base and auto-convert to text"""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files allowed")
    
    safe_filename = "".join(c for c in file.filename if c.isalnum() or c in ('_', '-', '.')).rstrip()
    if not safe_filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")
    
    try:
        pdf_path = KB_DIR / safe_filename
        with open(pdf_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        
        text_path = convert_pdf_to_text(pdf_path)
        
        return {
            "status": "success",
            "message": "Library uploaded and converted",
            "filename": safe_filename,
            "text_file": text_path.name,
            "size": f"{file_size / 1024:.1f}KB"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list")
async def list_libraries():
    """List all available libraries for selection"""
    try:
        libraries = []
        for file_path in KB_DIR.glob("*.md"):
            if file_path.is_file():
                libraries.append({
                    "name": file_path.stem,
                    "filename": file_path.name,
                    "type": "markdown"
                })
        
        # Add .txt files as well
        for file_path in KB_DIR.glob("*.txt"):
            if file_path.is_file() and not any(lib['name'] == file_path.stem for lib in libraries):
                libraries.append({
                    "name": file_path.stem,
                    "filename": file_path.name,
                    "type": "text"
                })
        
        return {
            "libraries": sorted(libraries, key=lambda x: x['name'])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{filename}")
async def get_library(filename: str):
    """Get content of a library file"""
    safe_filename = "".join(c for c in filename if c.isalnum() or c in ('_', '-', '.')).rstrip()
    
    txt_path = KB_DIR / safe_filename.replace('.pdf', '.txt')
    pdf_path = KB_DIR / safe_filename
    
    if txt_path.exists():
        with open(txt_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return {
            "status": "success",
            "filename": txt_path.name,
            "content": content,
            "size": f"{len(content)} characters"
        }
    elif pdf_path.exists():
        return FileResponse(path=pdf_path, filename=safe_filename, media_type="application/pdf")
    else:
        raise HTTPException(status_code=404, detail="File not found")

@router.delete("/{filename}")
async def delete_library(filename: str):
    """Delete a library file (both PDF and text)"""
    safe_filename = "".join(c for c in filename if c.isalnum() or c in ('_', '-', '.')).rstrip()
    
    if any(sys_file in safe_filename for sys_file in SYSTEM_FILES):
        raise HTTPException(status_code=403, detail="Cannot delete system files")
    
    try:
        deleted = []
        
        pdf_path = KB_DIR / safe_filename
        if pdf_path.exists():
            pdf_path.unlink()
            deleted.append(safe_filename)
        
        txt_filename = safe_filename.replace('.pdf', '.txt') if safe_filename.endswith('.pdf') else f"{safe_filename}.txt"
        txt_path = KB_DIR / txt_filename
        if txt_path.exists():
            txt_path.unlink()
            deleted.append(txt_filename)
        
        if not deleted:
            raise HTTPException(status_code=404, detail="File not found")
        
        return {
            "status": "success",
            "message": "Library deleted",
            "deleted_files": deleted
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/refresh")
async def refresh_libraries():
    """Re-convert all PDFs in knowledge base to text"""
    try:
        converted = convert_knowledge_base_pdfs()
        return {
            "status": "success",
            "message": "Knowledge base refreshed",
            "files_converted": len(converted),
            "converted_files": converted
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
