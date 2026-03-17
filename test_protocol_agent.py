"""
End-to-End Protocol Agent Test
Generates PDF 1 (Full Protocol) and PDF 2 (Lab Interpretation Report) + their JSONs
"""
import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.json_parser import parse_questionnaire_json
from core.schema import LabResult
from ai.lab_analyzer import analyze_lab_results, build_lab_markers_for_protocol
from ai.lab_report_generator import generate_lab_interpretation_json
from ai.knowledge_base import (
    get_nutrition_recommendations,
    analyze_symptom_drivers,
    generate_lifestyle_recommendations,
    generate_supplement_recommendations,
    generate_nutrition_recommendations,
    generate_what_to_expect,
    generate_goals_action_plan,
)
from core.html_pdf_generator import generate_protocol_pdf, generate_lab_report_pdf


def load_json(filepath):
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
    print("PROTOCOL AGENT — GENERATING PDF 1 (Protocol) + PDF 2 (Lab Report)")
    print("=" * 80)

    # --- Load inputs ---
    print("\n[1/7] Loading questionnaire and lab data...")
    questionnaire_data = load_json("test_intake_questionnaire.json")
    lab_data_raw = load_json("dutch_lab_report.json")

    intake_data = parse_questionnaire_json({'answers': questionnaire_data} if 'answers' not in questionnaire_data else questionnaire_data)
    # Fallback: read name directly from raw file if parser returns empty personal_info
    raw_pi = questionnaire_data.get('personal_info', {})
    first = raw_pi.get('legal_first_name') or intake_data.get('personal_info', {}).get('legal_first_name', 'Sarah')
    last = raw_pi.get('last_name') or intake_data.get('personal_info', {}).get('last_name', 'Mitchell')
    client_name = f"{first} {last}".strip() or 'Client'
    # Merge raw personal_info into intake_data so AI functions have it
    if not intake_data.get('personal_info', {}).get('legal_first_name'):
        intake_data['personal_info'] = raw_pi
    date_str = datetime.now().strftime('%B %d, %Y')
    print(f"✓ Client: {client_name}")

    # --- Process lab results ---
    print("\n[2/7] Processing lab markers...")
    lab_results = process_lab_report(lab_data_raw)
    lab_markers = build_lab_markers_for_protocol(lab_results)
    out_of_range_count = sum(1 for m in lab_markers if m['is_out_of_range'])
    print(f"✓ {len(lab_markers)} total markers | {out_of_range_count} out of range")

    # --- AI recommendations ---
    print("\n[3/7] Generating AI recommendations...")
    symptom_data = analyze_symptom_drivers(intake_data)
    lifestyle_data = generate_lifestyle_recommendations(intake_data)
    supplement_data = generate_supplement_recommendations(intake_data)
    nutrition_data = generate_nutrition_recommendations(intake_data)
    nutrition_calc = get_nutrition_recommendations(intake_data)
    macros = nutrition_calc.get('macros', {})
    what_to_expect = generate_what_to_expect(intake_data, supplement_data)
    goals_plan = generate_goals_action_plan(intake_data, nutrition_data, lifestyle_data, supplement_data)
    print("✓ AI recommendations generated")

    # --- Build Protocol JSON (PDF 1) ---
    print("\n[4/7] Building protocol JSON...")
    symptom_drivers = symptom_data.get('symptom_drivers', [])
    concerns = [
        {'description': sd['symptom'], 'drivers': sd['drivers']}
        for sd in symptom_drivers[:5]
    ]

    protocol_json = {
        'client_name': client_name,
        'date': date_str,
        'focus_items': nutrition_data.get('focus_items', []),
        'concerns': concerns,
        'lab_markers': lab_markers,
        'follow_up_tests': [],
        'video_link': '',
        'primary_nutrition_goal': f"Balance blood sugar and support hormone health",
        'hydration_target': '80-100 oz water daily',
        'core_habits': nutrition_data.get('core_habits', []),
        'additional_supports': [],
        'why_nutrition_helps': nutrition_data.get('why_this_helps', ''),
        'program_length': '12 weeks',
        'calories': str(macros.get('calories', '')),
        'protein': f"{macros.get('protein_g', '')}g",
        'carbohydrates': f"{macros.get('carbs_g', '')}g",
        'fat': f"{macros.get('fat_g', '')}g",
        'fiber': f"{macros.get('fiber_g', 30)}g",
        'food_recommendations_content': '',
        'daily_steps_target': lifestyle_data.get('daily_steps_target', '8,000-10,000 steps'),
        'strength_frequency': lifestyle_data.get('strength_training', {}).get('frequency', ''),
        'strength_split': lifestyle_data.get('strength_training', {}).get('split', ''),
        'stress_supports': lifestyle_data.get('stress_support', []),
        'avoid_mindful': ', '.join(lifestyle_data.get('avoid_or_mindful', [])),
        'pause_supplements': supplement_data.get('supplements_to_pause', []),
        'active_supplements': supplement_data.get('active_supplements', []),
        'titration_schedule': supplement_data.get('titration_schedule', {}),
        'early_changes': what_to_expect.get('early_changes', ''),
        'mid_changes': what_to_expect.get('mid_changes', ''),
        'long_term_changes': what_to_expect.get('long_term_changes', ''),
        'progress_criteria': what_to_expect.get('progress_criteria', ''),
        'next_phase_focus': what_to_expect.get('next_phase_focus', ''),
        'goals': goals_plan,
        'follow_up_recommended': 'Yes',
        'booking_link': '',
    }
    print("✓ Protocol JSON built")

    # --- Generate Lab Interpretation JSON (PDF 2) ---
    print("\n[5/7] Generating lab interpretation JSON (EndoAxis-style)...")
    report_type = lab_data_raw.get('reports', [{}])[0].get('report_type', 'DUTCH Complete')
    report_date = lab_data_raw.get('reports', [{}])[0].get('report_date', '')
    lab_report_json = generate_lab_interpretation_json(
        lab_results=lab_results,
        report_type=report_type,
        client_name=client_name,
        client_age="34",
        client_gender="Female",
        report_date=report_date
    )
    print("✓ Lab interpretation JSON generated")

    # --- Save JSONs ---
    print("\n[6/7] Saving JSONs...")
    Path("output").mkdir(exist_ok=True)
    protocol_json_path = "output/protocol.json"
    lab_report_json_path = "output/lab_report.json"
    with open(protocol_json_path, 'w') as f:
        json.dump(protocol_json, f, indent=2)
    with open(lab_report_json_path, 'w') as f:
        json.dump(lab_report_json, f, indent=2)
    print(f"✓ Protocol JSON: {protocol_json_path}")
    print(f"✓ Lab Report JSON: {lab_report_json_path}")

    # --- Generate PDFs ---
    print("\n[7/7] Generating PDFs...")
    protocol_pdf_path = "output/protocol.pdf"
    lab_report_pdf_path = "output/lab_report.pdf"

    generate_protocol_pdf(protocol_json, protocol_pdf_path)
    print(f"✓ PDF 1 (Protocol): {protocol_pdf_path}")

    generate_lab_report_pdf(lab_report_json, lab_report_pdf_path)
    print(f"✓ PDF 2 (Lab Report): {lab_report_pdf_path}")

    print("\n" + "=" * 80)
    print("DONE")
    print(f"  PDF 1 → {protocol_pdf_path}")
    print(f"  PDF 2 → {lab_report_pdf_path}")
    print(f"  JSON 1 → {protocol_json_path}")
    print(f"  JSON 2 → {lab_report_json_path}")
    print("=" * 80)


if __name__ == "__main__":
    main()
