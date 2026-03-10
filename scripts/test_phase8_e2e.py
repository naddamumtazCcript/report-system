"""
Phase 8: End-to-End Testing - Complete Workflow
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000/api/practitioner"

def test_complete_workflow():
    """Test: Generate → Edit → Finalize → Download → Reopen → Edit → Finalize"""
    
    print("=" * 60)
    print("TEST 1: COMPLETE WORKFLOW")
    print("=" * 60)
    
    # Step 1: Generate Protocol
    print("\n[1/8] Generating protocol...")
    files = {
        'questionnaire': open('data/jessica_intake.pdf', 'rb'),
        'lab_reports': open('lab_reports/Functional Bloodwork Panel.pdf', 'rb')
    }
    data = {
        'user_id': '3',
        'client_id': '3',
        'template_type': 'standard',
        'doc_types': json.dumps(['bloodwork']),
        'libraries': json.dumps(['BeBalancedNutritionLibrary'])
    }
    
    response = requests.post(f"{BASE_URL}/generate-protocol", files=files, data=data)
    assert response.status_code == 200, f"Generate failed: {response.text}"
    protocol_id = response.json()['protocol_id']
    print(f"✅ Protocol generated: ID {protocol_id}")
    
    # Step 2: Get Protocol
    print("\n[2/8] Getting protocol...")
    response = requests.get(f"{BASE_URL}/protocol/{protocol_id}")
    assert response.status_code == 200, f"Get failed: {response.text}"
    assert response.json()['status'] == 'draft'
    print(f"✅ Protocol retrieved: status={response.json()['status']}")
    
    # Step 3: Edit Protocol
    print("\n[3/8] Editing protocol...")
    edited_markdown = "# Edited Protocol\n\nThis is an edited version."
    response = requests.put(f"{BASE_URL}/edit-protocol/{protocol_id}", data={'markdown': edited_markdown})
    assert response.status_code == 200, f"Edit failed: {response.text}"
    print(f"✅ Protocol edited")
    
    # Step 4: Finalize Protocol
    print("\n[4/8] Finalizing protocol...")
    response = requests.post(f"{BASE_URL}/finalize-protocol/{protocol_id}")
    assert response.status_code == 200, f"Finalize failed: {response.text}"
    assert response.json()['status'] == 'final'
    pdf_url = response.json()['pdf_url']
    print(f"✅ Protocol finalized: PDF URL={pdf_url}")
    
    # Step 5: Download PDF (redirect)
    print("\n[5/8] Downloading PDF...")
    response = requests.get(f"{BASE_URL}/protocol/{protocol_id}/pdf", allow_redirects=False)
    assert response.status_code in [302, 307], f"Download failed: status={response.status_code}, body={response.text}"
    redirect_url = response.headers.get('location', '')
    assert 'cloudinary' in redirect_url, f"Expected Cloudinary URL, got: {redirect_url}"
    print(f"✅ PDF redirect: {redirect_url}")
    
    # Step 6: Reopen Protocol
    print("\n[6/8] Reopening protocol...")
    response = requests.post(f"{BASE_URL}/reopen-protocol/{protocol_id}")
    assert response.status_code == 200, f"Reopen failed: {response.text}"
    assert response.json()['status'] == 'draft'
    print(f"✅ Protocol reopened")
    
    # Step 7: Edit Again
    print("\n[7/8] Editing again...")
    edited_markdown_2 = "# Re-edited Protocol\n\nThis is the second edit."
    response = requests.put(f"{BASE_URL}/edit-protocol/{protocol_id}", data={'markdown': edited_markdown_2})
    assert response.status_code == 200, f"Edit 2 failed: {response.text}"
    print(f"✅ Protocol edited again")
    
    # Step 8: Finalize Again
    print("\n[8/8] Finalizing again...")
    response = requests.post(f"{BASE_URL}/finalize-protocol/{protocol_id}")
    assert response.status_code == 200, f"Finalize 2 failed: {response.text}"
    new_pdf_url = response.json()['pdf_url']
    print(f"✅ Protocol finalized again: PDF URL={new_pdf_url}")
    
    print("\n✅ COMPLETE WORKFLOW TEST PASSED\n")
    return protocol_id


def test_multiple_labs():
    """Test: Generate with multiple lab types"""
    
    print("=" * 60)
    print("TEST 2: MULTIPLE LAB TYPES")
    print("=" * 60)
    
    print("\n[1/1] Generating protocol with 2 lab types (bloodwork + gi_map)...")
    files = [
        ('questionnaire', open('data/jessica_intake.pdf', 'rb')),
        ('lab_reports', open('lab_reports/Functional Bloodwork Panel.pdf', 'rb')),
        ('lab_reports', open('lab_reports/GI-MAP Sample Report.pdf', 'rb'))
    ]
    data = {
        'user_id': '4',
        'client_id': '4',
        'template_type': 'standard',
        'doc_types': json.dumps(['bloodwork', 'gi_map']),
        'libraries': json.dumps(['BeBalancedNutritionLibrary'])
    }
    
    response = requests.post(f"{BASE_URL}/generate-protocol", files=files, data=data)
    assert response.status_code == 200, f"Generate failed: {response.text}"
    result = response.json()
    print(f"✅ Protocol generated: ID {result['protocol_id']}")
    print(f"   Labs processed: {result['lab_reports_processed']}")
    
    print("\n✅ MULTIPLE LAB TYPES TEST PASSED\n")
    return result['protocol_id']


def test_no_labs():
    """Test: Generate with no lab reports"""
    
    print("=" * 60)
    print("TEST 3: NO LAB REPORTS")
    print("=" * 60)
    
    print("\n[1/1] Generating protocol without labs...")
    files = {
        'questionnaire': open('data/jessica_intake.pdf', 'rb')
    }
    data = {
        'user_id': '5',
        'client_id': '5',
        'template_type': 'standard',
        'doc_types': json.dumps([]),
        'libraries': json.dumps(['BeBalancedNutritionLibrary'])
    }
    
    response = requests.post(f"{BASE_URL}/generate-protocol", files=files, data=data)
    assert response.status_code == 200, f"Generate failed: {response.text}"
    result = response.json()
    print(f"✅ Protocol generated: ID {result['protocol_id']}")
    print(f"   Labs processed: {result['lab_reports_processed']}")
    
    print("\n✅ NO LAB REPORTS TEST PASSED\n")
    return result['protocol_id']


def test_edge_cases():
    """Test: Edge cases and error handling"""
    
    print("=" * 60)
    print("TEST 4: EDGE CASES")
    print("=" * 60)
    
    # Test 1: Get non-existent protocol
    print("\n[1/5] Getting non-existent protocol...")
    response = requests.get(f"{BASE_URL}/protocol/99999")
    assert response.status_code == 404, "Should return 404"
    print(f"✅ Correctly returned 404")
    
    # Test 2: Edit finalized protocol
    print("\n[2/5] Editing finalized protocol (should fail)...")
    protocol_id = test_complete_workflow()  # Creates and finalizes
    response = requests.put(f"{BASE_URL}/edit-protocol/{protocol_id}", data={'markdown': 'test'})
    assert response.status_code == 400, "Should return 400"
    print(f"✅ Correctly returned 400")
    
    # Test 3: Finalize already finalized
    print("\n[3/5] Finalizing already finalized protocol (should fail)...")
    response = requests.post(f"{BASE_URL}/finalize-protocol/{protocol_id}")
    assert response.status_code == 400, "Should return 400"
    print(f"✅ Correctly returned 400")
    
    # Test 4: Download PDF from draft
    print("\n[4/5] Downloading PDF from draft protocol (should fail)...")
    response = requests.post(f"{BASE_URL}/reopen-protocol/{protocol_id}")  # Reopen to draft
    response = requests.get(f"{BASE_URL}/protocol/{protocol_id}/pdf")
    assert response.status_code == 400, "Should return 400"
    print(f"✅ Correctly returned 400")
    
    # Test 5: Reopen draft protocol
    print("\n[5/5] Reopening draft protocol (should fail)...")
    response = requests.post(f"{BASE_URL}/reopen-protocol/{protocol_id}")
    assert response.status_code == 400, "Should return 400"
    print(f"✅ Correctly returned 400")
    
    print("\n✅ EDGE CASES TEST PASSED\n")


def main():
    print("\n" + "=" * 60)
    print("PRACTITIONER AGENT - END-TO-END TESTING")
    print("=" * 60 + "\n")
    
    start_time = time.time()
    
    try:
        # Run test 2 (was failing before)
        test_multiple_labs()
        test_no_labs()
        test_edge_cases()
        
        elapsed = time.time() - start_time
        
        print("=" * 60)
        print("ALL TESTS PASSED ✅")
        print("=" * 60)
        print(f"Total time: {elapsed:.2f} seconds")
        print(f"Tests run: 3")
        print(f"Status: SUCCESS")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
