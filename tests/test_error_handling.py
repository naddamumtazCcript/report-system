"""
Test error handling with various failure scenarios
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from error_handler import (
    PDFExtractionError, DataMappingError, ConfigurationError,
    validate_api_key, validate_pdf_file, validate_extracted_data
)

def test_missing_api_key():
    """Test missing API key detection"""
    print("\n[TEST 1] Missing API Key")
    original_key = os.environ.get('OPENAI_API_KEY')
    try:
        # Remove API key temporarily
        if 'OPENAI_API_KEY' in os.environ:
            del os.environ['OPENAI_API_KEY']
        
        validate_api_key()
        print("❌ FAIL - Should have raised ConfigurationError")
    except ConfigurationError as e:
        print(f"✅ PASS - Caught error: {e}")
    finally:
        # Restore API key
        if original_key:
            os.environ['OPENAI_API_KEY'] = original_key

def test_missing_pdf():
    """Test missing PDF file detection"""
    print("\n[TEST 2] Missing PDF File")
    try:
        validate_pdf_file("nonexistent.pdf")
        print("❌ FAIL - Should have raised PDFExtractionError")
    except PDFExtractionError as e:
        print(f"✅ PASS - Caught error: {e}")

def test_invalid_pdf_extension():
    """Test invalid file extension"""
    print("\n[TEST 3] Invalid File Extension")
    try:
        validate_pdf_file("document.txt")
        print("❌ FAIL - Should have raised PDFExtractionError")
    except PDFExtractionError as e:
        print(f"✅ PASS - Caught error: {e}")

def test_empty_pdf():
    """Test empty PDF file"""
    print("\n[TEST 4] Empty PDF File")
    # Create empty file
    empty_file = "tests/empty.pdf"
    with open(empty_file, 'w') as f:
        pass
    
    try:
        validate_pdf_file(empty_file)
        print("❌ FAIL - Should have raised PDFExtractionError")
    except PDFExtractionError as e:
        print(f"✅ PASS - Caught error: {e}")
    finally:
        if os.path.exists(empty_file):
            os.remove(empty_file)

def test_missing_required_fields():
    """Test data validation with missing fields"""
    print("\n[TEST 5] Missing Required Fields")
    try:
        validate_extracted_data({"some_field": "value"})
        print("❌ FAIL - Should have raised DataMappingError")
    except DataMappingError as e:
        print(f"✅ PASS - Caught error: {e}")

def test_missing_client_name():
    """Test data validation with missing client name"""
    print("\n[TEST 6] Missing Client Name")
    try:
        validate_extracted_data({
            "personal_info": {},
            "health_info": {}
        })
        print("❌ FAIL - Should have raised DataMappingError")
    except DataMappingError as e:
        print(f"✅ PASS - Caught error: {e}")

def test_valid_data():
    """Test data validation with valid data"""
    print("\n[TEST 7] Valid Data")
    try:
        result = validate_extracted_data({
            "personal_info": {"name": "John Doe"},
            "health_info": {}
        })
        if result:
            print("✅ PASS - Valid data accepted")
        else:
            print("❌ FAIL - Should have returned True")
    except Exception as e:
        print(f"❌ FAIL - Unexpected error: {e}")

def run_all_tests():
    """Run all error handling tests"""
    print("="*60)
    print("ERROR HANDLING VALIDATION TESTS")
    print("="*60)
    
    test_missing_api_key()
    test_missing_pdf()
    test_invalid_pdf_extension()
    test_empty_pdf()
    test_missing_required_fields()
    test_missing_client_name()
    test_valid_data()
    
    print("\n" + "="*60)
    print("ERROR HANDLING TESTS COMPLETE")
    print("="*60)

if __name__ == "__main__":
    run_all_tests()
