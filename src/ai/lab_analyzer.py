"""
Lab Analyzer - AI-powered parsing of lab reports
"""
import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path
from core.schema import LabResult, LabReport, LabData
from utils.token_tracker import TokenTracker

load_dotenv()
token_tracker = TokenTracker()

def analyze_lab_report(lab_text_path):
    """Parse a single lab report using AI"""
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        return None
    
    with open(lab_text_path, 'r', encoding='utf-8') as f:
        lab_text = f.read()
    
    client = OpenAI(api_key=api_key)
    
    prompt = f"""You are a medical lab report parser. Extract structured data from this lab report.

LAB REPORT TEXT:
{lab_text[:8000]}

Extract the following information:

1. Report type (e.g., "DUTCH Complete", "Blood Panel", "Thyroid Panel")
2. Report date
3. All biomarkers with their values, units, reference ranges, and status flags

Return ONLY a JSON object with this structure:
{{
  "report_type": "report name",
  "report_date": "YYYY-MM-DD",
  "results": [
    {{
      "test_name": "Biomarker name",
      "value": "numeric value or result",
      "unit": "unit of measurement",
      "reference_range": "normal range",
      "flag": "High/Low/Normal/Out of Range/Within Range"
    }}
  ],
  "key_findings": ["finding 1", "finding 2"],
  "abnormal_markers": ["marker 1", "marker 2"]
}}

Focus on:
- Hormones (estrogen, progesterone, testosterone, cortisol, DHEA)
- Metabolites and ratios
- Any markers flagged as high, low, or out of range
- Clinical significance of abnormal values"""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        
        token_tracker.track("lab_analysis", response)
        
        result = response.choices[0].message.content.strip()
        if result.startswith('```json'):
            result = result[7:]
        if result.endswith('```'):
            result = result[:-3]
        
        parsed = json.loads(result.strip())
        
        # Convert to dataclass
        results = [LabResult(**r) for r in parsed.get('results', [])]
        lab_report = LabReport(
            report_date=parsed.get('report_date', ''),
            report_type=parsed.get('report_type', ''),
            results=results,
            key_findings=parsed.get('key_findings', []),
            abnormal_markers=parsed.get('abnormal_markers', [])
        )
        
        return lab_report
        
    except Exception as e:
        print(f"Error analyzing lab report: {e}")
        return None

def analyze_multiple_lab_reports(lab_text_dir="data/lab_reports/extracted"):
    """Analyze all lab reports in directory"""
    lab_dir = Path(lab_text_dir)
    
    if not lab_dir.exists():
        return LabData(reports=[], summary="No lab reports found")
    
    lab_reports = []
    txt_files = list(lab_dir.glob("*.txt"))
    
    for txt_file in txt_files:
        print(f"📊 Analyzing {txt_file.name}...")
        lab_report = analyze_lab_report(txt_file)
        if lab_report:
            lab_reports.append(lab_report)
            
            # Save parsed JSON
            output_dir = Path("data/lab_reports/parsed")
            output_dir.mkdir(parents=True, exist_ok=True)
            output_file = output_dir / f"{txt_file.stem}.json"
            
            with open(output_file, 'w') as f:
                json.dump({
                    'report_type': lab_report.report_type,
                    'report_date': lab_report.report_date,
                    'results': [vars(r) for r in lab_report.results],
                    'key_findings': lab_report.key_findings,
                    'abnormal_markers': lab_report.abnormal_markers
                }, f, indent=2)
            
            print(f"✅ Parsed {len(lab_report.results)} biomarkers")
    
    # Generate summary
    summary = generate_lab_summary(lab_reports)
    
    return LabData(reports=lab_reports, summary=summary)

def generate_lab_summary(lab_reports):
    """Generate a summary of all lab findings"""
    if not lab_reports:
        return "No lab reports analyzed"
    
    total_markers = sum(len(r.results) for r in lab_reports)
    all_abnormal = []
    for report in lab_reports:
        all_abnormal.extend(report.abnormal_markers)
    
    summary = f"Analyzed {len(lab_reports)} lab report(s) with {total_markers} total biomarkers. "
    if all_abnormal:
        summary += f"Found {len(all_abnormal)} abnormal markers: {', '.join(all_abnormal[:5])}"
    else:
        summary += "All markers within normal ranges."
    
    return summary
