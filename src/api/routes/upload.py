"""Upload endpoint"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import uuid
from datetime import datetime
from ..config import UPLOAD_DIR

router = APIRouter()

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload PDF questionnaire"""
    try:
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        
        job_id = str(uuid.uuid4())[:8]
        file_path = UPLOAD_DIR / f"{job_id}_{file.filename}"
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        return JSONResponse(
            status_code=200,
            content={
                "job_id": job_id,
                "filename": file.filename,
                "file_size": len(content),
                "status": "uploaded",
                "uploaded_at": datetime.now().isoformat(),
                "message": "File uploaded successfully"
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
