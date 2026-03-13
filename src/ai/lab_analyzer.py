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


def generate_marker_summary(
    marker_name: str,
    value: str,
    unit: str,
    reference_range: str,
    flag: str
) -> str:
    """
    Generate AI summary for out-of-range lab marker
    
    Args:
        marker_name: Name of the lab marker
        value: Test result value
        unit: Unit of measurement
        reference_range: Normal reference range
        flag: Status flag (H/L/High/Low)
        
    Returns:
        2-3 sentence summary explaining the marker
    """
    try:
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            logger.error("OPENAI_API_KEY not found")
            return ""
        
        client = OpenAI(api_key=api_key)
        
        prompt = f"""You are a health practitioner explaining lab results to a client.

Given this out-of-range lab marker:
- Marker: {marker_name}
- Value: {value} {unit}
- Reference Range: {reference_range}
- Status: {flag}

Generate a 2-3 sentence summary that:
1. States whether the value is above or below normal
2. Briefly explains what this marker measures
3. Mentions potential health implications

Use supportive, non-alarmist language. Be concise and clear.
Do not give medical advice or recommend specific treatments.

Example format:
"Your [marker name] level is [above/below] the normal reference range. This marker measures [what it measures]. [Status] levels may be associated with [potential implications]."
"""
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=150
        )
        
        summary = response.choices[0].message.content.strip()
        logger.info(f"Generated summary for {marker_name}")
        
        return summary
        
    except Exception as e:
        logger.error(f"Failed to generate summary for {marker_name}: {e}")
        return ""


def analyze_lab_results(lab_results: List[LabResult]) -> List[LabResult]:
    """
    Analyze lab results and add summaries for out-of-range markers
    
    Args:
        lab_results: List of LabResult objects
        
    Returns:
        List of LabResult objects with summaries added to out-of-range markers
    """
    if not lab_results:
        return []
    
    logger.info(f"Analyzing {len(lab_results)} lab results...")
    
    out_of_range_count = 0
    
    for result in lab_results:
        if is_out_of_range(result.flag):
            out_of_range_count += 1
            logger.info(f"Out-of-range marker detected: {result.test_name} = {result.value} (Flag: {result.flag})")
            
            # Generate summary for out-of-range marker
            summary = generate_marker_summary(
                marker_name=result.test_name,
                value=result.value,
                unit=result.unit,
                reference_range=result.reference_range,
                flag=result.flag
            )
            
            result.summary = summary
        else:
            # Normal markers don't get summaries
            result.summary = None
    
    logger.info(f"Found {out_of_range_count} out-of-range markers")
    logger.info(f"Generated {out_of_range_count} summaries")
    
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


def format_lab_summary_for_protocol(lab_results: List[LabResult]) -> str:
    """
    Format out-of-range markers with summaries for protocol inclusion
    
    Args:
        lab_results: List of LabResult objects
        
    Returns:
        Formatted string for protocol
    """
    out_of_range = get_out_of_range_markers(lab_results)
    
    if not out_of_range:
        return "All lab markers are within normal reference ranges."
    
    summary_lines = []
    summary_lines.append(f"**Out-of-Range Markers ({len(out_of_range)} found):**\n")
    
    for result in out_of_range:
        summary_lines.append(f"**{result.test_name}**")
        summary_lines.append(f"- Value: {result.value} {result.unit}")
        summary_lines.append(f"- Reference Range: {result.reference_range}")
        summary_lines.append(f"- Status: {result.flag}")
        
        if result.summary:
            summary_lines.append(f"- Summary: {result.summary}")
        
        summary_lines.append("")  # Blank line between markers
    
    return "\n".join(summary_lines)
