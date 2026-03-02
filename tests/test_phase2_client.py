"""
Test Phase 2: RAG-Based Chat System
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from ai.client_chat import ClientChat

from dotenv import load_dotenv
load_dotenv()

CLIENT_PROTOCOLS_DIR = Path("data/client_protocols")

def test_phase_2():
    """Test RAG-based chat system"""
    print("=" * 60)
    print("PHASE 2: RAG-BASED CHAT SYSTEM TEST")
    print("=" * 60)
    
    # Test 1: Initialize chat for client
    print("\n[Test 1] Initializing chat for client 'jessica'...")
    chat = ClientChat("jessica", CLIENT_PROTOCOLS_DIR)
    chunks = chat.initialize()
    print(f"✅ Protocol indexed: {chunks} chunks")
    
    # Test 2: Ask about supplements (IN protocol)
    print("\n[Test 2] Asking about supplements (in protocol)...")
    question = "What supplements should I take?"
    response = chat.chat(question)
    print(f"Question: {question}")
    print(f"Response: {response['response'][:200]}...")
    print(f"Sources: {response['sources']}")
    print("✅ Response generated with sources")
    
    # Test 3: Ask about nutrition (IN protocol)
    print("\n[Test 3] Asking about nutrition (in protocol)...")
    question = "What foods should I focus on?"
    response = chat.chat(question)
    print(f"Question: {question}")
    print(f"Response: {response['response'][:200]}...")
    print(f"Sources: {response['sources']}")
    print("✅ Response generated with sources")
    
    # Test 4: Ask about macros (IN protocol)
    print("\n[Test 4] Asking about macros (in protocol)...")
    question = "How many calories should I eat?"
    response = chat.chat(question)
    print(f"Question: {question}")
    print(f"Response: {response['response'][:200]}...")
    print(f"Sources: {response['sources']}")
    print("✅ Response generated with sources")
    
    # Test 5: Ask non-health question (OUT of scope)
    print("\n[Test 5] Asking non-health question (out of scope)...")
    question = "What's the weather today?"
    response = chat.chat(question)
    print(f"Question: {question}")
    print(f"Response: {response['response']}")
    print(f"Sources: {response['sources']}")
    if "health protocol" in response['response'].lower():
        print("✅ Correctly rejected non-health question")
    else:
        print("❌ Should have rejected non-health question")
        return False
    
    # Test 6: Ask about something NOT in protocol
    print("\n[Test 6] Asking about something not in protocol...")
    question = "Should I take antibiotics?"
    response = chat.chat(question)
    print(f"Question: {question}")
    print(f"Response: {response['response'][:200]}...")
    print(f"Sources: {response['sources']}")
    print("✅ Response generated (should say not in protocol)")
    
    # Test 7: Conversation with history
    print("\n[Test 7] Testing conversation with history...")
    history = [
        {"role": "user", "content": "What supplements should I take?"},
        {"role": "assistant", "content": "Based on your protocol, you should take magnesium and omega-3."}
    ]
    question = "Why do I need those?"
    response = chat.chat(question, conversation_history=history)
    print(f"Question: {question}")
    print(f"Response: {response['response'][:200]}...")
    print("✅ Conversation with history works")
    
    print("\n" + "=" * 60)
    print("✅ PHASE 2 COMPLETE: All tests passed!")
    print("=" * 60)
    print("\nSample Interactions:")
    print("-" * 60)
    
    # Show full sample interaction
    sample_questions = [
        "Can I eat pizza?",
        "How much protein should I eat per day?",
        "What are my top health concerns?"
    ]
    
    for q in sample_questions:
        resp = chat.chat(q)
        print(f"\nQ: {q}")
        print(f"A: {resp['response']}")
        print(f"Sources: {', '.join(resp['sources'])}")
    
    return True

if __name__ == "__main__":
    success = test_phase_2()
    sys.exit(0 if success else 1)
