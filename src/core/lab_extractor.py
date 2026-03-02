"""
Lab Report Extractor - Extract text from lab report PDFs
"""
from pathlib import Path
from utils.pdf_to_text_converter import extract_text_from_pdf

def extract_lab_report(pdf_path, output_dir="data/lab_reports/extracted"):
    """Extract text from a single lab report PDF"""
    pdf_path = Path(pdf_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = output_dir / f"{pdf_path.stem}.txt"
    
    text = extract_text_from_pdf(pdf_path)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(text)
    
    return output_path

def extract_multiple_lab_reports(pdf_paths):
    """Extract text from multiple lab report PDFs"""
    extracted = []
    for pdf_path in pdf_paths:
        try:
            output_path = extract_lab_report(pdf_path)
            extracted.append(str(output_path))
            print(f"✅ Extracted: {Path(pdf_path).name} → {output_path.name}")
        except Exception as e:
            print(f"❌ Error extracting {Path(pdf_path).name}: {e}")
    
    return extracted
