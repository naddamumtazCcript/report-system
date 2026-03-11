"""
PDF to JSON Converter - Converts library/template PDFs to structured JSON using Gemini
"""
import os
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
import uuid
import json
from pathlib import Path
import logging
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

from ..config import UPLOAD_DIR, OUTPUT_DIR

logger = logging.getLogger(__name__)
router = APIRouter()

def convert_pdf_to_json_with_gemini(pdf_path: str, document_type: str) -> dict:
    """
    Convert PDF to JSON using Gemini 2.5 Flash
    
    Args:
        pdf_path: Path to PDF file
        document_type: 'library' or 'template'
    
    Returns:
        Structured JSON representation of the PDF
    """
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment")
    
    client = genai.Client(api_key=api_key)
    
    logger.info(f"Uploading PDF to Gemini: {pdf_path}")
    
    # Upload PDF to Gemini
    with open(pdf_path, 'rb') as f:
        uploaded_file = client.files.upload(file=f, config={'mime_type': 'application/pdf'})
    
    logger.info(f"PDF uploaded successfully, processing with Gemini...")
    
    # Different prompts based on document type
    if document_type == 'library':
        prompt = """
        You are a medical knowledge base parser. Extract ALL content from this library PDF into structured JSON.
        
        This is a practitioner knowledge library containing guidelines, protocols, and recommendations.
        
        Your task:
        1. Identify the main topic/category of this library (e.g., "Nutrition", "Supplements", "Lifestyle", "Labs")
        2. Extract ALL sections, subsections, and content
        3. Preserve all guidelines, rules, recommendations, and protocols
        4. Maintain hierarchical structure
        5. Keep all medical terminology and specific instructions
        
        Return a JSON object with this structure:
        {
          "library_name": "Name of the library",
          "category": "Main category (Nutrition/Supplements/Lifestyle/Labs/etc)",
          "description": "Brief description of what this library covers",
          "sections": [
            {
              "title": "Section title",
              "content": "Full section content with all details",
              "subsections": [
                {
                  "title": "Subsection title",
                  "content": "Subsection content",
                  "guidelines": ["guideline 1", "guideline 2"],
                  "recommendations": ["rec 1", "rec 2"]
                }
              ]
            }
          ],
          "key_protocols": ["protocol 1", "protocol 2"],
          "important_notes": ["note 1", "note 2"]
        }
        
        Be thorough - extract EVERYTHING. This will be used by AI to generate medical protocols.
        """
    else:  # template
        prompt = """
        You are a medical template parser. Extract ALL content from this protocol template PDF into structured JSON.
        
        This is a clinical protocol template with sections and placeholders.
        
        Your task:
        1. Identify the template name/type
        2. Extract ALL sections in order
        3. Preserve all placeholders (e.g., {Client Name}, {Date})
        4. Maintain exact structure and formatting instructions
        5. Keep all section headers and subsection headers
        
        Return a JSON object with this structure:
        {
          "template_name": "Name of the template",
          "template_type": "Type (e.g., Standard Protocol, Deep Analysis, Quick Scan)",
          "description": "What this template is used for",
          "sections": [
            {
              "section_number": 1,
              "section_title": "SECTION 1: GENERAL",
              "subsections": [
                {
                  "title": "TOP CONCERNS",
                  "content": "Full content with placeholders",
                  "placeholders": ["{Client Name}", "{Date}"],
                  "structure": "Description of expected structure"
                }
              ]
            }
          ],
          "required_fields": ["field1", "field2"],
          "optional_fields": ["field3", "field4"]
        }
        
        Be thorough - extract EVERYTHING including all formatting and structure.
        """
    
    # Generate JSON with Gemini
    response = client.models.generate_content(
        model="models/gemini-2.5-flash",
        contents=[uploaded_file, prompt],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.0
        ),
    )
    
    logger.info("Gemini processing completed")
    
    # Parse response
    result_text = response.text.strip()
    
    # Remove markdown code blocks if present
    if result_text.startswith('```json'):
        result_text = result_text[7:]
    if result_text.endswith('```'):
        result_text = result_text[:-3]
    
    result_json = json.loads(result_text.strip())
    
    return result_json


