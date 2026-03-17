"""
Lab Analyzer - Detect out-of-range markers and generate AI summaries
"""
import os
from openai import OpenAI
from dotenv import load_dotenv
from typing import List, Optional
from core.schema import LabResult
from utils.error_handler import logger

load_dotenv()


def is_out_of_range(flag: str) -> bool:
    """Check if a lab marker is out of normal range"""
    if not flag:
        return False
    
    flag_upper = flag.upper().strip()
    
    # Simple flags
    out_of_range_flags = ['H', 'HIGH', 'L', 'LOW', 'OUT OF RANGE', 'ABNORMAL', 'ELEVATED']
    
    if flag_upper in out_of_range_flags:
        return True
    
    # Descriptive flags
    out_of_range_keywords = ['ABOVE', 'BELOW', 'ELEVATED', 'DECREASED', 'HIGH END', 'LOW END']
    
    for keyword in out_of_range_keywords:
        if keyword in flag_upper:
            return True
    
    return False


def generate_marker_details(
    marker_name: str,
    value: str,
    unit: str,
    reference_range: str,
    flag: str
) -> dict:
    """
    Generate structured AI details for a lab marker (all markers, not just out-of-range).
    Returns dict with what_we_found, why_this_matters, symptoms.
    """
    try:
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            logger.error("OPENAI_API_KEY not found")
            return {}

        client = OpenAI(api_key=api_key)

        prompt = f"""You are a functional health practitioner writing a client protocol report.

Lab marker:
- Marker: {marker_name}
- Value: {value} {unit}
- Reference Range: {reference_range}
- Status: {flag}

Return ONLY a JSON object with exactly these 3 fields:
{{
  "what_we_found": "1 sentence: state the value, whether it is within/above/below range, and what this marker measures",
  "why_this_matters": "1-2 sentences: explain the clinical significance of this result for this client",
  "symptoms": "comma-separated list of symptoms this marker level can contribute to"
}}

Use clear, supportive, non-alarmist language. Do not diagnose."""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=200
        )

        result = response.choices[0].message.content.strip()
        if result.startswith('```json'):
            result = result[7:]
        if result.startswith('```'):
            result = result[3:]
        if result.endswith('```'):
            result = result[:-3]

        import json
        data = json.loads(result.strip())
        logger.info(f"Generated details for {marker_name}")
        return data

    except Exception as e:
        logger.error(f"Failed to generate details for {marker_name}: {e}")
        return {}


def analyze_lab_results(lab_results: List[LabResult]) -> List[LabResult]:
    """
    Analyze ALL lab results and add structured details to each marker.
    """
    if not lab_results:
        return []

    logger.info(f"Analyzing {len(lab_results)} lab results...")

    for result in lab_results:
        if is_out_of_range(result.flag):
            logger.info(f"Out-of-range marker detected: {result.test_name} = {result.value} (Flag: {result.flag})")

        details = generate_marker_details(
            marker_name=result.test_name,
            value=result.value,
            unit=result.unit,
            reference_range=result.reference_range,
            flag=result.flag
        )
        result.what_we_found = details.get('what_we_found', '')
        result.why_this_matters = details.get('why_this_matters', '')
        result.symptoms = details.get('symptoms', '')

    logger.info(f"Generated details for {len(lab_results)} markers")
    return lab_results


def get_out_of_range_markers(lab_results: List[LabResult]) -> List[LabResult]:
    """
    Filter and return only out-of-range markers
    
    Args:
        lab_results: List of LabResult objects
        
    Returns:
        List of only out-of-range LabResult objects
    """
    return [result for result in lab_results if is_out_of_range(result.flag)]


def build_lab_markers_for_protocol(lab_results: List[LabResult]) -> List[dict]:
    """
    Build structured list of ALL lab markers for protocol PDF 1 lab review.
    Includes what_we_found, why_this_matters, symptoms per marker.
    """
    markers = []
    for result in lab_results:
        oor = is_out_of_range(result.flag)
        flag_upper = (result.flag or '').upper().strip()
        if flag_upper == 'H' or any(k in flag_upper for k in ['ABOVE', 'ELEVATED', 'HIGH END', 'HIGH']):
            flag_normalized = 'H'
        elif flag_upper == 'L' or any(k in flag_upper for k in ['BELOW', 'DECREASED', 'LOW END', 'LOW']):
            flag_normalized = 'L'
        else:
            flag_normalized = 'N'
        markers.append({
            'test_name': result.test_name,
            'value': result.value,
            'unit': result.unit,
            'reference_range': result.reference_range,
            'flag': result.flag,
            'flag_normalized': flag_normalized,
            'is_out_of_range': oor,
            'what_we_found': getattr(result, 'what_we_found', ''),
            'why_this_matters': getattr(result, 'why_this_matters', ''),
            'symptoms': getattr(result, 'symptoms', ''),
        })
    return markers
