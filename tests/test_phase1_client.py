"""
Test Phase 1: Client Context Management
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from ai.client_context import ClientContext

# Import config values directly
CLIENT_PROTOCOLS_DIR = Path("data/client_protocols")
CLIENT_PROTOCOLS_DIR.mkdir(parents=True, exist_ok=True)

def test_phase_1():
    """Test client context management"""
    print("=" * 60)
    print("PHASE 1: CLIENT CONTEXT MANAGEMENT TEST")
    print("=" * 60)
    
    # Test 1: Save protocol for a client
    print("\n[Test 1] Saving protocol for client 'jessica'...")
    
    # Load existing protocol from output
    sample_protocol_path = Path("data/output")
    protocol_files = list(sample_protocol_path.glob("*.md"))
    
    if not protocol_files:
        print("❌ No protocol found in data/output/")
        print("   Run practitioner agent first to generate a protocol")
        return False
    
    protocol_file = protocol_files[0]
    protocol_content = protocol_file.read_text(encoding='utf-8')
    
    # Save for client
    client = ClientContext("jessica", CLIENT_PROTOCOLS_DIR)
    metadata = {
        "name": "Jessica",
        "created_at": "2024-02-25",
        "practitioner": "Dr. Smith"
    }
    client.save_protocol(protocol_content, metadata)
    print(f"✅ Protocol saved to: {client.protocol_path}")
    
    # Test 2: Load protocol
    print("\n[Test 2] Loading protocol...")
    loaded_content = client.load_protocol()
    print(f"✅ Protocol loaded: {len(loaded_content)} characters")
    
    # Test 3: Load metadata
    print("\n[Test 3] Loading metadata...")
    loaded_metadata = client.load_metadata()
    print(f"✅ Metadata: {loaded_metadata}")
    
    # Test 4: Check existence
    print("\n[Test 4] Checking protocol existence...")
    exists = client.exists()
    print(f"✅ Protocol exists: {exists}")
    
    # Test 5: Parse sections
    print("\n[Test 5] Parsing protocol sections...")
    sections = client.parse_sections()
    print(f"✅ Found {len(sections)} sections:")
    for section_name in sections.keys():
        section_preview = sections[section_name][:100].replace('\n', ' ')
        print(f"   - {section_name}: {section_preview}...")
    
    # Test 6: Non-existent client
    print("\n[Test 6] Testing non-existent client...")
    fake_client = ClientContext("nonexistent", CLIENT_PROTOCOLS_DIR)
    try:
        fake_client.load_protocol()
        print("❌ Should have raised FileNotFoundError")
        return False
    except FileNotFoundError as e:
        print(f"✅ Correctly raised error: {e}")
    
    print("\n" + "=" * 60)
    print("✅ PHASE 1 COMPLETE: All tests passed!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = test_phase_1()
    sys.exit(0 if success else 1)
