import sys
import os
import json
import time
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from test_profiles import TEST_PROFILES
from ai.knowledge_base import (
    calculate_bmr, calculate_dee, calculate_macros,
    analyze_symptom_drivers, generate_nutrition_recommendations,
    generate_supplement_recommendations, generate_lifestyle_recommendations
)
from ai.pattern_detector import detect_patterns

def validate_profile(profile_name, client_data):
    """Test a single profile and validate outputs"""
    print(f"\n{'='*60}")
    print(f"TESTING: {profile_name}")
    print(f"{'='*60}")
    
    results = {
        "profile": profile_name,
        "client_name": client_data['personal_info']['name'],
        "timestamp": datetime.now().isoformat(),
        "tests": {},
        "cost_estimate": 0,
        "errors": []
    }
    
    # Test 1: Pattern Detection
    print("\n[1/6] Pattern Detection...")
    try:
        patterns = detect_patterns(client_data)
        results['tests']['patterns'] = {
            "status": "PASS",
            "detected": [k for k, v in patterns.items() if v]
        }
        print(f"✓ Detected patterns: {', '.join(results['tests']['patterns']['detected'])}")
    except Exception as e:
        results['tests']['patterns'] = {"status": "FAIL", "error": str(e)}
        results['errors'].append(f"Pattern detection: {e}")
        print(f"✗ Error: {e}")
    
    # Test 2: BMR/DEE Calculations
    print("\n[2/6] Metabolic Calculations...")
    try:
        weight_lbs = client_data['personal_info']['weight_lbs']
        height_inches = client_data['personal_info']['height_inches']
        age = client_data['personal_info']['age']
        sex = client_data['personal_info']['sex']
        activity = client_data['fitness']['activity_level']
        
        bmr = calculate_bmr(weight_lbs, height_inches, age, sex)
        dee = calculate_dee(bmr, activity)
        macros = calculate_macros(weight_lbs, dee)
        results['tests']['metabolic'] = {
            "status": "PASS",
            "bmr": bmr,
            "dee": dee,
            "macros": macros
        }
        print(f"✓ BMR: {bmr} cal, DEE: {dee} cal")
        print(f"✓ Macros: P={macros['protein_g']}g, C={macros['carbs_g']}g, F={macros['fat_g']}g")
    except Exception as e:
        results['tests']['metabolic'] = {"status": "FAIL", "error": str(e)}
        results['errors'].append(f"Metabolic calculations: {e}")
        print(f"✗ Error: {e}")
    
    # Test 3: Symptom Analysis (AI)
    print("\n[3/6] Symptom Analysis (AI)...")
    try:
        start = time.time()
        symptom_analysis = analyze_symptom_drivers(client_data)
        elapsed = time.time() - start
        
        if symptom_analysis and 'symptom_drivers' in symptom_analysis:
            results['tests']['symptom_analysis'] = {
                "status": "PASS",
                "count": len(symptom_analysis['symptom_drivers']),
                "time_seconds": round(elapsed, 2)
            }
            results['cost_estimate'] += 0.002
            print(f"✓ Analyzed {len(symptom_analysis['symptom_drivers'])} symptoms in {elapsed:.2f}s")
        else:
            results['tests']['symptom_analysis'] = {"status": "FAIL", "error": "Empty response"}
            results['errors'].append("Symptom analysis returned empty")
            print(f"✗ Empty response")
    except Exception as e:
        results['tests']['symptom_analysis'] = {"status": "FAIL", "error": str(e)}
        results['errors'].append(f"Symptom analysis: {e}")
        print(f"✗ Error: {e}")
    
    # Test 4: Nutrition Recommendations (AI)
    print("\n[4/6] Nutrition Recommendations (AI)...")
    try:
        start = time.time()
        nutrition = generate_nutrition_recommendations(client_data)
        elapsed = time.time() - start
        
        if nutrition and 'core_habits' in nutrition:
            results['tests']['nutrition'] = {
                "status": "PASS",
                "habits_count": len(nutrition.get('core_habits', [])),
                "foods_filtered": 'foods_to_focus' in nutrition,
                "time_seconds": round(elapsed, 2)
            }
            results['cost_estimate'] += 0.003
            print(f"✓ Generated {len(nutrition.get('core_habits', []))} habits in {elapsed:.2f}s")
        else:
            results['tests']['nutrition'] = {"status": "FAIL", "error": "Empty response"}
            results['errors'].append("Nutrition recommendations empty")
            print(f"✗ Empty response")
    except Exception as e:
        results['tests']['nutrition'] = {"status": "FAIL", "error": str(e)}
        results['errors'].append(f"Nutrition recommendations: {e}")
        print(f"✗ Error: {e}")
    
    # Test 5: Supplement Recommendations (AI)
    print("\n[5/6] Supplement Recommendations (AI)...")
    try:
        start = time.time()
        supplements = generate_supplement_recommendations(client_data)
        elapsed = time.time() - start
        
        if supplements and 'active_supplements' in supplements:
            supp_count = len(supplements.get('active_supplements', []))
            results['tests']['supplements'] = {
                "status": "PASS" if supp_count <= 5 else "WARNING",
                "supplement_count": supp_count,
                "has_titration": 'titration_schedule' in supplements,
                "time_seconds": round(elapsed, 2)
            }
            results['cost_estimate'] += 0.003
            print(f"✓ Generated {supp_count} supplements in {elapsed:.2f}s")
            if supp_count > 5:
                print(f"⚠ Warning: More than 5 supplements recommended")
        else:
            results['tests']['supplements'] = {"status": "FAIL", "error": "Empty response"}
            results['errors'].append("Supplement recommendations empty")
            print(f"✗ Empty response")
    except Exception as e:
        results['tests']['supplements'] = {"status": "FAIL", "error": str(e)}
        results['errors'].append(f"Supplement recommendations: {e}")
        print(f"✗ Error: {e}")
    
    # Test 6: Lifestyle Recommendations (AI)
    print("\n[6/6] Lifestyle Recommendations (AI)...")
    try:
        start = time.time()
        lifestyle = generate_lifestyle_recommendations(client_data)
        elapsed = time.time() - start
        
        if lifestyle and 'daily_steps_target' in lifestyle:
            results['tests']['lifestyle'] = {
                "status": "PASS",
                "has_steps": bool(lifestyle.get('daily_steps_target')),
                "has_strength": bool(lifestyle.get('strength_training')),
                "time_seconds": round(elapsed, 2)
            }
            results['cost_estimate'] += 0.002
            print(f"✓ Generated lifestyle plan in {elapsed:.2f}s")
        else:
            results['tests']['lifestyle'] = {"status": "FAIL", "error": "Empty response"}
            results['errors'].append("Lifestyle recommendations empty")
            print(f"✗ Empty response")
    except Exception as e:
        results['tests']['lifestyle'] = {"status": "FAIL", "error": str(e)}
        results['errors'].append(f"Lifestyle recommendations: {e}")
        print(f"✗ Error: {e}")
    
    # Summary
    print(f"\n{'='*60}")
    passed = sum(1 for t in results['tests'].values() if t.get('status') == 'PASS')
    total = len(results['tests'])
    print(f"RESULTS: {passed}/{total} tests passed")
    print(f"ESTIMATED COST: ${results['cost_estimate']:.4f}")
    if results['errors']:
        print(f"ERRORS: {len(results['errors'])}")
    print(f"{'='*60}")
    
    return results

