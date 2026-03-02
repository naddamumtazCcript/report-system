"""
Test PDF to Text Converter
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from utils.pdf_to_text_converter import extract_text_from_pdf, convert_pdf_to_text

def test_extract_text():
    """Test extracting text from sample intake PDF"""
    pdf_path = Path(__file__).parent.parent / 'data' / 'jessica_intake.pdf'
    
    if not pdf_path.exists():
        print(f"❌ Test PDF not found: {pdf_path}")
        return False
    
    try:
        text = extract_text_from_pdf(pdf_path)
        assert len(text) > 100, "Extracted text too short"
        assert "Jessica" in text or "Name" in text, "Expected content not found"
        print(f"✅ Text extraction successful ({len(text)} characters)")
        return True
    except Exception as e:
        print(f"❌ Text extraction failed: {e}")
        return False

def test_convert_to_text():
    """Test converting PDF to text file"""
    pdf_path = Path(__file__).parent.parent / 'data' / 'jessica_intake.pdf'
    output_path = Path(__file__).parent.parent / 'data' / 'test_output.txt'
    
    if not pdf_path.exists():
        print(f"❌ Test PDF not found: {pdf_path}")
        return False
    
    try:
        result = convert_pdf_to_text(pdf_path, output_path)
        assert output_path.exists(), "Output file not created"
        
        with open(output_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        assert len(text) > 100, "Output text too short"
        print(f"✅ PDF to text conversion successful")
        
        # Cleanup
        output_path.unlink()
        return True
    except Exception as e:
        print(f"❌ Conversion failed: {e}")
        if output_path.exists():
            output_path.unlink()
        return False

if __name__ == "__main__":
    print("🧪 Testing PDF to Text Converter\n")
    
    results = []
    results.append(("Text Extraction", test_extract_text()))
    results.append(("PDF to Text Conversion", test_convert_to_text()))
    
    print("\n" + "="*50)
    print("Test Results:")
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status} - {name}")
    
    all_passed = all(r[1] for r in results)
    print("="*50)
    print(f"\n{'✅ All tests passed!' if all_passed else '❌ Some tests failed'}")