@router.post("/convert-pdf-to-json")
async def convert_pdf_to_json(
    file: UploadFile = File(...),
    document_type: str = Form(...),  # 'library' or 'template'
    document_name: Optional[str] = Form(None)
):
    """
    Convert library or template PDF to structured JSON using Gemini AI
    
    Args:
        file: PDF file to convert
        document_type: 'library' or 'template'
        document_name: Optional name for the document
    
    Returns:
        Structured JSON representation of the PDF
    """
    
    # Validate inputs
    if document_type not in ['library', 'template']:
        raise HTTPException(
            status_code=400, 
            detail="document_type must be 'library' or 'template'"
        )
    
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="File must be a PDF"
        )
    
    job_id = str(uuid.uuid4())
    
    try:
        logger.info(f"[{job_id}] Starting PDF to JSON conversion")
        logger.info(f"[{job_id}] File: {file.filename}, Type: {document_type}")
        
        # Save uploaded PDF temporarily
        temp_pdf_path = UPLOAD_DIR / f"{job_id}_{file.filename}"
        with open(temp_pdf_path, 'wb') as f:
            content = await file.read()
            f.write(content)
        
        logger.info(f"[{job_id}] PDF saved temporarily: {temp_pdf_path}")
        
        # Convert to JSON using Gemini
        result_json = convert_pdf_to_json_with_gemini(str(temp_pdf_path), document_type)
        
        # Add metadata
        result_json['metadata'] = {
            'job_id': job_id,
            'original_filename': file.filename,
            'document_type': document_type,
            'document_name': document_name or file.filename,
            'conversion_method': 'gemini-2.5-flash'
        }
        
        # Save JSON output
        json_filename = f"{job_id}_{document_type}.json"
        json_path = OUTPUT_DIR / json_filename
        
        with open(json_path, 'w') as f:
            json.dump(result_json, f, indent=2)
        
        logger.info(f"[{job_id}] JSON saved: {json_path}")
        
        # Clean up temporary PDF
        temp_pdf_path.unlink()
        
        logger.info(f"[{job_id}] Conversion completed successfully")
        
        return {
            "status": "success",
            "job_id": job_id,
            "document_type": document_type,
            "document_name": document_name or file.filename,
            "json_file": json_filename,
            "json_data": result_json
        }
    
    except Exception as e:
        logger.error(f"[{job_id}] Conversion failed: {str(e)}", exc_info=True)
        
        # Clean up on error
        if temp_pdf_path.exists():
            temp_pdf_path.unlink()
        
        raise HTTPException(
            status_code=500,
            detail=f"PDF to JSON conversion failed: {str(e)}"
        )


@router.post("/convert-multiple-pdfs")
async def convert_multiple_pdfs(
    files: list[UploadFile] = File(...),
    document_type: str = Form(...)  # 'library' or 'template'
):
    """
    Convert multiple PDFs to JSON in one request
    
    Args:
        files: List of PDF files
        document_type: 'library' or 'template'
    
    Returns:
        List of JSON conversions
    """
    
    if document_type not in ['library', 'template']:
        raise HTTPException(
            status_code=400,
            detail="document_type must be 'library' or 'template'"
        )
    
    results = []
    
    for file in files:
        if not file.filename.lower().endswith('.pdf'):
            logger.warning(f"Skipping non-PDF file: {file.filename}")
            continue
        
        try:
            # Process each file
            result = await convert_pdf_to_json(file, document_type)
            results.append(result)
        except Exception as e:
            logger.error(f"Failed to convert {file.filename}: {str(e)}")
            results.append({
                "status": "failed",
                "filename": file.filename,
                "error": str(e)
            })
    
    return {
        "status": "completed",
        "total_files": len(files),
        "successful": len([r for r in results if r.get('status') == 'success']),
        "failed": len([r for r in results if r.get('status') == 'failed']),
        "results": results
    }
