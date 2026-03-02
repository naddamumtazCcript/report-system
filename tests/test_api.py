"""
Test Merged API
"""
import requests
from pathlib import Path

BASE_URL = "http://localhost:8000"

def test_health():
    response = requests.get(f"{BASE_URL}/health")
    print(f"✅ Health: {response.json()}")
    return response.status_code == 200

def test_list():
    response = requests.get(f"{BASE_URL}/api/library/list")
    data = response.json()
    print(f"\n📚 Libraries: {data['count']} files")
    return response.status_code == 200

def test_upload():
    test_pdf = Path(__file__).parent.parent / 'data' / 'jessica_intake.pdf'
    with open(test_pdf, 'rb') as f:
        files = {'file': ('test.pdf', f, 'application/pdf')}
        response = requests.post(f"{BASE_URL}/api/library/upload", files=files)
    
    if response.status_code == 200:
        print(f"\n📤 Upload: {response.json()['filename']}")
        return True
    print(f"❌ Failed: {response.text}")
    return False

def test_delete():
    response = requests.delete(f"{BASE_URL}/api/library/test.pdf")
    if response.status_code == 200:
        print(f"\n🗑️  Deleted: {response.json()['deleted_files']}")
        return True
    return False

if __name__ == "__main__":
    print("🧪 Testing Merged API\n")
    print("Start: cd src && uvicorn api.app:app --reload\n")
    input("Press Enter...")
    
    results = [
        ("Health", test_health()),
        ("List", test_list()),
        ("Upload", test_upload()),
        ("Delete", test_delete())
    ]
    
    print("\n" + "="*50)
    for name, passed in results:
        print(f"  {'✅' if passed else '❌'} {name}")
    print("="*50)
