"""
End-to-End Protocol Agent Test
Tests complete pipeline: JSON input → Lab analysis → PDF generation
"""
import sys
from pathlib import Path
import json

sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.json_parser import parse_questionnaire_json
from core.schema import LabResult
from ai.lab_analyzer import analyze_lab_results, format_lab_summary_for_protocol
from core.html_pdf_generator import generate_protocol_pdf
from datetime import datetime


def load_json_file(filepath: str):
    with open(filepath, 'r') as f:
        return json.load(f)


def process_lab_report(lab_data: dict) -> list:
    lab_results = []
    for report in lab_data.get('reports', []):
        for result in report.get('results', []):
            lab_results.append(LabResult(
                test_name=result.get('test_name', ''),
                value=result.get('value', ''),
                unit=result.get('unit', ''),
                reference_range=result.get('reference_range', ''),
                flag=result.get('flag', '')
            ))
    return analyze_lab_results(lab_results)


def main():
    print("=" * 80)
    print("PROTOCOL AGENT - END-TO-END TEST")
    print("=" * 80)

    print("\n[1/5] Loading questionnaire JSON...")
    questionnaire_data = load_json_file("test_intake_questionnaire.json")
    print(f"✓ Loaded: test_intake_questionnaire.json")

    print("\n[2/5] Parsing questionnaire data...")
    if 'answers' not in questionnaire_data:
        questionnaire_data = {'answers': questionnaire_data}
    intake_data = parse_questionnaire_json(questionnaire_data)
    print(f"✓ Parsed {len(intake_data)} fields")
    print(f"  - Client: {intake_data.get('client_name', 'Unknown')}")
    print(f"  - Main symptoms: {len(intake_data.get('main_symptoms', []))} symptoms")

    print("\n[3/5] Loading and analyzing lab report...")
    lab_data = load_json_file("dutch_lab_report.json")
    lab_results = process_lab_report(lab_data)
    markers_with_summaries = [r for r in lab_results if r.summary]
    print(f"✓ Loaded: dutch_lab_report.json")
    print(f"✓ Processed {len(lab_results)} lab markers")
    print(f"✓ Generated AI summaries for {len(markers_with_summaries)} out-of-range markers")

    print("\n[4/5] Formatting lab summary...")
    lab_summary_html = format_lab_summary_for_protocol(lab_results)
    print(f"✓ Lab summary formatted ({len(lab_summary_html)} characters)")

    print("\n[5/5] Generating protocol PDF...")
    protocol_data = {
        'client_name': intake_data.get('client_name', 'Client'),
        'date': datetime.now().strftime('%B %d, %Y'),
        'focus_items': [
            'Regulate menstrual cycle',
            'Increase energy levels',
            'Improve sleep quality',
            'Support hormone balance'
        ],
        'concerns': [
            {
                'description': 'Chronic fatigue and low energy levels (8/10 severity)',
                'drivers': 'Elevated cortisol (especially evening), blood sugar dysregulation, PCOS'
            },
            {
                'description': 'Irregular menstrual cycles (35-45 days)',
                'drivers': 'Elevated estrogen, PCOS, hormonal imbalance'
            },
            {
                'description': 'Difficulty losing weight despite diet and exercise',
                'drivers': 'PCOS, insulin resistance, elevated cortisol'
            }
        ],
        'lab_review_content': lab_summary_html,
        'primary_nutrition_goal': 'Balance blood sugar, support hormone health, and reduce inflammation',
        'hydration_target': '80-100 oz water daily',
        'core_habits': [
            'Eat protein with every meal (25-30g per meal)',
            'Include healthy fats to support hormone production',
            'Focus on low-glycemic carbohydrates',
            'Avoid dairy (noted sensitivity causing bloating)',
            'Limit alcohol to 1-2 drinks per week'
        ],
        'calories': '1800-2000 kcal',
        'protein': '120-140g (30-35g per meal)',
        'carbohydrates': '150-180g (focus on low-glycemic)',
        'fat': '60-70g (healthy fats)',
        'fiber': '30-35g',
        'daily_steps_target': '8,000-10,000 steps',
        'strength_frequency': '3-4x per week',
        'strength_split': 'Full body or Upper/Lower split',
        'stress_supports': [
            'Evening cortisol management: no screens 1 hour before bed',
            'Morning sunlight exposure within 30 minutes of waking',
            'Breathwork or meditation 10 minutes daily',
            'Prioritize 7-8 hours sleep',
            'Consider adaptogenic herbs (Ashwagandha, Rhodiola)'
        ],
        'active_supplements_content': '''
            <strong>Core Supplements:</strong><br>
            • <strong>Inositol (Myo-inositol + D-chiro-inositol 40:1)</strong> - 2000mg twice daily with meals<br>
            • <strong>Magnesium Glycinate</strong> - 300-400mg before bed<br>
            • <strong>Omega-3 (EPA/DHA)</strong> - 2000mg daily with food<br>
            • <strong>Vitamin D3 + K2</strong> - 4000 IU D3 + 100mcg K2 daily<br>
            • <strong>DIM (Diindolylmethane)</strong> - 200mg daily with food<br>
            • <strong>Chromium Picolinate</strong> - 200mcg daily
        ''',
        'pause_supplements': [
            'Current multivitamin (replace with targeted supplements above)',
            'Reduce fish oil to avoid overlap with Omega-3 recommendation'
        ]
    }

    Path("output").mkdir(exist_ok=True)
    output_path = "output/sarah_mitchell_protocol.pdf"
    result = generate_protocol_pdf(protocol_data, output_path)

    print(f"✓ Protocol generated: {result}")
    print("\n" + "=" * 80)
    print("TEST COMPLETE - SUMMARY")
    print("=" * 80)
    print(f"Client: {protocol_data['client_name']}")
    print(f"Date: {protocol_data['date']}")
    print(f"Lab Markers Analyzed: {len(lab_results)}")
    print(f"AI Summaries Generated: {len(markers_with_summaries)}")
    print(f"Output: {result}")
    print("=" * 80)


if __name__ == "__main__":
    main()