def run_all_tests():
    """Run validation on all test profiles"""
    print("\n" + "="*60)
    print("REPORT SYSTEM VALIDATION SUITE")
    print("="*60)
    
    all_results = []
    
    for profile_name, client_data in TEST_PROFILES.items():
        result = validate_profile(profile_name, client_data)
        all_results.append(result)
        time.sleep(1)  # Rate limiting
    
    # Overall summary
    print("\n" + "="*60)
    print("OVERALL SUMMARY")
    print("="*60)
    
    total_tests = sum(len(r['tests']) for r in all_results)
    total_passed = sum(sum(1 for t in r['tests'].values() if t.get('status') == 'PASS') for r in all_results)
    total_cost = sum(r['cost_estimate'] for r in all_results)
    avg_cost = total_cost / len(all_results)
    
    print(f"\nProfiles Tested: {len(all_results)}")
    print(f"Total Tests: {total_passed}/{total_tests} passed")
    print(f"Total Cost: ${total_cost:.4f}")
    print(f"Average Cost per Protocol: ${avg_cost:.4f}")
    
    # Check if within budget
    if avg_cost <= 0.014:
        print(f"✓ Cost within budget (target: $0.014)")
    else:
        print(f"⚠ Cost exceeds budget by ${avg_cost - 0.014:.4f}")
    
    # Save results
    output_file = f"tests/validation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    print(f"\nDetailed results saved to: {output_file}")
    
    return all_results

if __name__ == "__main__":
    run_all_tests()
