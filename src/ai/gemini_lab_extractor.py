"""
Gemini Lab Extractors - Converts Gemini output to LabData format
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from core.schema import LabResult, LabReport, LabData

load_dotenv()

def detect_lab_type(pdf_path: str) -> str:
    """Detect lab report type from PDF filename/content"""
    filename = Path(pdf_path).name.lower()
    
    if 'dutch' in filename:
        return 'dutch'
    elif 'gi-map' in filename or 'gi_map' in filename:
        return 'gi_map'
    elif 'bloodwork' in filename or 'blood' in filename:
        return 'bloodwork'
    return 'generic'

def extract_dutch(pdf_path: str) -> LabData:
    """Extract DUTCH report using Gemini"""
    from ai.gemini_extractors.dutch_extraction import extract_dutch_test

    parsed_data, lab_results = extract_dutch_test(pdf_path)

    abnormal = [r.test_name for r in lab_results if r.flag and r.flag not in ('Normal', 'N')]
    lab_report = LabReport(
        report_date="",
        report_type="DUTCH Complete",
        results=lab_results,
        key_findings=[f"Patient: {parsed_data.patient_sex}, Age: {parsed_data.patient_age}"],
        abnormal_markers=abnormal
    )
    return LabData(
        reports=[lab_report],
        summary=f"DUTCH Complete analysis for {parsed_data.patient_sex} patient, age {parsed_data.patient_age}. {len(lab_results)} markers extracted."
    )

def extract_gi_map(pdf_path: str) -> LabData:
    """Extract GI-MAP report using Gemini"""
    from ai.gemini_extractors.gi_map import extract_gi_map as gemini_extract
    
    result = gemini_extract(pdf_path)
    lab_results = []
    
    # Pathogens
    for marker in result.pathogens.bacterial:
        lab_results.append(LabResult(
            test_name=f"Bacterial: {marker.marker_name}",
            value=marker.result,
            unit="",
            reference_range=marker.reference,
            flag=marker.status or "Normal"
        ))
    
    # Commensal bacteria
    for marker in result.commensal_bacteria:
        lab_results.append(LabResult(
            test_name=f"Commensal: {marker.marker_name}",
            value=marker.result,
            unit="",
            reference_range=marker.reference,
            flag=marker.status or "Normal"
        ))
    
    # Intestinal health
    for marker in result.intestinal_health.digestion:
        lab_results.append(LabResult(
            test_name=f"Digestion: {marker.marker_name}",
            value=marker.result,
            unit="",
            reference_range=marker.reference,
            flag=marker.status or "Normal"
        ))
    
    abnormal = [r.test_name for r in lab_results if r.flag and r.flag != "Normal"]
    
    lab_report = LabReport(
        report_date="",
        report_type="GI-MAP",
        results=lab_results,
        key_findings=[f"H. pylori: {result.h_pylori.h_pylori_result.result}"],
        abnormal_markers=abnormal
    )
    
    return LabData(
        reports=[lab_report],
        summary=f"GI-MAP analysis complete. {len(lab_results)} markers extracted, {len(abnormal)} abnormal."
    )

def extract_bloodwork(pdf_path: str) -> LabData:
    """Extract Functional Bloodwork using Gemini"""
    from ai.gemini_extractors.functional_bloodwork import extract_bloodwork as gemini_extract

    report_date, lab_results = gemini_extract(pdf_path)

    abnormal = [r.test_name for r in lab_results if r.flag and r.flag not in ('Normal', 'N')]
    lab_report = LabReport(
        report_date=report_date,
        report_type="Functional Bloodwork Panel",
        results=lab_results,
        key_findings=[f"Report date: {report_date}"],
        abnormal_markers=abnormal
    )
    return LabData(
        reports=[lab_report],
        summary=f"Bloodwork analysis complete. {len(lab_results)} markers extracted, {len(abnormal)} abnormal."
    )

def analyze_lab_with_gemini(pdf_path: str) -> LabData:
    """
    Main entry point - detects lab type and extracts using appropriate Gemini extractor
    Returns LabData format compatible with existing system
    """
    lab_type = detect_lab_type(pdf_path)
    
    if lab_type == 'dutch':
        return extract_dutch(pdf_path)
    elif lab_type == 'gi_map':
        return extract_gi_map(pdf_path)
    elif lab_type == 'bloodwork':
        return extract_bloodwork(pdf_path)
    else:
        # Fallback to OpenAI for unknown types
        from ai.lab_analyzer import analyze_lab_report
        return analyze_lab_report(pdf_path)
