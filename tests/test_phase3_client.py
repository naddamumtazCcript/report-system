"""
Test Phase 3: Client Chat API Endpoints
"""
import requests
import json
from pathlib import Path

BASE_URL = "http://localhost:8000/api"

def test_phase_3():
    """Test client chat API endpoints"""
    print("=" * 60)
    print("PHASE 3: CLIENT CHAT API TEST")
    print("=" * 60)
    
    # Load protocol
    protocol_path = Path("data/client_protocols/jessica/protocol.md")
    if not protocol_path.exists():
        print("❌ Protocol not found. Run Phase 1 test first.")
        return False
    
    protocol_content = protocol_path.read_text(encoding='utf-8')
    
    # Test 1: Initialize client
    print("\n[Test 1] Initialize client protocol...")
    response = requests.post(f"{BASE_URL}/client/initialize", json={
        "client_id": "jessica_api",
        "protocol_content": protocol_content,
        "metadata": {
            "name": "Jessica",
            "created_at": "2024-02-25"
        }
    })
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Client initialized: {data['chunks_indexed']} chunks")
    else:
        print(f"❌ Failed: {response.text}")
        return False
    
    # Test 2: Chat - Ask about supplements
    print("\n[Test 2] Chat - Ask about supplements...")
    response = requests.post(f"{BASE_URL}/client/chat", json={
        "client_id": "jessica_api",
        "message": "What supplements should I take?"
    })
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Response: {data['response'][:150]}...")
        print(f"Sources: {data['sources']}")
        print("✅ Chat response received")
    else:
        print(f"❌ Failed: {response.text}")
        return False
    
    # Test 3: Chat - Ask about nutrition
    print("\n[Test 3] Chat - Ask about nutrition...")
    response = requests.post(f"{BASE_URL}/client/chat", json={
        "client_id": "jessica_api",
        "message": "How many calories should I eat?"
    })
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Response: {data['response'][:150]}...")
        print(f"Sources: {data['sources']}")
        print("✅ Chat response received")
    else:
        print(f"❌ Failed: {response.text}")
        return False
    
    # Test 4: Chat with conversation history
    print("\n[Test 4] Chat with conversation history...")
    response = requests.post(f"{BASE_URL}/client/chat", json={
        "client_id": "jessica_api",
        "message": "Why do I need that amount?",
        "conversation_history": [
            {"role": "user", "content": "How many calories should I eat?"},
            {"role": "assistant", "content": "You should eat 2198 calories daily."}
        ]
    })
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Response: {data['response'][:150]}...")
        print("✅ Conversation history works")
    else:
        print(f"❌ Failed: {response.text}")
        return False
    
    # Test 5: Get protocol
    print("\n[Test 5] Get client protocol...")
    response = requests.get(f"{BASE_URL}/client/protocol/jessica_api")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Protocol retrieved: {len(data['protocol'])} characters")
        print(f"   Metadata: {data['metadata']}")
    else:
        print(f"❌ Failed: {response.text}")
        return False
    
    # Test 6: Non-existent client
    print("\n[Test 6] Test non-existent client...")
    response = requests.post(f"{BASE_URL}/client/chat", json={
        "client_id": "nonexistent",
        "message": "Hello?"
    })
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    if response.status_code == 404:
        print("✅ Correctly returned 404 for non-existent client")
    else:
        print(f"❌ Should have returned 404, got {response.status_code}")
        return False
    
    print("\n" + "=" * 60)
    print("✅ PHASE 3 COMPLETE: All API tests passed!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    print("\n⚠️  Make sure API server is running:")
    print("   cd src && uvicorn api.app:app --reload\n")
    
    try:
        test_phase_3()
    except requests.exceptions.ConnectionError:
        print("\n❌ Could not connect to API server.")
        print("   Start the server first: cd src && uvicorn api.app:app --reload")
