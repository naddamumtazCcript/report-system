"""
Test Generate Protocol API
"""
import requests
import json
from pathlib import Path

API_URL = "http://localhost:8000/api"

def test_get_templates():
    """Test GET /api/templates"""
    print("\n" + "="*60)
    print("TEST 1: GET /api/templates")
    print("="*60)
    
    response = requests.get(f"{API_URL}/templates")
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Success!")
        print(f"Available templates: {len(data['templates'])}")
        for t in data['templates']:
            print(f"  - {t['metadata']['name']} ({t['type']})")
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)

def test_get_libraries():
    """Test GET /api/library/list"""
    print("\n" + "="*60)
    print("TEST 2: GET /api/library/list")
    print("="*60)
    
    response = requests.get(f"{API_URL}/library/list")
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Success!")
        print(f"Available libraries: {len(data['libraries'])}")
        for lib in data['libraries']:
            print(f"  - {lib['name']}")
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)

def test_generate_protocol():
    """Test POST /api/generate-protocol"""
    print("\n" + "="*60)
    print("TEST 3: POST /api/generate-protocol")
    print("="*60)
    
    # Check if intake file exists
    intake_file = Path("data/jessica_intake.pdf")
    if not intake_file.exists():
        print(f"❌ File not found: {intake_file}")
        return
    
    # Prepare request
    files = {
        'intake_file': ('jessica_intake.pdf', open(intake_file, 'rb'), 'application/pdf')
    }
    
    data = {
        'patient_id': 'patient_001',
        'template_type': 'standard_protocol',
        'selected_libraries': json.dumps([
            'BeBalancedNutritionLibrary',
            'BeBalancedSupplementLibrary',
            'BeBalancedLifestyleLibrary'
        ])
    }
    
    print(f"Sending request...")
    print(f"  Patient: {data['patient_id']}")
    print(f"  Template: {data['template_type']}")
    print(f"  File: {intake_file.name}")
    
    response = requests.post(
        f"{API_URL}/generate-protocol",
        files=files,
        data=data
    )
    
    if response.status_code == 200:
        result = response.json()
        print("\n✅ Success!")
        print(f"  Job ID: {result['job_id']}")
        print(f"  Client: {result['output']['client_name']}")
        print(f"  Processing Time: {result['metadata']['processing_time']}")
        print(f"  Download URL: {result['output']['download_url']}")
        return result['job_id']
    else:
        print(f"\n❌ Failed: {response.status_code}")
        print(response.text)
        return None

def main():
    print("\n" + "="*60)
    print("GENERATE PROTOCOL API TESTS")
    print("="*60)
    print("\nMake sure server is running:")
    print("  cd src && python -m uvicorn api.app:app --reload")
    print("="*60)
    
    try:
        # Test 1: Get templates
        test_get_templates()
        
        # Test 2: Get libraries
        test_get_libraries()
        
        # Test 3: Generate protocol
        # test_generate_protocol()
        
        print("\n" + "="*60)
        print("✅ TESTS COMPLETE")
        print("="*60)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to API")
        print("Start the server: cd src && python -m uvicorn api.app:app --reload")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")

if __name__ == "__main__":
    main()
