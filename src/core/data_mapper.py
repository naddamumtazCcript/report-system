"""
Data Mapper - Extracts structured JSON from PDF text using OpenAI
"""
import json
import os
from openai import OpenAI
from core.schema import INTAKE_SCHEMA
from dotenv import load_dotenv
from utils.error_handler import DataMappingError, ConfigurationError, logger, validate_api_key, validate_extracted_data

load_dotenv()

def configure_openai():
    """Configure OpenAI API"""
    try:
        api_key = validate_api_key()
        logger.info("OpenAI API key validated")
        return OpenAI(api_key=api_key)
    except ConfigurationError as e:
        logger.error(f"OpenAI configuration failed: {e}")
        raise

def create_extraction_prompt(text):
    """Create prompt for OpenAI to extract structured data"""
    return f"""Extract all client information from this intake questionnaire text and return it as JSON.

IMPORTANT INSTRUCTIONS:
- Extract ONLY the client's filled-in answers, NOT the question labels
- If a field is empty or not answered, use an empty string ""
- For lists/arrays, extract multiple items if present
- Return valid JSON matching this exact structure:

{json.dumps(INTAKE_SCHEMA, indent=2)}

QUESTIONNAIRE TEXT:
{text}

Return ONLY the JSON object, no other text."""

def extract_data(text_file_path):
    """Extract structured data from PDF text using OpenAI"""
    try:
        # Read extracted text
        if not os.path.exists(text_file_path):
            raise DataMappingError(f"Text file not found: {text_file_path}")
        
        with open(text_file_path, 'r') as f:
            text = f.read()
        
        if not text.strip():
            raise DataMappingError("Extracted text is empty")
        
        logger.info(f"Processing {len(text)} characters of extracted text")
        
        # Configure OpenAI
        client = configure_openai()
        
        # Create prompt and get response
        prompt = create_extraction_prompt(text)
        logger.info("Sending data extraction request to OpenAI...")
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        
        # Parse JSON response
        response_text = response.choices[0].message.content.strip()
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]
        
        data = json.loads(response_text.strip())
        
        # Log what OpenAI returned
        logger.info(f"OpenAI response data keys: {list(data.keys())}")
        logger.info(f"Personal info from OpenAI: {data.get('personal_info', {})}")
        
        # Validate extracted data
        validate_extracted_data(data)
        
        logger.info(f"Successfully extracted data for client: {data.get('personal_info', {}).get('name', 'Unknown')}")
        return data
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response: {e}")
        raise DataMappingError(f"OpenAI returned invalid JSON: {e}")
    except Exception as e:
        if isinstance(e, (DataMappingError, ConfigurationError)):
            raise
        logger.error(f"Data extraction failed: {e}")
        raise DataMappingError(f"Failed to extract data: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python3 data_mapper.py <extracted_text_file>")
        sys.exit(1)
    
    text_file = sys.argv[1]
    
    try:
        data = extract_data(text_file)
        print(json.dumps(data, indent=2))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
