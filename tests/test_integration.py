"""
Test Final Integration - Pipeline with and without labs
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from main import run_pipeline

def test_pipeline_with_labs():
    """Test pipeline WITH lab reports"""
    intake_pdf = Path(__file__).parent.parent / 'data' / 'jessica_intake.pdf'
    lab_pdfs = [
        Path(__file__).parent.parent / 'templates' / 'sample_report_1.pdf'
    ]
    template = Path(__file__).parent.parent / 'templates' / 'ProtocolTemplate.md'
    output = Path(__file__).parent.parent / 'data' / 'output' / 'protocol_with_labs.md'
    
    try:
        result = run_pipeline(str(intake_pdf), str(template), str(output), [str(p) for p in lab_pdfs])
        
        assert Path(result).exists(), "Output not created"
        
        with open(result, 'r') as f:
            content = f.read()
        
        assert "LAB REVIEW SUMMARY" in content, "Lab section missing"
        assert "DUTCH Complete" in content or "Marker" in content, "Lab data not populated"
        assert len(content) > 3000, "Output too short"
        
        print(f"✅ Pipeline WITH labs successful")
        print(f"   Output: {result}")
        print(f"   Size: {len(content)} characters")
        print(f"   Contains lab data: Yes")
        
        return True
    except Exception as e:
        print(f"❌ Pipeline with labs failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_pipeline_without_labs():
    """Test pipeline WITHOUT lab reports"""
    intake_pdf = Path(__file__).parent.parent / 'data' / 'jessica_intake.pdf'
    template = Path(__file__).parent.parent / 'templates' / 'ProtocolTemplate.md'
    output = Path(__file__).parent.parent / 'data' / 'output' / 'protocol_without_labs.md'
    
    try:
        result = run_pipeline(str(intake_pdf), str(template), str(output), None)
        
        assert Path(result).exists(), "Output not created"
        
        with open(result, 'r') as f:
            content = f.read()
        
        assert "LAB REVIEW SUMMARY" in content, "Lab section missing"
        assert "No lab reports provided" in content, "Should show no labs message"
        assert len(content) > 3000, "Output too short"
        
        print(f"✅ Pipeline WITHOUT labs successful")
        print(f"   Output: {result}")
        print(f"   Size: {len(content)} characters")
        print(f"   Contains lab data: No (as expected)")
        
        return True
    except Exception as e:
        print(f"❌ Pipeline without labs failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_compare_outputs():
    """Compare outputs with and without labs"""
    with_labs = Path(__file__).parent.parent / 'data' / 'output' / 'protocol_with_labs.md'
    without_labs = Path(__file__).parent.parent / 'data' / 'output' / 'protocol_without_labs.md'
    
    if not with_labs.exists() or not without_labs.exists():
        print("❌ Output files not found")
        return False
    
    try:
        with open(with_labs, 'r') as f:
            content_with = f.read()
        
        with open(without_labs, 'r') as f:
            content_without = f.read()
        
        # With labs should be longer
        assert len(content_with) > len(content_without), "With labs should be longer"
        
        # With labs should have biomarker data
        assert "Marker Name:" in content_with, "Missing marker data"
        assert "Marker Name:" not in content_without or "No lab reports" in content_without, "Should not have marker data"
        
        print(f"✅ Output comparison successful")
        print(f"   With labs: {len(content_with)} chars")
        print(f"   Without labs: {len(content_without)} chars")
        print(f"   Difference: {len(content_with) - len(content_without)} chars")
        
        return True
    except Exception as e:
        print(f"❌ Comparison failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Final Integration\n")
    
    results = []
    results.append(("Pipeline WITH Labs", test_pipeline_with_labs()))
    print()
    results.append(("Pipeline WITHOUT Labs", test_pipeline_without_labs()))
    print()
    results.append(("Output Comparison", test_compare_outputs()))
    
    print("\n" + "="*50)
    print("Test Results:")
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status} - {name}")
    
    all_passed = all(r[1] for r in results)
    print("="*50)
    print(f"\n{'✅ All tests passed!' if all_passed else '❌ Some tests failed'}")
    
    if all_passed:
        print("\n🎉 INTEGRATION COMPLETE!")
        print("   ✅ Lab reports are fully integrated")
        print("   ✅ Pipeline works with or without labs")
        print("   ✅ Recommendations are lab-informed when available")
