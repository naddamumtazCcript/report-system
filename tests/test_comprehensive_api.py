"""
Test Comprehensive Protocol Generation Endpoint

This script demonstrates how to use the new comprehensive endpoint
that handles all 5 steps in one call.
"""
import requests
import json
from pathlib import Path

# API Configuration
API_BASE_URL = "http://localhost:8000/api"

def test_get_available_templates():
    """Test getting available templates"""
    print("=" * 60)
    print("TEST 1: Get Available Templates")
    print("=" * 60)
    
    response = requests.get(f"{API_BASE_URL}/templates")
    
    if response.status_code == 200:
        data = response.json()
        print("\n✅ Available Templates:")
        for template in data["templates"]:
            print(f"\n  Type: {template['type']}")
            print(f"  Name: {template['metadata']['name']}")
            print(f"  Description: {template['metadata']['description']}")
            print(f"  Processing Time: {template['metadata']['processing_time']}")
            print(f"  Requires Labs: {template['metadata']['requires_labs']}")
        print(f"\n  Default: {data['default']}")
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)

def test_generate_standard_protocol():
    """Test generating a standard protocol"""
    print("\n" + "=" * 60)
    print("TEST 2: Generate Standard Protocol")
    print("=" * 60)
    
    # Prepare files
    intake_pdf = Path("data/jessica_intake.pdf")
    
    if not intake_pdf.exists():
        print(f"❌ Intake PDF not found: {intake_pdf}")
        return
    
    # Prepare form data
    files = {
        'intake_file': ('jessica_intake.pdf', open(intake_pdf, 'rb'), 'application/pdf')
    }
    
    data = {
        'patient_id': 'patient_jessica_001',
        'template_type': 'standard_protocol',
        'selected_libraries': json.dumps([
            'BeBalancedNutritionLibrary',
            'BeBalancedSupplementLibrary',
            'BeBalancedLifestyleLibrary'
        ]),
        'include_lab_analysis': 'false',
        'practitioner_notes': 'Initial consultation - focus on gut health'
    }
    
    print("\n📤 Sending request...")
    print(f"  Patient ID: {data['patient_id']}")
    print(f"  Template: {data['template_type']}")
    print(f"  Libraries: {data['selected_libraries']}")
    
    response = requests.post(
        f"{API_BASE_URL}/generate-protocol",
        files=files,
        data=data
    )
    
    if response.status_code == 200:
        result = response.json()
        print("\n✅ Protocol Generated Successfully!")
        print(f"\n  Job ID: {result['job_id']}")
        print(f"  Patient ID: {result['patient_id']}")
        print(f"  Template: {result['template_type']}")
        print(f"  Client Name: {result['output']['client_name']}")
        print(f"  Processing Time: {result['metadata']['processing_time']}")
        print(f"  Download URL: {result['output']['download_url']}")
        
        print("\n  Processing Steps:")
        for step, status in result['processing_steps'].items():
            print(f"    - {step}: {status}")
        
        print("\n  Metadata:")
        print(f"    - Template: {result['metadata']['template_name']}")
        print(f"    - Libraries Used: {', '.join(result['metadata']['libraries_used'])}")
        print(f"    - Lab Reports: {result['metadata']['lab_reports_processed']}")
        
        # Save protocol to file
        output_file = Path(f"data/output/test_{result['job_id']}_protocol.md")
        with open(output_file, 'w') as f:
            f.write(result['output']['protocol_content'])
        print(f"\n  Protocol saved to: {output_file}")
        
        return result['job_id']
    else:
        print(f"\n❌ Failed: {response.status_code}")
        print(response.text)
        return None

