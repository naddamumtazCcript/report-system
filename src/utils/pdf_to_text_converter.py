"""
PDF to Text Converter - Convert PDFs in knowledge base to text files
"""
import pdfplumber
from pathlib import Path

def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file"""
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text.strip()

def convert_pdf_to_text(pdf_path, output_path=None):
    """Convert a single PDF to text file"""
    pdf_path = Path(pdf_path)
    if output_path is None:
        output_path = pdf_path.with_suffix('.txt')
    
    text = extract_text_from_pdf(pdf_path)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(text)
    
    return output_path

def convert_knowledge_base_pdfs(kb_root="knowledge_base"):
    """Convert all PDFs in knowledge base to text files"""
    kb_path = Path(kb_root)
    if not kb_path.exists():
        print(f"Knowledge base directory not found: {kb_root}")
        return []
    
    converted = []
    for pdf_file in kb_path.rglob("*.pdf"):
        txt_file = pdf_file.with_suffix('.txt')
        
        # Skip if text file already exists and is newer
        if txt_file.exists() and txt_file.stat().st_mtime > pdf_file.stat().st_mtime:
            print(f"⏭️  Skipping {pdf_file.name} (text file up to date)")
            continue
        
        try:
            convert_pdf_to_text(pdf_file, txt_file)
            converted.append(str(txt_file))
            print(f"✅ Converted: {pdf_file.relative_to(kb_path)} → {txt_file.name}")
        except Exception as e:
            print(f"❌ Error converting {pdf_file.name}: {e}")
    
    return converted
