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
from core.template_populator import populate

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
            logger.info(f"Data extraction successful. Keys: {list(data.keys())}")
            logger.info(f"Personal info: {data.get('personal_info', {})}")
        except Exception as e:
            logger.error(f"Data extraction failed: {str(e)}")
            raise
        
        # Save JSON data
        json_file = OUTPUT_DIR / f"{request.job_id}_data.json"
        with open(json_file, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Saved JSON data to: {json_file}")
        
        # Step 3: Populate template
        logger.info("Step 3: Populating protocol template...")
        template_path = "templates/ProtocolTemplate.md"
        output_file = OUTPUT_DIR / f"{request.job_id}_protocol.md"
        
        populate(template_path, str(json_file), str(output_file))
        logger.info(f"Protocol generated: {output_file}")
        
        # Read generated protocol
        with open(output_file, 'r') as f:
            protocol = f.read()
        
        processing_time = time.time() - start_time
        logger.info(f"Protocol generation completed in {processing_time:.2f}s")
        
        return {
            "job_id": request.job_id,
            "status": "completed",
            "protocol": protocol,
            "client_name": data.get('personal_info', {}).get('name', 'Unknown'),
            "processing_time": f"{processing_time:.2f}s",
            "output_file": str(output_file)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Generation failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")
