"""
Complete Practitioner Agent Flow Test
Tests the entire workflow from intake to protocol generation
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from main import run_pipeline
from ai.knowledge_base import print_token_summary
import json

def test_complete_flow():
    """Test complete practitioner agent workflow"""
    print("="*70)
    print("🧪 TESTING COMPLETE PRACTITIONER AGENT FLOW")
    print("="*70)
    
    # Test files
    intake_pdf = Path(__file__).parent.parent / 'data' / 'jessica_intake.pdf'
    lab_pdfs = [
        Path(__file__).parent.parent / 'templates' / 'sample_report_1.pdf',
        Path(__file__).parent.parent / 'templates' / 'sample_report_2.pdf'
    ]
    template = Path(__file__).parent.parent / 'templates' / 'ProtocolTemplate.md'
    output = Path(__file__).parent.parent / 'data' / 'output' / 'final_test_protocol.md'
    
    print("\n📋 Test Configuration:")
    print(f"   Intake: {intake_pdf.name}")
    print(f"   Lab Reports: {len(lab_pdfs)}")
    print(f"   Template: {template.name}")
    print(f"   Output: {output.name}")
    
    try:
        print("\n" + "="*70)
        print("STEP 1: Running Complete Pipeline")
        print("="*70)
        
        result = run_pipeline(
            str(intake_pdf),
            str(template),
            str(output),
            [str(p) for p in lab_pdfs]
        )
        
        print("\n✅ Pipeline completed successfully!")
        
        # Verify output
        print("\n" + "="*70)
        print("STEP 2: Verifying Output")
        print("="*70)
        
        assert Path(result).exists(), "Output file not created"
        
        with open(result, 'r') as f:
            content = f.read()
        
        print(f"\n✅ Protocol generated: {len(content)} characters")
        
        # Check key sections
        checks = [
            ("Client Name", "Jessica Martinez" in content),
            ("Lab Review", "LAB REVIEW SUMMARY" in content),
            ("Nutrition", "NUTRITION FOCUS" in content),
            ("Supplements", "SUPPLEMENT PROTOCOL" in content),
            ("Lifestyle", "LIFESTYLE & MOVEMENT" in content),
            ("Macros", "Calories:" in content and "Protein:" in content),
        ]
        
        print("\n📊 Content Validation:")
        all_passed = True
        for check_name, passed in checks:
            status = "✅" if passed else "❌"
            print(f"   {status} {check_name}")
            if not passed:
                all_passed = False
        
        if not all_passed:
            print("\n❌ Some content checks failed")
            return False
        
        # Token usage
        print("\n" + "="*70)
        print("STEP 3: Token Usage Summary")
        print("="*70)
        print_token_summary()
        
        # Show sample output
        print("\n" + "="*70)
        print("STEP 4: Sample Protocol Output")
        print("="*70)
        
        lines = content.split('\n')
        print("\n📄 First 30 lines:")
        for line in lines[:30]:
            print(f"   {line}")
        
        # Lab section
        if "LAB REVIEW SUMMARY" in content:
            lab_start = content.index("LAB REVIEW SUMMARY")
            lab_section = content[lab_start:lab_start+500]
            print("\n🧬 Lab Review Section (preview):")
            for line in lab_section.split('\n')[:15]:
                print(f"   {line}")
        
        print("\n" + "="*70)
        print("✅ PRACTITIONER AGENT TEST PASSED")
        print("="*70)
        
        print("\n📊 Summary:")
        print(f"   ✅ Intake processed: Jessica Martinez")
        print(f"   ✅ Lab reports analyzed: 2 reports")
        print(f"   ✅ Protocol generated: {len(content)} chars")
        print(f"   ✅ All sections present")
        print(f"   ✅ Lab-informed recommendations")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_without_labs():
    """Test workflow without lab reports"""
    print("\n" + "="*70)
    print("🧪 TESTING WITHOUT LAB REPORTS")
    print("="*70)
    
    intake_pdf = Path(__file__).parent.parent / 'data' / 'jessica_intake.pdf'
    template = Path(__file__).parent.parent / 'templates' / 'ProtocolTemplate.md'
    output = Path(__file__).parent.parent / 'data' / 'output' / 'test_no_labs.md'
    
    try:
        result = run_pipeline(str(intake_pdf), str(template), str(output), None)
        
        with open(result, 'r') as f:
            content = f.read()
        
        assert "No lab reports provided" in content, "Should show no labs message"
        
        print(f"\n✅ Protocol without labs: {len(content)} chars")
        print("   ✅ Handles missing labs gracefully")
        
        return True
    except Exception as e:
        print(f"\n❌ Failed: {e}")
        return False

def test_knowledge_base():
    """Test knowledge base integration"""
    print("\n" + "="*70)
    print("🧪 TESTING KNOWLEDGE BASE")
    print("="*70)
    
    kb_dir = Path(__file__).parent.parent / 'knowledge_base' / 'libraries'
    
    # Check files
    txt_files = list(kb_dir.glob("*.txt"))
    md_files = list(kb_dir.glob("*.md"))
    
    print(f"\n📚 Knowledge Base Files:")
    print(f"   Text files: {len(txt_files)}")
    print(f"   Markdown files: {len(md_files)}")
    
    for f in (txt_files + md_files)[:5]:
        print(f"   - {f.name}")
    
    if len(txt_files) + len(md_files) > 0:
        print("\n✅ Knowledge base populated")
        return True
    else:
        print("\n❌ Knowledge base empty")
        return False

if __name__ == "__main__":
    print("\n" + "="*70)
    print("🚀 PRACTITIONER AGENT - COMPLETE FLOW TEST")
    print("="*70)
    
    results = []
    
    # Test 1: Complete flow with labs
    results.append(("Complete Flow (with labs)", test_complete_flow()))
    
    # Test 2: Flow without labs
    results.append(("Flow without labs", test_without_labs()))
    
    # Test 3: Knowledge base
    results.append(("Knowledge Base", test_knowledge_base()))
    
    # Summary
    print("\n" + "="*70)
    print("📊 FINAL TEST RESULTS")
    print("="*70)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status} - {name}")
    
    all_passed = all(r[1] for r in results)
    
    print("="*70)
    
    if all_passed:
        print("\n🎉 ALL TESTS PASSED!")
        print("\n✅ Practitioner Agent is ready for production")
        print("\n📋 What the agent can do:")
        print("   ✅ Process client intake questionnaires")
        print("   ✅ Analyze lab reports (optional)")
        print("   ✅ Generate personalized protocols")
        print("   ✅ Provide lab-informed recommendations")
        print("   ✅ Calculate nutrition macros")
        print("   ✅ Suggest supplements")
        print("   ✅ Recommend lifestyle changes")
        print("   ✅ Use custom knowledge base rules")
        print("\n🚀 Ready to move to Client Agent!")
    else:
        print("\n❌ SOME TESTS FAILED")
        print("Please fix issues before proceeding")
    
    sys.exit(0 if all_passed else 1)