def test_generate_with_labs():
    """Test generating protocol with lab reports"""
    print("\n" + "=" * 60)
    print("TEST 3: Generate Protocol with Lab Reports")
    print("=" * 60)
    
    # Prepare files
    intake_pdf = Path("data/jessica_intake.pdf")
    lab_pdf_1 = Path("data/lab_reports/sample_report_1.pdf")
    lab_pdf_2 = Path("data/lab_reports/sample_report_2.pdf")
    
    if not intake_pdf.exists():
        print(f"❌ Intake PDF not found: {intake_pdf}")
        return
    
    # Check if lab files exist
    lab_files = []
    if lab_pdf_1.exists():
        lab_files.append(('lab_files', ('lab_1.pdf', open(lab_pdf_1, 'rb'), 'application/pdf')))
    if lab_pdf_2.exists():
        lab_files.append(('lab_files', ('lab_2.pdf', open(lab_pdf_2, 'rb'), 'application/pdf')))
    
    if not lab_files:
        print("⚠️  No lab files found, skipping test")
        return
    
    # Prepare form data
    files = [
        ('intake_file', ('jessica_intake.pdf', open(intake_pdf, 'rb'), 'application/pdf'))
    ] + lab_files
    
    data = {
        'patient_id': 'patient_jessica_002',
        'template_type': 'standard_protocol',
        'selected_libraries': json.dumps([
            'BeBalancedNutritionLibrary',
            'BeBalancedSupplementLibrary',
            'BeBalancedLifestyleLibrary',
            'BeBalancedLabLibrary'
        ]),
        'include_lab_analysis': 'true',
        'practitioner_notes': 'Follow-up with lab results'
    }
    
    print("\n📤 Sending request with lab reports...")
    print(f"  Patient ID: {data['patient_id']}")
    print(f"  Template: {data['template_type']}")
    print(f"  Lab Files: {len(lab_files)}")
    
    response = requests.post(
        f"{API_BASE_URL}/generate-protocol",
        files=files,
        data=data
    )
    
    if response.status_code == 200:
        result = response.json()
        print("\n✅ Protocol with Labs Generated Successfully!")
        print(f"\n  Job ID: {result['job_id']}")
        print(f"  Lab Reports Processed: {result['metadata']['lab_reports_processed']}")
        print(f"  Processing Time: {result['metadata']['processing_time']}")
        
        return result['job_id']
    else:
        print(f"\n❌ Failed: {response.status_code}")
        print(response.text)
        return None

def test_download_protocol(job_id):
    """Test downloading generated protocol"""
    print("\n" + "=" * 60)
    print("TEST 4: Download Protocol")
    print("=" * 60)
    
    if not job_id:
        print("⚠️  No job_id provided, skipping test")
        return
    
    print(f"\n📥 Downloading protocol for job: {job_id}")
    
    response = requests.get(f"{API_BASE_URL}/download/{job_id}")
    
    if response.status_code == 200:
        output_file = Path(f"data/output/downloaded_{job_id}.md")
        with open(output_file, 'wb') as f:
            f.write(response.content)
        print(f"✅ Protocol downloaded to: {output_file}")
    else:
        print(f"❌ Failed: {response.status_code}")

def test_get_status(job_id):
    """Test getting generation status"""
    print("\n" + "=" * 60)
    print("TEST 5: Get Generation Status")
    print("=" * 60)
    
    if not job_id:
        print("⚠️  No job_id provided, skipping test")
        return
    
    print(f"\n🔍 Checking status for job: {job_id}")
    
    response = requests.get(f"{API_BASE_URL}/status/{job_id}")
    
    if response.status_code == 200:
        status = response.json()
        print(f"✅ Status: {status['status']}")
        if status['status'] == 'completed':
            print(f"   Download URL: {status['download_url']}")
    else:
        print(f"❌ Failed: {response.status_code}")

def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("COMPREHENSIVE PROTOCOL GENERATION API TESTS")
    print("=" * 60)
    print("\nMake sure the API server is running:")
    print("  cd src && python -m uvicorn api.app:app --reload")
    print("\n" + "=" * 60)
    
    try:
        # Test 1: Get available templates
        test_get_available_templates()
        
        # Test 2: Generate standard protocol
        job_id = test_generate_standard_protocol()
        
        # Test 3: Generate with labs (if available)
        # job_id_with_labs = test_generate_with_labs()
        
        # Test 4: Download protocol
        if job_id:
            test_download_protocol(job_id)
            test_get_status(job_id)
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS COMPLETED")
        print("=" * 60)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to API server")
        print("Make sure the server is running on http://localhost:8000")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")

if __name__ == "__main__":
    main()
