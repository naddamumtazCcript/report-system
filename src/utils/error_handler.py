"""
Error handling and logging utilities
"""
import logging
import os
from datetime import datetime
from pathlib import Path

# Create logs directory
LOGS_DIR = Path(__file__).parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# Configure logging
LOG_FILE = LOGS_DIR / f"report_system_{datetime.now().strftime('%Y%m%d')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('report_system')

class ReportSystemError(Exception):
    """Base exception for report system errors"""
    pass

class PDFExtractionError(ReportSystemError):
    """Raised when PDF extraction fails"""
    pass

class DataMappingError(ReportSystemError):
    """Raised when data mapping/extraction fails"""
    pass

class TemplatePopulationError(ReportSystemError):
    """Raised when template population fails"""
    pass

class ConfigurationError(ReportSystemError):
    """Raised when configuration is invalid"""
    pass

def validate_api_key():
    """Validate OpenAI API key is configured"""
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ConfigurationError(
            "OPENAI_API_KEY not found. Please set it in your .env file:\n"
            "OPENAI_API_KEY=your-api-key-here"
        )
    return api_key

def validate_pdf_file(pdf_path):
    """Validate PDF file exists and is readable"""
    if not os.path.exists(pdf_path):
        raise PDFExtractionError(f"PDF file not found: {pdf_path}")
    
    if not pdf_path.lower().endswith('.pdf'):
        raise PDFExtractionError(f"File is not a PDF: {pdf_path}")
    
    if os.path.getsize(pdf_path) == 0:
        raise PDFExtractionError(f"PDF file is empty: {pdf_path}")
    
    return True

def validate_extracted_data(data):
    """Validate extracted data has required fields"""
    required_fields = ['personal_info', 'health_info']
    missing = [f for f in required_fields if f not in data]
    
    if missing:
        raise DataMappingError(
            f"Extracted data missing required fields: {', '.join(missing)}\n"
            f"The PDF may be incomplete or in an unexpected format."
        )
    
    # Check for minimum personal info
    personal_info = data.get('personal_info', {})
    if not personal_info.get('legal_first_name') and not personal_info.get('last_name'):
        raise DataMappingError("Client name is required but not found in extracted data")
    
    return True
