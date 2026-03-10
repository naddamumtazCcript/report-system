"""
Practitioner Agent Endpoint - Protocol Generation with DB
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import List, Optional
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from db.database import get_db_connection
from core.pdf_extractor import PDFExtractor
from core.data_mapper import extract_data
from core.template_populator import populate
from ai.gemini_lab_extractor import analyze_lab_with_gemini
from utils.cloudinary_helper import upload_pdf_bytes

router = APIRouter()

@router.post("/practitioner/generate-protocol")
async def generate_protocol(
    user_id: str = Form(...),
    client_id: int = Form(...),
    template_type: str = Form("standard"),
    questionnaire: UploadFile = File(...),
    lab_reports: List[UploadFile] = File(default=[]),
    doc_types: str = Form(default="[]"),  # JSON array as string
    libraries: str = Form(default="[]")   # JSON array as string
):
    """
    Generate protocol with lab reports and save to DB
    """
    try:
        # Parse JSON strings
        doc_types_list = json.loads(doc_types)
        libraries_list = json.loads(libraries)
        
        # Save questionnaire
        questionnaire_path = f"src/data/uploads/{user_id}_questionnaire.pdf"
        Path(questionnaire_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(questionnaire_path, "wb") as f:
            f.write(await questionnaire.read())
        
        # Extract questionnaire
        extractor = PDFExtractor(questionnaire_path)
        text = extractor.extract_text()
        
        text_file = f"src/data/uploads/{user_id}_text.txt"
        with open(text_file, 'w') as f:
            f.write(text)
        
        intake_data = extract_data(text_file)
        
        # Process lab reports
        lab_data_list = []
        for i, (lab_file, doc_type) in enumerate(zip(lab_reports, doc_types_list)):
            lab_path = f"src/data/uploads/{user_id}_lab_{i}_{doc_type}.pdf"
            
            with open(lab_path, "wb") as f:
                f.write(await lab_file.read())
            
            # Route by doc_type
            if doc_type == 'dutch':
                from ai.gemini_extractors.dutch_extraction import extract_dutch_test
                lab_result = extract_dutch_test(lab_path)
            elif doc_type == 'gi_map':
                from ai.gemini_extractors.gi_map import extract_gi_map
                lab_result = extract_gi_map(lab_path)
            elif doc_type == 'bloodwork':
                from ai.gemini_extractors.functional_bloodwork import extract_bloodwork
                lab_result = extract_bloodwork(lab_path)
            else:
                lab_result = analyze_lab_with_gemini(lab_path)
            
            lab_data_list.append({
                "type": doc_type,
                "data": lab_result.model_dump() if hasattr(lab_result, 'model_dump') else lab_result
            })
        
        # Generate protocol
        template_path = "/Users/rizwanhabib/Desktop/hassaanccript/new/report-system/templates/ProtocolTemplate.md"
        json_file = f"src/data/uploads/{user_id}_data.json"
        
        with open(json_file, 'w') as f:
            json.dump(intake_data, f, indent=2)
        
        output_file = f"src/data/uploads/{user_id}_protocol.md"
        
        # Combine lab data for template
        from core.schema import LabData, LabReport
        combined_labs = LabData(reports=[], summary="")
        for lab in lab_data_list:
            if isinstance(lab['data'], LabData):
                combined_labs.reports.extend(lab['data'].reports)
        
        populate(template_path, json_file, output_file, combined_labs if combined_labs.reports else None)
        
        # Read generated protocol
        with open(output_file, 'r') as f:
            protocol_markdown = f.read()
        
        # Save to DB
        conn = get_db_connection()
        cur = conn.cursor()
        
        protocol_json = {
            "markdown": protocol_markdown,
            "intake_data": intake_data,
            "lab_reports": lab_data_list,
            "libraries": libraries_list,
            "template_type": template_type
        }
        
        cur.execute("""
            INSERT INTO "Protocol" (protocol, status, "clientId", "createdById")
            VALUES (%s, 'draft', %s, %s)
            RETURNING id
        """, (json.dumps(protocol_json), client_id, int(user_id)))
        
        protocol_id = cur.fetchone()['id']
        conn.commit()
        
        cur.close()
        conn.close()
        
        return {
            "protocol_id": protocol_id,
            "status": "draft",
            "markdown": protocol_markdown,
            "lab_reports_processed": len(lab_data_list)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/practitioner/edit-protocol/{protocol_id}")
async def edit_protocol(
    protocol_id: int,
    markdown: str = Form(...)
):
    """
    Edit protocol markdown (draft only)
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Check status
        cur.execute('SELECT status, protocol FROM "Protocol" WHERE id = %s', (protocol_id,))
        row = cur.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Protocol not found")
        
        if row['status'] != 'draft':
            raise HTTPException(status_code=400, detail="Can only edit draft protocols")
        
        # Update markdown
        protocol_data = row['protocol']
        protocol_data['markdown'] = markdown
        
        cur.execute(
            'UPDATE "Protocol" SET protocol = %s WHERE id = %s',
            (json.dumps(protocol_data), protocol_id)
        )
        
        conn.commit()
        cur.close()
        conn.close()
        
        return {
            "protocol_id": protocol_id,
            "status": "draft",
            "markdown": markdown
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/practitioner/finalize-protocol/{protocol_id}")
async def finalize_protocol(protocol_id: int):
    """
    Finalize protocol: generate PDF and update status
    """
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from io import BytesIO
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Get protocol
        cur.execute('SELECT status, protocol FROM "Protocol" WHERE id = %s', (protocol_id,))
        row = cur.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Protocol not found")
        
        if row['status'] != 'draft':
            raise HTTPException(status_code=400, detail="Protocol already finalized")
        
        markdown = row['protocol']['markdown']
        
        # Generate PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
        styles = getSampleStyleSheet()
        story = []
        
        for line in markdown.split('\n'):
            line = line.strip()
            if not line:
                story.append(Spacer(1, 0.2*inch))
            elif line.startswith('# '):
                story.append(Paragraph(line[2:], styles['Title']))
                story.append(Spacer(1, 0.3*inch))
            elif line.startswith('## '):
                story.append(Paragraph(line[3:], styles['Heading1']))
                story.append(Spacer(1, 0.2*inch))
            elif line.startswith('### '):
                story.append(Paragraph(line[4:], styles['Heading2']))
                story.append(Spacer(1, 0.1*inch))
            elif line.startswith(('* ', '- ')):
                story.append(Paragraph('• ' + line[2:], styles['Normal']))
            elif line != '---':
                story.append(Paragraph(line, styles['Normal']))
        
        doc.build(story)
        pdf_bytes = buffer.getvalue()
        
        # Upload to Cloudinary
        cloudinary_result = upload_pdf_bytes(pdf_bytes, f"protocol_{protocol_id}")
        
        # Update DB with Cloudinary URL
        cur.execute(
            'UPDATE "Protocol" SET status = %s, pdf_url = %s WHERE id = %s',
            ('final', cloudinary_result['url'], protocol_id)
        )
        
        conn.commit()
        cur.close()
        conn.close()
        
        return {
            "protocol_id": protocol_id,
            "status": "final",
            "pdf_url": cloudinary_result['url']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/practitioner/reopen-protocol/{protocol_id}")
async def reopen_protocol(protocol_id: int):
    """
    Reopen finalized protocol for editing: remove PDF and set status to draft
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Get protocol
        cur.execute('SELECT status FROM "Protocol" WHERE id = %s', (protocol_id,))
        row = cur.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Protocol not found")
        
        if row['status'] != 'final':
            raise HTTPException(status_code=400, detail="Can only reopen finalized protocols")
        
        # Reopen: set to draft and remove PDF URL
        cur.execute(
            'UPDATE "Protocol" SET status = %s, pdf_url = NULL WHERE id = %s',
            ('draft', protocol_id)
        )
        
        conn.commit()
        cur.close()
        conn.close()
        
        return {
            "protocol_id": protocol_id,
            "status": "draft"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/practitioner/protocol/{protocol_id}")
async def get_protocol(protocol_id: int):
    """
    Get protocol by ID
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute('SELECT id, status, protocol, "clientId", "createdById" FROM "Protocol" WHERE id = %s', (protocol_id,))
        row = cur.fetchone()
        
        cur.close()
        conn.close()
        
        if not row:
            raise HTTPException(status_code=404, detail="Protocol not found")
        
        return {
            "protocol_id": row['id'],
            "status": row['status'],
            "client_id": row['clientId'],
            "created_by_id": row['createdById'],
            "markdown": row['protocol']['markdown'],
            "intake_data": row['protocol'].get('intake_data'),
            "lab_reports": row['protocol'].get('lab_reports'),
            "libraries": row['protocol'].get('libraries'),
            "template_type": row['protocol'].get('template_type')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/practitioner/protocol/{protocol_id}/pdf")
async def download_pdf(protocol_id: int):
    """
    Get protocol PDF URL (finalized only)
    """
    try:
        from fastapi.responses import RedirectResponse
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute('SELECT status, pdf_url FROM "Protocol" WHERE id = %s', (protocol_id,))
        row = cur.fetchone()
        
        cur.close()
        conn.close()
        
        if not row:
            raise HTTPException(status_code=404, detail="Protocol not found")
        
        if row['status'] != 'final':
            raise HTTPException(status_code=400, detail="Protocol not finalized")
        
        if not row['pdf_url']:
            raise HTTPException(status_code=404, detail="PDF not found")
        
        return RedirectResponse(url=row['pdf_url'])
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
