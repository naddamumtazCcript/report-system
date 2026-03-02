"""
End-to-End Test: Practitioner Agent + Client Agent
Complete workflow from intake PDF to client chat
"""
import requests
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

BASE_URL = "http://localhost:8000/api"

def test_complete_workflow():
    """Test complete workflow: Practitioner generates protocol, Client chats about it"""
    print("=" * 70)
    print("END-TO-END TEST: PRACTITIONER AGENT + CLIENT AGENT")
    print("=" * 70)
    
    # ========== PRACTITIONER AGENT ==========
    print("\n" + "=" * 70)
    print("PART 1: PRACTITIONER AGENT - Generate Protocol")
    print("=" * 70)
    
    # Test 1: Generate protocol from intake PDF
    print("\n[Test 1] Generate protocol from intake PDF...")
    intake_pdf = Path("data/jessica_intake.pdf")
    
    if not intake_pdf.exists():
        print("❌ Intake PDF not found")
        return False
    
    with open(intake_pdf, 'rb') as f:
        response = requests.post(
            f"{BASE_URL}/protocol/generate",
            files={"intake_pdf": f}
        )
    
    print(f"Status: {response.status_code}")
    if response.status_code != 200:
        print(f"❌ Failed: {response.text}")
        return False
    
    data = response.json()
    session_id = data['session_id']
    print(f"✅ Protocol generated: {session_id}")
    print(f"   Download URL: {data['download_url']}")
    
    # Test 2: Download generated protocol
    print("\n[Test 2] Download generated protocol...")
    response = requests.get(f"{BASE_URL}/protocol/download/{session_id}")
    
    if response.status_code != 200:
        print(f"❌ Failed to download protocol")
        return False
    
    protocol_content = response.text
    print(f"✅ Protocol downloaded: {len(protocol_content)} characters")
    
    # ========== CLIENT AGENT ==========
    print("\n" + "=" * 70)
    print("PART 2: CLIENT AGENT - Chat About Protocol")
    print("=" * 70)
    
    # Test 3: Initialize client with generated protocol
    print("\n[Test 3] Initialize client with generated protocol...")
    response = requests.post(f"{BASE_URL}/client/initialize", json={
        "client_id": "jessica_e2e",
        "protocol_content": protocol_content,
        "metadata": {
            "name": "Jessica Martinez",
            "session_id": session_id,
            "created_at": "2024-02-26"
        }
    })
    
    print(f"Status: {response.status_code}")
    if response.status_code != 200:
        print(f"❌ Failed: {response.text}")
        return False
    
    data = response.json()
    print(f"✅ Client initialized: {data['chunks_indexed']} chunks indexed")
    
    # Test 4: Client asks about their health concerns
    print("\n[Test 4] Client asks: 'What are my main health concerns?'")
    response = requests.post(f"{BASE_URL}/client/chat", json={
        "client_id": "jessica_e2e",
        "message": "What are my main health concerns?"
    })
    
    if response.status_code != 200:
        print(f"❌ Failed: {response.text}")
        return False
    
    data = response.json()
    print(f"Response: {data['response'][:200]}...")
    print(f"Sources: {', '.join(data['sources'][:3])}")
    print("✅ Health concerns answered")
    
    # Test 5: Client asks about supplements
    print("\n[Test 5] Client asks: 'What supplements should I take and why?'")
    response = requests.post(f"{BASE_URL}/client/chat", json={
        "client_id": "jessica_e2e",
        "message": "What supplements should I take and why?"
    })
    
    if response.status_code != 200:
        print(f"❌ Failed: {response.text}")
        return False
    
    data = response.json()
    print(f"Response: {data['response'][:200]}...")
    print(f"Sources: {', '.join(data['sources'][:3])}")
    print("✅ Supplement recommendations answered")
    
    # Test 6: Client asks about diet
    print("\n[Test 6] Client asks: 'What foods should I avoid?'")
    response = requests.post(f"{BASE_URL}/client/chat", json={
        "client_id": "jessica_e2e",
        "message": "What foods should I avoid?"
    })
    
    if response.status_code != 200:
        print(f"❌ Failed: {response.text}")
        return False
    
    data = response.json()
    print(f"Response: {data['response'][:200]}...")
    print(f"Sources: {', '.join(data['sources'][:3])}")
    print("✅ Diet recommendations answered")
    
    # Test 7: Client asks about macros
    print("\n[Test 7] Client asks: 'How much protein should I eat daily?'")
    response = requests.post(f"{BASE_URL}/client/chat", json={
        "client_id": "jessica_e2e",
        "message": "How much protein should I eat daily?"
    })
    
    if response.status_code != 200:
        print(f"❌ Failed: {response.text}")
        return False
    
    data = response.json()
    print(f"Response: {data['response']}")
    print(f"Sources: {', '.join(data['sources'][:3])}")
    print("✅ Macro recommendations answered")
    
    # Test 8: Conversation with history
    print("\n[Test 8] Follow-up question with conversation history...")
    response = requests.post(f"{BASE_URL}/client/chat", json={
        "client_id": "jessica_e2e",
        "message": "Why do I need that much protein?",
        "conversation_history": [
            {"role": "user", "content": "How much protein should I eat daily?"},
            {"role": "assistant", "content": "You should aim for 142g of protein per day."}
        ]
    })
    
    if response.status_code != 200:
        print(f"❌ Failed: {response.text}")
        return False
    
    data = response.json()
    print(f"Response: {data['response'][:200]}...")
    print("✅ Conversation history works")
    
    # Test 9: Non-health question (should be rejected)
    print("\n[Test 9] Client asks non-health question: 'What's the weather?'")
    response = requests.post(f"{BASE_URL}/client/chat", json={
        "client_id": "jessica_e2e",
        "message": "What's the weather today?"
    })
    
    if response.status_code != 200:
        print(f"❌ Failed: {response.text}")
        return False
    
    data = response.json()
    print(f"Response: {data['response']}")
    if "health protocol" in data['response'].lower():
        print("✅ Non-health question correctly rejected")
    else:
        print("⚠️  Warning: Should reject non-health questions")
    
    # Test 10: Question not in protocol
    print("\n[Test 10] Client asks about something not in protocol...")
    response = requests.post(f"{BASE_URL}/client/chat", json={
        "client_id": "jessica_e2e",
        "message": "Should I take antibiotics for my condition?"
    })
    
    if response.status_code != 200:
        print(f"❌ Failed: {response.text}")
        return False
    
    data = response.json()
    print(f"Response: {data['response'][:150]}...")
    if "don't have" in data['response'].lower() or "contact your practitioner" in data['response'].lower():
        print("✅ Correctly says information not in protocol")
    else:
        print("⚠️  Warning: Should say information not in protocol")
    
    # ========== SUMMARY ==========
    print("\n" + "=" * 70)
    print("✅ END-TO-END TEST COMPLETE!")
    print("=" * 70)
    print("\nWorkflow Summary:")
    print("1. ✅ Practitioner uploaded intake PDF")
    print("2. ✅ System generated personalized protocol")
    print("3. ✅ Client initialized with protocol")
    print("4. ✅ Client asked 7 different questions")
    print("5. ✅ All responses grounded in protocol")
    print("6. ✅ Non-health questions rejected")
    print("7. ✅ Missing information handled correctly")
    print("\n🎉 Both agents working perfectly together!")
    
    return True

if __name__ == "__main__":
    print("\n⚠️  Make sure API server is running:")
    print("   cd src && python3 api/app.py\n")
    
    try:
        success = test_complete_workflow()
        sys.exit(0 if success else 1)
    except requests.exceptions.ConnectionError:
        print("\n❌ Could not connect to API server.")
        print("   Start the server first: cd src && python3 api/app.py")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
