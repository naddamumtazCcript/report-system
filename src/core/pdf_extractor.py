"""
PDF Text Extractor
Extracts text content from PDF files using pdfplumber
"""

import pdfplumber
from pathlib import Path
from utils.error_handler import PDFExtractionError, logger, validate_pdf_file


class PDFExtractor:
    """Extract text from PDF files"""
    
    def __init__(self, pdf_path: str):
        """
        Initialize PDF extractor
        
        Args:
            pdf_path: Path to the PDF file
        """
        self.pdf_path = Path(pdf_path)
        try:
            validate_pdf_file(str(self.pdf_path))
            logger.info(f"Initialized PDF extractor for: {pdf_path}")
        except Exception as e:
            logger.error(f"PDF validation failed: {e}")
            raise
    
    def extract_text(self) -> str:
        """
        Extract all text from the PDF
        
        Returns:
            Extracted text as a single string
        """
        try:
            text_content = []
            
            with pdfplumber.open(self.pdf_path) as pdf:
                if len(pdf.pages) == 0:
                    raise PDFExtractionError("PDF has no pages")
                
                for i, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    if text:
                        text_content.append(text)
                    else:
                        logger.warning(f"Page {i+1} has no extractable text")
            
            if not text_content:
                raise PDFExtractionError(
                    "No text could be extracted from PDF. "
                    "The PDF may be image-based or corrupted."
                )
            
            full_text = "\n\n".join(text_content)
            logger.info(f"Successfully extracted {len(full_text)} characters from {len(text_content)} pages")
            return full_text
            
        except pdfplumber.pdfminer.pdfparser.PDFSyntaxError as e:
            logger.error(f"PDF syntax error: {e}")
            raise PDFExtractionError(f"PDF file is corrupted or malformed: {e}")
        except Exception as e:
            logger.error(f"PDF extraction failed: {e}")
            raise PDFExtractionError(f"Failed to extract text from PDF: {e}")
    
    def extract_text_by_page(self) -> list[str]:
        """
        Extract text from PDF, separated by page
        
        Returns:
            List of text strings, one per page
        """
        pages_text = []
        
        with pdfplumber.open(self.pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                pages_text.append(text if text else "")
        
        return pages_text


def main():
    """Test the PDF extractor"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python pdf_extractor.py <pdf_file>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    try:
        extractor = PDFExtractor(pdf_path)
        text = extractor.extract_text()
        
        print("=" * 80)
        print("EXTRACTED TEXT:")
        print("=" * 80)
        print(text)
        print("=" * 80)
        print(f"\nTotal characters: {len(text)}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
