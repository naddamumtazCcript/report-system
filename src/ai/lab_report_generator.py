"""
Lab Report Generator - Generates EndoAxis-style lab interpretation report JSON using GPT
"""
import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from typing import List, Dict, Any
from core.schema import LabResult
from ai.lab_analyzer import is_out_of_range
from utils.error_handler import logger

load_dotenv()


def generate_lab_interpretation_json(
    lab_results: List[LabResult],
    report_type: str,
    client_name: str,
    client_age: str = "",
    client_gender: str = "",
    report_date: str = ""
) -> Dict[str, Any]:
    """
    Generate EndoAxis-style lab interpretation JSON using GPT.
    Only called when lab reports are present.
    """
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found")

    client = OpenAI(api_key=api_key)

    out_of_range = [r for r in lab_results if is_out_of_range(r.flag)]
    all_markers_text = "\n".join([
        f"- {r.test_name}: {r.value} {r.unit} | Range: {r.reference_range} | Flag: {r.flag}"
        for r in lab_results
    ])
    out_of_range_text = "\n".join([
        f"- {r.test_name}: {r.value} {r.unit} | Range: {r.reference_range} | Flag: {r.flag}"
        for r in out_of_range
    ]) or "None"

    prompt = f"""You are a clinical lab interpretation specialist writing an EndoAxis-style hormone report for a practitioner.

PATIENT INFO:
- Name: {client_name}
- Age: {client_age}
- Gender: {client_gender}
- Report Type: {report_type}
- Report Date: {report_date}

ALL LAB MARKERS:
{all_markers_text}

OUT-OF-RANGE MARKERS:
{out_of_range_text}

Generate a comprehensive clinical interpretation report in the exact EndoAxis style. The report must include:
1. An overview with sex hormone pattern summary and adrenal pattern summary (2-3 paragraphs each)
2. Findings section - one entry per out-of-range marker with title, explanation, and bullet-point causes
3. Hormonal insights - grouped sections (Progesterone/Estrogen Balance, Estrogen Detox, Estrogen/Testosterone Balance, or relevant groupings based on markers)
4. Adrenal insights - if adrenal markers are present
5. Strategy & Analysis - deep-dive per hormonal/adrenal finding with clinical recommendations

Use professional clinical language. Do not diagnose. Focus on education and pattern recognition.

Return ONLY a JSON object with this exact structure:
{{
  "client_name": "{client_name}",
  "client_age": "{client_age}",
  "client_gender": "{client_gender}",
  "report_type": "{report_type}",
  "report_date": "{report_date}",
  "overview": {{
    "sex_hormone_pattern": {{
      "pattern_number": "pattern number or label",
      "summary": "2-3 paragraph narrative summary of sex hormone pattern"
    }},
    "adrenal_pattern": {{
      "pattern_number": "pattern number or label",
      "summary": "2-3 paragraph narrative summary of adrenal pattern"
    }}
  }},
  "findings": [
    {{
      "title": "FINDING TITLE IN CAPS",
      "explanation": "1-2 paragraph explanation of what this finding means clinically",
      "bullet_points": ["potential cause or implication 1", "potential cause or implication 2"],
      "recommendation": "brief clinical recommendation"
    }}
  ],
  "hormonal_insights": [
    {{
      "section_title": "SECTION TITLE (e.g. PROGESTERONE / ESTROGEN BALANCE)",
      "content": "2-3 paragraph clinical narrative for this hormonal relationship"
    }}
  ],
  "adrenal_insights": [
    {{
      "section_title": "SECTION TITLE (e.g. DIURNAL RISE)",
      "content": "1-2 paragraph clinical narrative"
    }}
  ],
  "strategy_analysis": [
    {{
      "section_title": "SECTION TITLE",
      "content": "deep-dive clinical narrative with specific recommendations, 3-5 paragraphs"
    }}
  ],
  "disclaimer": "All comments made on this report are coming from a series of relationships made between the primary sex hormones and metabolites. Nothing can replace the expertise and experience that comes from you, the provider, and your understanding of your patient's unique case and history."
}}"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=4000
    )

    result = response.choices[0].message.content.strip()
    if result.startswith('```json'):
        result = result[7:]
    if result.startswith('```'):
        result = result[3:]
    if result.endswith('```'):
        result = result[:-3]

    data = json.loads(result.strip())
    logger.info(f"Generated lab interpretation JSON for {client_name}")
    return data
