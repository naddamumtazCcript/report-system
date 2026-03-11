"""
Protocol Generation Routes
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
import shutil
import uuid
import json
from typing import List, Optional
from api.config import UPLOAD_DIR, OUTPUT_DIR
from core.pdf_extractor import PDFExtractor
from core.data_mapper import extract_data
from core.template_populator import populate
from core.template_populator_json import populate_json
from core.lab_extractor import extract_lab_report
from ai.gemini_lab_extractor import analyze_lab_with_gemini
from core.schema import LabData

router = APIRouter()

@router.post("/generate")
async def generate_protocol(
    intake_pdf: UploadFile = File(...),
    lab_pdfs: Optional[List[UploadFile]] = File(None),
    doc_types: Optional[str] = Form(None),
    libraries: Optional[str] = Form(None),
    template: Optional[str] = Form(None),
    user_id: Optional[str] = Form(None),
    client_id: Optional[str] = Form(None)
):
    """
    Generate health protocol from intake and optional lab reports.
    
    Supports two modes:
    1. File-based (legacy): Uses templates/libraries from disk
    2. JSON-based (new): Accepts libraries and template as JSON objects
    
    JSON mode is used when 'libraries' and 'template' parameters are provided.
    """
    session_id = str(uuid.uuid4())
    
    try:
        # Save intake PDF
        intake_path = UPLOAD_DIR / f"{session_id}_intake.pdf"
        with open(intake_path, "wb") as f:
            shutil.copyfileobj(intake_pdf.file, f)
        
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
        
        # Process lab reports if provided
        lab_data = None
        if lab_pdfs:
            if doc_types:
                # JSON mode with explicit doc types
                doc_types_list = json.loads(doc_types)
                if len(lab_pdfs) != len(doc_types_list):
                    raise HTTPException(
                        status_code=400,
                        detail="Number of lab PDFs must match number of doc_types"
                    )
                
                all_reports = []
                for i, (lab_pdf, doc_type) in enumerate(zip(lab_pdfs, doc_types_list)):
                    lab_path = UPLOAD_DIR / f"{session_id}_lab_{i}_{doc_type}.pdf"
                    with open(lab_path, "wb") as f:
                        shutil.copyfileobj(lab_pdf.file, f)
                    
                    lab_result = analyze_lab_with_gemini(str(lab_path))
                    if lab_result and lab_result.reports:
                        all_reports.extend(lab_result.reports)
                
                lab_data = LabData(reports=all_reports, summary="") if all_reports else None
            else:
                # Legacy mode - auto-detect
                lab_texts = []
                for i, lab_pdf in enumerate(lab_pdfs):
                    lab_path = UPLOAD_DIR / f"{session_id}_lab_{i}.pdf"
                    with open(lab_path, "wb") as f:
                        shutil.copyfileobj(lab_pdf.file, f)
                    
                    lab_text_path = extract_lab_report(lab_path)
                    with open(lab_text_path, 'r') as f:
                        lab_texts.append(f.read())
        
        output_path = OUTPUT_DIR / f"{session_id}_protocol.md"
        
        # Check if JSON mode or file mode
        if libraries and template:
            # JSON mode
            libraries_json = json.loads(libraries)
            template_json = json.loads(template)
            
            populate_json(
                template_json=template_json,
                client_data=client_data,
                libraries_json=libraries_json,
                output_path=str(output_path),
                lab_data=lab_data,
                user_id=user_id,
                client_id=client_id
            )
            
            return {
                "status": "success",
                "session_id": session_id,
                "user_id": user_id,
                "client_id": client_id,
                "protocol_file": str(output_path),
                "lab_reports_processed": len(lab_pdfs) if lab_pdfs else 0,
                "download_url": f"/api/protocol/download/{session_id}"
            }
        else:
            # File mode (legacy)
            from pathlib import Path
            template_path = Path(__file__).parent.parent.parent.parent / "templates" / "ProtocolTemplate.md"
            
            populate(template_path, str(json_file), str(output_path), lab_data)
            
            return {
                "status": "success",
                "session_id": session_id,
                "protocol_file": str(output_path),
                "lab_reports_processed": len(lab_pdfs) if lab_pdfs else 0,
                "download_url": f"/api/protocol/download/{session_id}"
            }
        
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON format: {e}")
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
