"""Lab extraction endpoint - Extract structured data from lab report PDFs"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
import time
import uuid
import json
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from ..config import UPLOAD_DIR, OUTPUT_DIR
from ai.gemini_lab_extractor import detect_lab_type, extract_dutch, extract_gi_map, extract_bloodwork

router = APIRouter()

@router.post("/labs/extract")
async def extract_labs(files: List[UploadFile] = File(...)):
    """
    Extract structured data from 1-3 lab report PDFs
    
    Supports:
    - DUTCH Complete (hormone testing)
    - GI-MAP (gut health)
    - Functional Bloodwork Panel
    """
    start_time = time.time()
    
    # Validate file count
    if len(files) == 0:
        raise HTTPException(status_code=400, detail="No files provided")
    if len(files) > 3:
        raise HTTPException(status_code=400, detail="Maximum 3 lab reports allowed")
    
    # Generate job ID
    job_id = str(uuid.uuid4())
    logger.info(f"Starting lab extraction for job_id: {job_id}, files: {len(files)}")
    
    extracted_labs = []
    
    try:
        for file in files:
            # Validate PDF
            if not file.filename.lower().endswith('.pdf'):
                raise HTTPException(status_code=400, detail=f"File {file.filename} is not a PDF")
            
            logger.info(f"Processing: {file.filename}")
            
            # Save uploaded PDF
            pdf_content = await file.read()
            temp_pdf_path = UPLOAD_DIR / f"{job_id}_{file.filename}"
            with open(temp_pdf_path, 'wb') as f:
                f.write(pdf_content)
            
            # Detect lab type
            lab_type = detect_lab_type(str(temp_pdf_path))
            logger.info(f"Detected lab type: {lab_type}")
            
            # Extract based on type
            if lab_type == 'dutch':
                lab_data = extract_dutch(str(temp_pdf_path))
            elif lab_type == 'gi_map':
                lab_data = extract_gi_map(str(temp_pdf_path))
            elif lab_type == 'bloodwork':
                lab_data = extract_bloodwork(str(temp_pdf_path))
            else:
                raise HTTPException(status_code=400, detail=f"Unknown lab type for {file.filename}")
            
            # Save JSON with type in filename
            json_filename = f"{job_id}_{lab_type}.json"
            json_path = OUTPUT_DIR / json_filename
            
            # Convert LabData to dict for JSON serialization
            lab_dict = {
                "reports": [
                    {
                        "report_date": report.report_date,
                        "report_type": report.report_type,
                        "results": [
                            {
                                "test_name": r.test_name,
                                "value": r.value,
                                "unit": r.unit,
                                "reference_range": r.reference_range,
                                "flag": r.flag
                            } for r in report.results
                        ],
                        "key_findings": report.key_findings,
                        "abnormal_markers": report.abnormal_markers
                    } for report in lab_data.reports
                ],
                "summary": lab_data.summary
            }
            
            with open(json_path, 'w') as f:
                json.dump(lab_dict, f, indent=2)
            
            logger.info(f"Saved JSON: {json_path}")
            
            # Count markers
            markers_count = sum(len(report.results) for report in lab_data.reports)
            
            # Include both metadata and full JSON data in response
            extracted_labs.append({
                "type": lab_type,
                "filename": file.filename,
                "json_file": json_filename,
                "markers_count": markers_count,
                "data": lab_dict,
            })
        
        processing_time = time.time() - start_time
        logger.info(f"Lab extraction completed in {processing_time:.2f}s")
        
        return {
            "job_id": job_id,
            "status": "completed",
            "extracted_labs": extracted_labs,
            "processing_time": f"{processing_time:.2f}s"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Lab extraction failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Lab extraction failed: {str(e)}")
