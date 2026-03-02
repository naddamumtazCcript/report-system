"""
Complete end-to-end test with token tracking
"""
import sys
import os
import json
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from test_profiles import TEST_PROFILES
from ai.knowledge_base import (
    calculate_bmr, calculate_dee, calculate_macros,
    analyze_symptom_drivers, generate_nutrition_recommendations,
    generate_supplement_recommendations, generate_lifestyle_recommendations,
    print_token_summary, get_token_summary
)
from ai.pattern_detector import detect_patterns

def test_full_protocol(profile_name, client_data):
    """Test complete protocol generation with token tracking"""
    print(f"\n{'='*60}")
    print(f"TESTING: {profile_name}")
    print(f"Client: {client_data['personal_info']['name']}")
    print(f"{'='*60}")
    
    # Pattern Detection
    print("\n[1/6] Pattern Detection...")
    patterns = detect_patterns(client_data)
    print(f"✓ Patterns: {', '.join([k for k, v in patterns.items() if v])}")
    
    # Metabolic Calculations
    print("\n[2/6] Metabolic Calculations...")
    weight_lbs = client_data['personal_info']['weight_lbs']
    height_inches = client_data['personal_info']['height_inches']
    age = client_data['personal_info']['age']
    sex = client_data['personal_info']['sex']
    activity = client_data['fitness']['activity_level']
    
    bmr = calculate_bmr(weight_lbs, height_inches, age, sex)
    dee = calculate_dee(bmr, activity)
    macros = calculate_macros(weight_lbs, dee)
    print(f"✓ BMR: {bmr} cal, DEE: {dee} cal")
    print(f"✓ Macros: P={macros['protein_g']}g, C={macros['carbs_g']}g, F={macros['fat_g']}g")
    
    # AI Operations with token tracking
    print("\n[3/6] Symptom Analysis (AI)...")
    symptom_analysis = analyze_symptom_drivers(client_data)
    print(f"✓ Analyzed {len(symptom_analysis.get('symptom_drivers', []))} symptoms")
    
    print("\n[4/6] Nutrition Recommendations (AI)...")
    nutrition = generate_nutrition_recommendations(client_data)
    print(f"✓ Generated {len(nutrition.get('core_habits', []))} core habits")
    
    print("\n[5/6] Supplement Recommendations (AI)...")
    supplements = generate_supplement_recommendations(client_data)
    print(f"✓ Generated {len(supplements.get('active_supplements', []))} supplements")
    
    print("\n[6/6] Lifestyle Recommendations (AI)...")
    lifestyle = generate_lifestyle_recommendations(client_data)
    print(f"✓ Generated lifestyle plan")
    
    print(f"\n{'='*60}")
    print(f"PROTOCOL COMPLETE: {profile_name}")
    print(f"{'='*60}")

if __name__ == "__main__":
    # Test with PCOS profile
    profile = "pcos_profile"
    client_data = TEST_PROFILES[profile]
    
    print("\n" + "="*60)
    print("FULL PROTOCOL TEST WITH TOKEN TRACKING")
    print("="*60)
    
    test_full_protocol(profile, client_data)
    
    # Print token summary
    print_token_summary()
    
    # Save token summary
    summary = get_token_summary()
    output_file = "tests/token_usage_report.json"
    with open(output_file, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"Token usage report saved to: {output_file}")
