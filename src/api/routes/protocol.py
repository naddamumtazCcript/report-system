"""
Protocol Generation Routes
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
import shutil
import uuid
import json
from typing import List, Optional
from api.config import UPLOAD_DIR, OUTPUT_DIR
from core.pdf_extractor import PDFExtractor
from core.data_mapper import extract_data
from core.template_populator import populate
from core.lab_extractor import extract_lab_report

router = APIRouter()

@router.post("/generate")
async def generate_protocol(
    intake_pdf: UploadFile = File(...),
    lab_pdfs: Optional[List[UploadFile]] = File(None)
):
    """Generate health protocol from intake and optional lab reports"""
    session_id = str(uuid.uuid4())
    
    try:
        # Save intake PDF
        intake_path = UPLOAD_DIR / f"{session_id}_intake.pdf"
        with open(intake_path, "wb") as f:
            shutil.copyfileobj(intake_pdf.file, f)
        
        # Process lab reports if provided
        lab_texts = []
        if lab_pdfs:
            for i, lab_pdf in enumerate(lab_pdfs):
                lab_path = UPLOAD_DIR / f"{session_id}_lab_{i}.pdf"
                with open(lab_path, "wb") as f:
                    shutil.copyfileobj(lab_pdf.file, f)
                
                lab_text_path = extract_lab_report(lab_path)
                with open(lab_text_path, 'r') as f:
                    lab_texts.append(f.read())
        
        # Extract intake text
        extractor = PDFExtractor(str(intake_path))
        intake_text = extractor.extract_text()
        
        text_file = UPLOAD_DIR / f"{session_id}_text.txt"
        with open(text_file, 'w') as f:
            f.write(intake_text)
        
        # Extract structured data
        client_data = extract_data(str(text_file))
        
        json_file = UPLOAD_DIR / f"{session_id}_data.json"
        with open(json_file, 'w') as f:
            json.dump(client_data, f, indent=2)
        
        # Generate protocol
        from pathlib import Path
        template_path = Path(__file__).parent.parent.parent.parent / "templates" / "ProtocolTemplate.md"
        output_path = OUTPUT_DIR / f"{session_id}_protocol.md"
        
        populate(template_path, str(json_file), str(output_path))
        
        return {
            "status": "success",
            "session_id": session_id,
            "protocol_file": str(output_path),
            "lab_reports_processed": len(lab_texts) if lab_pdfs else 0,
            "download_url": f"/api/protocol/download/{session_id}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/download/{session_id}")
async def download_protocol(session_id: str):
    """Download generated protocol"""
    protocol_path = OUTPUT_DIR / f"{session_id}_protocol.md"
    
    if not protocol_path.exists():
        raise HTTPException(status_code=404, detail="Protocol not found")
    
    return FileResponse(
        path=protocol_path,
        filename=f"protocol_{session_id}.md",
        media_type="text/markdown"
    )
