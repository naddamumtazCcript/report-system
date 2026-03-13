"""Protocol generation endpoint"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import time
import sys
import json
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from ..config import UPLOAD_DIR, OUTPUT_DIR
from core.pdf_extractor import PDFExtractor
from core.data_mapper import extract_data
from core.json_parser import parse_questionnaire_json
from core.questionnaire_models import QuestionnaireJSON
from core.html_pdf_generator import generate_protocol_pdf

router = APIRouter()

class GenerateRequest(BaseModel):
    job_id: str

@router.post("/generate")
async def generate_protocol(request: GenerateRequest):
    """Generate personalized health protocol from uploaded PDF"""
    start_time = time.time()
    
    try:
        logger.info(f"Starting protocol generation for job_id: {request.job_id}")
        
        # Find uploaded file
        files = list(UPLOAD_DIR.glob(f"{request.job_id}_*.pdf"))
        if not files:
            logger.error(f"File not found for job_id: {request.job_id}")
            raise HTTPException(status_code=404, detail="File not found")
        
        pdf_path = str(files[0])
        logger.info(f"Found PDF: {pdf_path}")
        
        # Step 1: Extract text from PDF
        logger.info("Step 1: Extracting text from PDF...")
        extractor = PDFExtractor(pdf_path)
        text = extractor.extract_text()
        logger.info(f"Extracted {len(text)} characters")
        
        # Save extracted text
        text_file = OUTPUT_DIR / f"{request.job_id}_extracted_text.txt"
        with open(text_file, 'w') as f:
            f.write(text)
        logger.info(f"Saved extracted text to: {text_file}")
        
        # Step 2: Extract structured data
        logger.info("Step 2: Extracting structured data with OpenAI...")
        try:
            data = extract_data(str(text_file))
        except Exception as e:
            logger.error(f"Data extraction failed: {str(e)}")
            raise
        
        # Step 3: Generate PDF protocol
        logger.info("Step 3: Generating PDF protocol...")
        pdf_output = OUTPUT_DIR / f"{request.job_id}_protocol.pdf"
        
        protocol_data = {
            'client_name': f"{data.get('personal_info', {}).get('legal_first_name', '')} {data.get('personal_info', {}).get('last_name', '')}".strip() or 'Client',
            'health_info': data.get('health_info', {}),
            'nutrition_preferences': data.get('nutrition_preferences', {}),
        }
        
        generate_protocol_pdf(protocol_data, str(pdf_output))
        logger.info(f"Protocol generated: {pdf_output}")
        
        processing_time = time.time() - start_time
        
        return {
            "job_id": request.job_id,
            "status": "completed",
            "protocol_pdf": str(pdf_output),
            "client_name": protocol_data['client_name'],
            "processing_time": f"{processing_time:.2f}s",
            "output_file": str(pdf_output)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Generation failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


@router.post("/generate-from-json")
async def generate_protocol_from_json(questionnaire: QuestionnaireJSON):
    """Generate personalized health protocol from JSON questionnaire"""
    start_time = time.time()
    
    try:
        logger.info("Starting protocol generation from JSON questionnaire")
        
        # Parse questionnaire JSON to INTAKE_SCHEMA format
        logger.info("Step 1: Parsing questionnaire JSON...")
        try:
            data = parse_questionnaire_json(questionnaire.dict())
            logger.info(f"Data parsing successful. Keys: {list(data.keys())}")
        except Exception as e:
            logger.error(f"JSON parsing failed: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Invalid questionnaire format: {str(e)}")
        
        # Generate job_id for this request
        import uuid
        job_id = str(uuid.uuid4())
        
        # Save parsed data
        json_file = OUTPUT_DIR / f"{job_id}_data.json"
        with open(json_file, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Saved parsed data to: {json_file}")
        
        # Step 2: Generate PDF protocol
        logger.info("Step 2: Generating PDF protocol...")
        pdf_output = OUTPUT_DIR / f"{job_id}_protocol.pdf"
        
        # Prepare protocol data for PDF
        protocol_data = {
            'client_name': f"{data.get('personal_info', {}).get('legal_first_name', 'Client')} {data.get('personal_info', {}).get('last_name', '')}".strip(),
            'date': data.get('personal_info', {}).get('date_of_birth', ''),
            'focus_items': [
                'Balance hormones',
                'Improve energy',
                'Support digestion',
                'Reduce inflammation',
                'Optimize sleep'
            ],
            'concerns': [
                {
                    'description': data.get('health_info', {}).get('short_term_goals', ''),
                    'drivers': 'To be determined based on assessment'
                }
            ],
            'lab_review_content': 'Lab results pending',
            'primary_nutrition_goal': data.get('nutrition_preferences', {}).get('nutritional_support_preference', ''),
            'hydration_target': '80-100 oz daily',
            'core_habits': [
                'Eat protein with every meal',
                'Include healthy fats',
                'Focus on fiber-rich vegetables',
                'Limit processed foods'
            ],
            'goals': [
                {'goal': 'Improve energy', 'action': 'Follow nutrition plan'},
                {'goal': 'Better sleep', 'action': 'Evening routine'},
                {'goal': 'Reduce symptoms', 'action': 'Lifestyle modifications'}
            ]
        }
        
        generate_protocol_pdf(protocol_data, str(pdf_output))
        logger.info(f"PDF protocol generated: {pdf_output}")
        
        processing_time = time.time() - start_time
        logger.info(f"Protocol generation completed in {processing_time:.2f}s")
        
        return {
            "job_id": job_id,
            "status": "completed",
            "protocol_pdf": str(pdf_output),
            "client_name": protocol_data['client_name'],
            "processing_time": f"{processing_time:.2f}s",
            "output_file": str(pdf_output),
            "download_url": f"/api/protocol/download-pdf/{job_id}"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Generation failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")