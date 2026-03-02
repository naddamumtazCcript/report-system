"""
Main Pipeline - Orchestrates PDF extraction, data mapping, and template population
"""
import sys
import json
from pathlib import Path
from core.pdf_extractor import PDFExtractor
from core.data_mapper import extract_data
from core.template_populator import populate
from utils.error_handler import (
    ReportSystemError, PDFExtractionError, DataMappingError, 
    TemplatePopulationError, ConfigurationError, logger
)

def run_pipeline(pdf_path, template_path, output_path, lab_files=None):
    """Run complete pipeline"""
    logger.info(f"="*60)
    logger.info(f"Starting pipeline for: {pdf_path}")
    logger.info(f"="*60)
    
    try:
        # Extract and analyze lab reports if provided
        lab_data = None
        if lab_files:
            from core.lab_extractor import extract_multiple_lab_reports
            from ai.lab_analyzer import analyze_multiple_lab_reports
            
            logger.info(f"Extracting {len(lab_files)} lab report(s)...")
            print(f"\n📋 Extracting {len(lab_files)} lab report(s)...")
            
            extract_multiple_lab_reports(lab_files)
            
            logger.info("Analyzing lab reports with AI...")
            print("🧬 Analyzing lab reports with AI...")
            
            lab_data = analyze_multiple_lab_reports()
            print(f"✓ Lab analysis complete: {lab_data.summary}\n")
        
        # Step 1: Extract text from PDF
        logger.info("Step 1: Extracting text from PDF...")
        print("Step 1: Extracting text from PDF...")
        
        extractor = PDFExtractor(pdf_path)
        text = extractor.extract_text()
        
        # Save extracted text
        text_file = "data/extracted_text.txt"
        with open(text_file, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("EXTRACTED TEXT:\n")
            f.write("=" * 80 + "\n")
            f.write(text)
            f.write("\n" + "=" * 80 + "\n")
            f.write(f"\nTotal characters: {len(text)}\n")
        
        logger.info(f"✓ Text extracted: {text_file}")
        print(f"✓ Text extracted: {text_file}")
        
        # Step 2: Extract structured data
        logger.info("Step 2: Extracting structured data with OpenAI...")
        print("Step 2: Extracting structured data with OpenAI...")
        
        data = extract_data(text_file)
        
        # Save JSON data
        json_file = "data/extracted_data.json"
        with open(json_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"✓ Data extracted: {json_file}")
        print(f"✓ Data extracted: {json_file}")
        
        # Step 3: Populate template
        logger.info("Step 3: Populating protocol template...")
        print("Step 3: Populating protocol template...")
        
        result = populate(template_path, json_file, output_path, lab_data)
        
        logger.info(f"✓ Protocol generated: {result}")
        print(f"✓ Protocol generated: {result}")
        
        logger.info("Pipeline completed successfully")
        print("\n✓ Pipeline complete!")
        return result
        
    except PDFExtractionError as e:
        logger.error(f"PDF extraction failed: {e}")
        print(f"\n❌ PDF Extraction Error: {e}", file=sys.stderr)
        print("\nTroubleshooting:")
        print("- Ensure the PDF file is not corrupted")
        print("- Check if the PDF contains extractable text (not just images)")
        print("- Try opening the PDF in a PDF reader to verify it's valid")
        raise
        
    except DataMappingError as e:
        logger.error(f"Data mapping failed: {e}")
        print(f"\n❌ Data Mapping Error: {e}", file=sys.stderr)
        print("\nTroubleshooting:")
        print("- Check if the questionnaire format matches expected structure")
        print("- Verify the PDF contains filled-in answers")
        print("- Review extracted text in data/extracted_text.txt")
        raise
        
    except ConfigurationError as e:
        logger.error(f"Configuration error: {e}")
        print(f"\n❌ Configuration Error: {e}", file=sys.stderr)
        print("\nTroubleshooting:")
        print("- Create a .env file in the project root")
        print("- Add: OPENAI_API_KEY=your-api-key-here")
        print("- Get your API key from: https://platform.openai.com/api-keys")
        raise
        
    except TemplatePopulationError as e:
        logger.error(f"Template population failed: {e}")
        print(f"\n❌ Template Population Error: {e}", file=sys.stderr)
        raise
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        print(f"\n❌ Unexpected Error: {e}", file=sys.stderr)
        print("\nPlease check the log file for details.")
        raise

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate health protocol from intake questionnaire')
    parser.add_argument('pdf_file', help='Path to intake questionnaire PDF')
    parser.add_argument('--labs', nargs='*', help='Path(s) to lab report PDFs', default=[])
    
    args = parser.parse_args()
    
    pdf_file = args.pdf_file
    lab_files = args.labs
    template_file = "templates/ProtocolTemplate.md"
    output_file = "data/output/generated_protocol.md"
    
    # Ensure output directory exists
    Path("data/output").mkdir(parents=True, exist_ok=True)
    
    # Extract lab reports if provided
    if lab_files:
        print(f"\n📋 Processing {len(lab_files)} lab report(s)...")
    
    try:
        run_pipeline(pdf_file, template_file, output_file, lab_files)
        sys.exit(0)
    except ReportSystemError:
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print(f"\n❌ Fatal Error: {e}", file=sys.stderr)
        sys.exit(1)
