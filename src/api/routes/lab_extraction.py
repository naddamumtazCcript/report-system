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
from ai.gemini_lab_extractor import analyze_lab_with_gemini
from core.schema import LabResult

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
            
            # Extract using auto-detect (handles dutch/gi_map/bloodwork/generic)
            lab_data = analyze_lab_with_gemini(str(temp_pdf_path))
            lab_type = lab_data.reports[0].report_type if lab_data.reports else 'unknown'
            logger.info(f"Extracted lab type: {lab_type}")

            # Flatten to LabResult list for markers_count
            raw_results = [r for report in lab_data.reports for r in report.results]

            # Build response dict — use structured_results for DUTCH/GI-MAP, raw for bloodwork
            def build_report_results(report):
                if report.structured_results is not None:
                    return report.structured_results
                return [
                    {
                        "test_name": r.test_name,
                        "value": r.value,
                        "unit": r.unit,
                        "reference_range": r.reference_range,
                        "flag": r.flag
                    } for r in report.results
                ]

            lab_dict = {
                "reports": [
                    {
                        "report_date": report.report_date,
                        "report_type": report.report_type,
                        "results": build_report_results(report),
                        "key_findings": report.key_findings,
                        "abnormal_markers": report.abnormal_markers
                    } for report in lab_data.reports
                ],
                "summary": lab_data.summary,
            }

            json_filename = f"{job_id}_{lab_type.lower().replace(' ', '_')}.json"
            json_path = OUTPUT_DIR / json_filename
            with open(json_path, 'w') as f:
                json.dump(lab_dict, f, indent=2)
            logger.info(f"Saved JSON: {json_path}")

            extracted_labs.append({
                "type": lab_type,
                "filename": file.filename,
                "json_file": json_filename,
                "markers_count": len(raw_results),
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
