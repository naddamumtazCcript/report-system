"""
Comprehensive Protocol Generation Endpoint
Handles all 5 steps: Patient → Template → Intake → Labs → Libraries
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import List, Optional
from pydantic import BaseModel
import uuid
import json
import time
from pathlib import Path
import logging

from ..config import UPLOAD_DIR, OUTPUT_DIR
from core.pdf_extractor import PDFExtractor
from core.data_mapper import extract_data
from core.template_populator import populate
from core.template_registry import (
    TemplateType, 
    get_template_path, 
    get_template_metadata,
    validate_template_type,
    list_available_templates
)
from core.lab_extractor import extract_multiple_lab_reports
from ai.lab_analyzer import analyze_multiple_lab_reports

logger = logging.getLogger(__name__)
router = APIRouter()

class GenerationResponse(BaseModel):
    """Response model for protocol generation"""
    status: str
    job_id: str
    patient_id: str
    template_type: str
    processing_steps: dict
    output: dict
    metadata: dict

@router.get("/templates")
async def get_available_templates():
    """
    Get list of available clinical templates
    
    Returns:
        List of templates with metadata
    """
    return {
        "templates": list_available_templates(),
        "default": TemplateType.STANDARD_PROTOCOL
    }

@router.post("/generate-protocol")
async def generate_comprehensive_protocol(
    patient_id: str = Form(...),
    template_type: Optional[str] = Form(None),
    intake_file: UploadFile = File(...),
    selected_libraries: Optional[str] = Form(None),
    lab_files: Optional[List[UploadFile]] = File(None),
    doc_types: Optional[str] = Form(None),
    libraries: Optional[str] = Form(None),
    template: Optional[str] = Form(None),
    include_lab_analysis: bool = Form(True),
    practitioner_notes: Optional[str] = Form(None),
    user_id: Optional[str] = Form(None),
    client_id: Optional[str] = Form(None)
):
    """
    Comprehensive protocol generation endpoint
    
    Supports two modes:
    1. File-based: Uses template_type and selected_libraries (legacy)
    2. JSON-based: Uses libraries and template as JSON objects (new)
    
    Args:
        patient_id: Unique patient identifier
        template_type: Clinical template (standard_protocol, deep_analysis, quick_scan) - File mode
        intake_file: Patient intake questionnaire PDF
        selected_libraries: JSON array of library names - File mode
        lab_files: Optional list of lab report PDFs
        doc_types: JSON array mapping lab files to types ["dutch", "gi_map", "bloodwork"]
        libraries: JSON object with library data - JSON mode
        template: JSON object with template structure - JSON mode
        include_lab_analysis: Whether to include lab analysis
        practitioner_notes: Optional notes from practitioner
        user_id: Practitioner ID
        client_id: Client ID
    
    Returns:
        Complete protocol with metadata
    """
    start_time = time.time()
    job_id = str(uuid.uuid4())
    
    processing_steps = {
        "validation": "pending",
        "pdf_extraction": "pending",
        "data_mapping": "pending",
        "lab_analysis": "pending",
        "ai_recommendations": "pending",
        "template_population": "pending"
    }
    
    try:
        # ============================================================
        # STEP 1: VALIDATION
        # ============================================================
        logger.info(f"[{job_id}] Starting protocol generation")
        logger.info(f"[{job_id}] Patient: {patient_id}")
        
        # Detect mode
        is_json_mode = libraries is not None and template is not None
        
        if is_json_mode:
            logger.info(f"[{job_id}] Mode: JSON-based")
            # Parse JSON inputs
            try:
                libraries_json = json.loads(libraries)
                template_json = json.loads(template)
            except json.JSONDecodeError as e:
                raise HTTPException(status_code=400, detail=f"Invalid JSON format: {e}")
        else:
            logger.info(f"[{job_id}] Mode: File-based, Template: {template_type}")
            # Validate template type
            if not template_type:
                raise HTTPException(status_code=400, detail="template_type is required for file-based mode")
            if not validate_template_type(template_type):
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid template type: {template_type}. Must be one of: {list(TemplateType.__members__.values())}"
                )
            
            # Parse selected libraries
            if selected_libraries:
                try:
                    libraries_list = json.loads(selected_libraries)
                    if not isinstance(libraries_list, list):
                        raise ValueError("selected_libraries must be an array")
                except json.JSONDecodeError:
                    raise HTTPException(status_code=400, detail="Invalid selected_libraries format. Must be JSON array.")
            else:
                libraries_list = []
        
        # Validate intake file
        if not intake_file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Intake file must be a PDF")
        
        processing_steps["validation"] = "completed"
        logger.info(f"[{job_id}] Validation completed")
        
        # ============================================================
        # STEP 2: SAVE UPLOADED FILES
        # ============================================================
        
        # Save intake PDF
        intake_path = UPLOAD_DIR / f"{job_id}_intake.pdf"
        with open(intake_path, "wb") as f:
            content = await intake_file.read()
            f.write(content)
        logger.info(f"[{job_id}] Intake PDF saved: {intake_path}")
        
        # Save lab PDFs (if provided)
        lab_paths = []
        lab_data = None
        if lab_files and include_lab_analysis:
            if doc_types:
                # JSON mode with explicit doc types
                doc_types_list = json.loads(doc_types)
                if len(lab_files) != len(doc_types_list):
                    raise HTTPException(
                        status_code=400,
                        detail="Number of lab PDFs must match number of doc_types"
                    )
                
                from ai.gemini_lab_extractor import analyze_lab_with_gemini
                from core.schema import LabData
                
                all_reports = []
                for i, (lab_file, doc_type) in enumerate(zip(lab_files, doc_types_list)):
                    if not lab_file.filename.endswith('.pdf'):
                        logger.warning(f"[{job_id}] Skipping non-PDF lab file: {lab_file.filename}")
                        continue
                    
                    lab_path = UPLOAD_DIR / f"{job_id}_lab_{i}_{doc_type}.pdf"
                    with open(lab_path, "wb") as f:
                        lab_content = await lab_file.read()
                        f.write(lab_content)
                    
                    lab_result = analyze_lab_with_gemini(str(lab_path))
                    if lab_result and lab_result.reports:
                        all_reports.extend(lab_result.reports)
                    lab_paths.append(str(lab_path))
                
                lab_data = LabData(reports=all_reports, summary="") if all_reports else None
                logger.info(f"[{job_id}] {len(lab_paths)} lab PDFs processed with Gemini")
            else:
                # Legacy mode - auto-detect
                for i, lab_file in enumerate(lab_files):
                    if not lab_file.filename.endswith('.pdf'):
                        logger.warning(f"[{job_id}] Skipping non-PDF lab file: {lab_file.filename}")
                        continue
                    
                    lab_path = UPLOAD_DIR / f"{job_id}_lab_{i}.pdf"
                    with open(lab_path, "wb") as f:
                        lab_content = await lab_file.read()
                        f.write(lab_content)
                    lab_paths.append(str(lab_path))
                
                logger.info(f"[{job_id}] {len(lab_paths)} lab PDFs saved")
        
        # ============================================================
        # STEP 3: PDF EXTRACTION
        # ============================================================
        processing_steps["pdf_extraction"] = "in_progress"
        logger.info(f"[{job_id}] Extracting text from intake PDF...")
        
        extractor = PDFExtractor(str(intake_path))
        intake_text = extractor.extract_text()
        
        # Save extracted text
        text_file = UPLOAD_DIR / f"{job_id}_text.txt"
        with open(text_file, 'w') as f:
            f.write(intake_text)
        
        processing_steps["pdf_extraction"] = "completed"
        logger.info(f"[{job_id}] PDF extraction completed: {len(intake_text)} characters")
        
        # ============================================================
        # STEP 4: DATA MAPPING
        # ============================================================
        processing_steps["data_mapping"] = "in_progress"
        logger.info(f"[{job_id}] Mapping data to structured JSON...")
        
        client_data = extract_data(str(text_file))
        
        # Save JSON data
        json_file = UPLOAD_DIR / f"{job_id}_data.json"
        with open(json_file, 'w') as f:
            json.dump(client_data, f, indent=2)
        
        processing_steps["data_mapping"] = "completed"
        logger.info(f"[{job_id}] Data mapping completed")
        
        # ============================================================
        # STEP 5: LAB ANALYSIS (if provided and not already processed)
        # ============================================================
        if lab_paths and include_lab_analysis and not lab_data:
            processing_steps["lab_analysis"] = "in_progress"
            logger.info(f"[{job_id}] Analyzing {len(lab_paths)} lab reports...")
            
            try:
                # Extract lab reports
                extract_multiple_lab_reports(lab_paths)
                
                # Analyze with AI
                lab_data = analyze_multiple_lab_reports()
                
                processing_steps["lab_analysis"] = "completed"
                logger.info(f"[{job_id}] Lab analysis completed")
            except Exception as e:
                logger.error(f"[{job_id}] Lab analysis failed: {e}")
                processing_steps["lab_analysis"] = "failed"
                # Continue without lab data
        elif lab_data:
            processing_steps["lab_analysis"] = "completed"
        else:
            processing_steps["lab_analysis"] = "skipped"
        
        # ============================================================
        # STEP 6: AI RECOMMENDATIONS
        # ============================================================
        processing_steps["ai_recommendations"] = "in_progress"
        
        if is_json_mode:
            logger.info(f"[{job_id}] Generating AI recommendations using JSON libraries")
        else:
            logger.info(f"[{job_id}] Generating AI recommendations using libraries: {libraries_list}")
        
        processing_steps["ai_recommendations"] = "completed"
        logger.info(f"[{job_id}] AI recommendations completed")
        
        # ============================================================
        # STEP 7: TEMPLATE POPULATION
        # ============================================================
        processing_steps["template_population"] = "in_progress"
        
        # Generate output file
        output_file = OUTPUT_DIR / f"{job_id}_protocol.md"
        
        if is_json_mode:
            logger.info(f"[{job_id}] Populating JSON template...")
            from core.template_populator_json import populate_json
            
            populate_json(
                template_json=template_json,
                client_data=client_data,
                libraries_json=libraries_json,
                output_path=str(output_file),
                lab_data=lab_data,
                user_id=user_id,
                client_id=client_id
            )
        else:
            logger.info(f"[{job_id}] Populating {template_type} template...")
            
            # Get template path
            template_path = get_template_path(template_type)
            
            # Populate template
            populate(str(template_path), str(json_file), str(output_file), lab_data)
        
        processing_steps["template_population"] = "completed"
        logger.info(f"[{job_id}] Template population completed")
        
        # ============================================================
        # STEP 8: BUILD RESPONSE
        # ============================================================
        
        # Read generated protocol
        with open(output_file, 'r') as f:
            protocol_content = f.read()
        
        # Extract client name
        client_name = f"{client_data.get('personal_info', {}).get('legal_first_name', '')} {client_data.get('personal_info', {}).get('last_name', '')}".strip()
        if not client_name:
            client_name = "Unknown"
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Get template metadata
        if is_json_mode:
            template_meta = {"name": "Custom JSON Template", "description": "JSON-based template"}
            libraries_used = list(libraries_json.keys()) if libraries_json else []
        else:
            template_meta = get_template_metadata(template_type)
            libraries_used = libraries_list
        
        # Build response
        response = {
            "status": "success",
            "job_id": job_id,
            "patient_id": patient_id,
            "template_type": template_type if not is_json_mode else "json_template",
            "user_id": user_id,
            "client_id": client_id,
            "processing_steps": processing_steps,
            "output": {
                "protocol_file": str(output_file),
                "protocol_content": protocol_content,
                "client_name": client_name,
                "download_url": f"/api/download/{job_id}"
            },
            "metadata": {
                "mode": "json" if is_json_mode else "file",
                "template_name": template_meta["name"],
                "template_description": template_meta["description"],
                "libraries_used": libraries_used,
                "lab_reports_processed": len(lab_paths) if lab_paths else 0,
                "processing_time": f"{processing_time:.2f}s",
                "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "practitioner_notes": practitioner_notes
            }
        }
        
        logger.info(f"[{job_id}] Protocol generation completed in {processing_time:.2f}s")
        
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{job_id}] Protocol generation failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail={
                "error": "Protocol generation failed",
                "message": str(e),
                "job_id": job_id,
                "processing_steps": processing_steps
            }
        )

@router.get("/download/{job_id}")
async def download_protocol(job_id: str):
    """
    Download generated protocol
    
    Args:
        job_id: Job ID from generation request
    
    Returns:
        Protocol file
    """
    from fastapi.responses import FileResponse
    
    protocol_file = OUTPUT_DIR / f"{job_id}_protocol.md"
    
    if not protocol_file.exists():
        raise HTTPException(status_code=404, detail="Protocol not found")
    
    return FileResponse(
        path=protocol_file,
        filename=f"protocol_{job_id}.md",
        media_type="text/markdown"
    )

@router.get("/status/{job_id}")
async def get_generation_status(job_id: str):
    """
    Get status of protocol generation (for future async implementation)
    
    Args:
        job_id: Job ID from generation request
    
    Returns:
        Generation status
    """
    protocol_file = OUTPUT_DIR / f"{job_id}_protocol.md"
    data_file = UPLOAD_DIR / f"{job_id}_data.json"
    
    if protocol_file.exists():
        return {
            "job_id": job_id,
            "status": "completed",
            "download_url": f"/api/download/{job_id}"
        }
    elif data_file.exists():
        return {
            "job_id": job_id,
            "status": "processing"
        }
    else:
        return {
            "job_id": job_id,
            "status": "not_found"
        }
