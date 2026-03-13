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
from utils.error_handler import logger

router = APIRouter()

@router.post("/practitioner/generate-protocol")
async def generate_protocol(
    user_id: str = Form(...),
    client_id: int = Form(...),
    template_type: str = Form("standard"),
    questionnaire: UploadFile = File(...),
    lab_reports: List[UploadFile] = File(default=[]),
    doc_types: str = Form(default="[]"),
    libraries: str = Form(default="[]")
):
    """
    Generate protocol with lab reports and save to DB
    """
    try:
        logger.info(
            f"[practitioner.generate_protocol] user_id={user_id}, "
            f"client_id={client_id}, template_type={template_type}, "
            f"num_lab_reports={len(lab_reports)}"
        )

<<<<<<< Updated upstream
        # Parse JSON strings
=======
>>>>>>> Stashed changes
        doc_types_list = json.loads(doc_types)
        libraries_list = json.loads(libraries)
        logger.info(
            f"[practitioner.generate_protocol] Parsed doc_types={doc_types_list}, "
            f"libraries={libraries_list}"
        )
<<<<<<< Updated upstream
        
=======

>>>>>>> Stashed changes
        # Save questionnaire
        questionnaire_path = f"src/data/uploads/{user_id}_questionnaire.pdf"
        Path(questionnaire_path).parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"[practitioner.generate_protocol] Saving questionnaire to {questionnaire_path}")

        with open(questionnaire_path, "wb") as f:
            f.write(await questionnaire.read())

        # Extract questionnaire
        logger.info(f"[practitioner.generate_protocol] Extracting text from {questionnaire_path}")
        extractor = PDFExtractor(questionnaire_path)
        text = extractor.extract_text()

        text_file = f"src/data/uploads/{user_id}_text.txt"
        with open(text_file, 'w') as f:
            f.write(text)
<<<<<<< Updated upstream
        
=======

>>>>>>> Stashed changes
        logger.info(f"[practitioner.generate_protocol] Text saved to {text_file}, starting extract_data")
        intake_data = extract_data(text_file)
        logger.info(
            f"[practitioner.generate_protocol] extract_data complete; "
            f"top-level keys={list(intake_data.keys())}"
        )
<<<<<<< Updated upstream
        
=======

>>>>>>> Stashed changes
        # Process lab reports
        lab_data_list = []
        for i, (lab_file, doc_type) in enumerate(zip(lab_reports, doc_types_list)):
            lab_path = f"src/data/uploads/{user_id}_lab_{i}_{doc_type}.pdf"
            logger.info(
                f"[practitioner.generate_protocol] Saving lab {i} doc_type={doc_type} "
                f"to {lab_path}"
            )
<<<<<<< Updated upstream
            
=======

>>>>>>> Stashed changes
            with open(lab_path, "wb") as f:
                f.write(await lab_file.read())

            if doc_type == 'dutch':
                from ai.gemini_extractors.dutch_extraction import extract_dutch_test
                logger.info(f"[practitioner.generate_protocol] Routing DUTCH lab to gemini extractor")
                lab_result = extract_dutch_test(lab_path)
            elif doc_type == 'gi_map':
                from ai.gemini_extractors.gi_map import extract_gi_map
                logger.info(f"[practitioner.generate_protocol] Routing GI-MAP lab to gemini extractor")
                lab_result = extract_gi_map(lab_path)
            elif doc_type == 'bloodwork':
                from ai.gemini_extractors.functional_bloodwork import extract_bloodwork
                logger.info(f"[practitioner.generate_protocol] Routing bloodwork lab to gemini extractor")
                lab_result = extract_bloodwork(lab_path)
            else:
                logger.info(f"[practitioner.generate_protocol] Routing lab to generic Gemini analyzer")
                lab_result = analyze_lab_with_gemini(lab_path)

            lab_data_list.append({
                "type": doc_type,
                "data": lab_result.model_dump() if hasattr(lab_result, 'model_dump') else lab_result
            })
<<<<<<< Updated upstream
        
        # Generate protocol – use project root (one level above src)
        project_root = Path(__file__).resolve().parent.parent.parent.parent
        template_path = project_root / "templates" / "ProtocolTemplate.md"
        logger.info(f"[practitioner.generate_protocol] Using template_path={template_path}")
        json_file = f"src/data/uploads/{user_id}_data.json"
        
        with open(json_file, 'w') as f:
            json.dump(intake_data, f, indent=2)
        logger.info(f"[practitioner.generate_protocol] Intake JSON saved to {json_file}")
        
        output_file = f"src/data/uploads/{user_id}_protocol.md"
        
        # Combine lab data for template
        from core.schema import LabData, LabReport
        combined_labs = LabData(reports=[], summary="")
        for lab in lab_data_list:
            if isinstance(lab['data'], LabData):
                combined_labs.reports.extend(lab['data'].reports)
        
        logger.info(
            f"[practitioner.generate_protocol] Calling populate with "
            f"output_file={output_file}, num_combined_labs={len(combined_labs.reports)}"
        )
        populate(template_path, json_file, output_file, combined_labs if combined_labs.reports else None)
        logger.info(f"[practitioner.generate_protocol] Template population complete")
        
        # Read generated protocol
        with open(output_file, 'r') as f:
            protocol_markdown = f.read()
=======

        # Generate protocol PDF
        output_file = f"src/data/uploads/{user_id}_protocol.pdf"

        protocol_data = {
            'client_name': f"{intake_data.get('personal_info', {}).get('legal_first_name', '')} {intake_data.get('personal_info', {}).get('last_name', '')}".strip() or 'Client',
            'health_info': intake_data.get('health_info', {}),
            'lab_review_content': json.dumps(lab_data_list) if lab_data_list else ''
        }

        logger.info(f"[practitioner.generate_protocol] Generating PDF to {output_file}")
        generate_protocol_pdf(protocol_data, output_file)

        with open(output_file.replace('.pdf', '.html'), 'r') as f:
            protocol_markdown = f.read()

>>>>>>> Stashed changes
        logger.info(
            f"[practitioner.generate_protocol] Generated protocol length={len(protocol_markdown)} "
            f"bytes; starting DB save"
        )
<<<<<<< Updated upstream
        
=======

>>>>>>> Stashed changes
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
<<<<<<< Updated upstream
        logger.info(
            f"[practitioner.generate_protocol] Saved protocol to DB with id={protocol_id}"
        )
        
=======
        logger.info(f"[practitioner.generate_protocol] Saved protocol to DB with id={protocol_id}")

>>>>>>> Stashed changes
        cur.close()
        conn.close()

        return {
            "protocol_id": protocol_id,
            "status": "draft",
            "lab_reports_processed": len(lab_data_list)
        }

    except Exception as e:
<<<<<<< Updated upstream
        # Log full traceback for debugging
        import traceback
        logger.error(
            f"[practitioner.generate_protocol] Unexpected error: {e}",
            exc_info=True
        )
=======
        logger.error(f"[practitioner.generate_protocol] Unexpected error: {e}", exc_info=True)
>>>>>>> Stashed changes
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

        cur.execute('SELECT status, protocol FROM "Protocol" WHERE id = %s', (protocol_id,))
        row = cur.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Protocol not found")

        if row['status'] != 'draft':
            raise HTTPException(status_code=400, detail="Can only edit draft protocols")

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
<<<<<<< Updated upstream
        logger.info(f"[practitioner.finalize_protocol] Start finalize for protocol_id={protocol_id}")

        from utils.pdf_formatter import markdown_to_pdf
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Get protocol
=======
        import tempfile, os
        from utils.pdf_formatter import markdown_to_pdf

        logger.info(f"[practitioner.finalize_protocol] Start finalize for protocol_id={protocol_id}")

        conn = get_db_connection()
        cur = conn.cursor()

>>>>>>> Stashed changes
        cur.execute('SELECT status, protocol FROM "Protocol" WHERE id = %s', (protocol_id,))
        row = cur.fetchone()

        if not row:
            logger.info(f"[practitioner.finalize_protocol] Protocol not found id={protocol_id}")
            raise HTTPException(status_code=404, detail="Protocol not found")
        
        if row['status'] != 'draft':
            logger.info(
                f"[practitioner.finalize_protocol] Protocol already finalized or not draft "
                f"id={protocol_id}, status={row['status']}"
            )
            raise HTTPException(status_code=400, detail="Protocol already finalized")
<<<<<<< Updated upstream
        
        markdown = row['protocol']['markdown']
        logger.info(
            f"[practitioner.finalize_protocol] Loaded protocol markdown length={len(markdown)} "
            f"for id={protocol_id}"
        )
        
        # Generate formatted PDF using the new formatter
        logger.info(f"[practitioner.finalize_protocol] Building PDF for protocol_id={protocol_id}")
        pdf_bytes = markdown_to_pdf(markdown)
        logger.info(
            f"[practitioner.finalize_protocol] Generated PDF bytes={len(pdf_bytes)} "
            f"for protocol_id={protocol_id}"
        )
        
        # Upload to Cloudinary
        logger.info(f"[practitioner.finalize_protocol] Uploading PDF to Cloudinary for protocol_id={protocol_id}")
        cloudinary_result = upload_pdf_bytes(pdf_bytes, f"protocol_{protocol_id}")
        logger.info(
            f"[practitioner.finalize_protocol] Uploaded PDF to Cloudinary url={cloudinary_result.get('url')}"
        )
        
        # Update DB with Cloudinary URL
=======

        markdown = row['protocol']['markdown']
        logger.info(f"[practitioner.finalize_protocol] Building PDF for protocol_id={protocol_id}")

        pdf_bytes = markdown_to_pdf(markdown)
        logger.info(f"[practitioner.finalize_protocol] Generated PDF bytes={len(pdf_bytes)}")

        cloudinary_result = upload_pdf_bytes(pdf_bytes, f"protocol_{protocol_id}")
        logger.info(f"[practitioner.finalize_protocol] Uploaded to Cloudinary url={cloudinary_result.get('url')}")

>>>>>>> Stashed changes
        cur.execute(
            'UPDATE "Protocol" SET status = %s, pdf_url = %s WHERE id = %s',
            ('final', cloudinary_result['url'], protocol_id),
        )

        conn.commit()
        cur.close()
        conn.close()
<<<<<<< Updated upstream
        
=======

>>>>>>> Stashed changes
        logger.info(f"[practitioner.finalize_protocol] Finalized protocol_id={protocol_id}")

        return {
            "protocol_id": protocol_id,
            "status": "final",
            "pdf_url": cloudinary_result['url'],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[practitioner.finalize_protocol] Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/practitioner/reopen-protocol/{protocol_id}")
async def reopen_protocol(protocol_id: int):
    """
    Reopen finalized protocol for editing
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute('SELECT status FROM "Protocol" WHERE id = %s', (protocol_id,))
        row = cur.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Protocol not found")
        if row['status'] != 'final':
            raise HTTPException(status_code=400, detail="Can only reopen finalized protocols")

        cur.execute(
            'UPDATE "Protocol" SET status = %s, pdf_url = NULL WHERE id = %s',
            ('draft', protocol_id)
        )

        conn.commit()
        cur.close()
        conn.close()

        return {"protocol_id": protocol_id, "status": "draft"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"[practitioner.finalize_protocol] Unexpected error: {e}",
            exc_info=True,
        )
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


@router.get("/practitioner/protocol/{protocol_id}/preview-pdf")
async def preview_pdf(protocol_id: int):
    """
<<<<<<< Updated upstream
    Generate and return a PDF preview (works for draft or final protocols).
    This generates the PDF on-the-fly without saving to Cloudinary.
=======
    Generate and return a PDF preview (works for draft or final protocols)
>>>>>>> Stashed changes
    """
    try:
        from fastapi.responses import Response
        from utils.pdf_formatter import markdown_to_pdf
<<<<<<< Updated upstream
        
        logger.info(f"[practitioner.preview_pdf] Generating preview for protocol_id={protocol_id}")
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute('SELECT protocol FROM "Protocol" WHERE id = %s', (protocol_id,))
        row = cur.fetchone()
        
        cur.close()
        conn.close()
        
        if not row:
            raise HTTPException(status_code=404, detail="Protocol not found")
        
        markdown = row['protocol'].get('markdown', '')
        if not markdown:
            raise HTTPException(status_code=400, detail="Protocol has no content")
        
        # Generate PDF
        pdf_bytes = markdown_to_pdf(markdown)
        
        logger.info(
            f"[practitioner.preview_pdf] Generated preview PDF bytes={len(pdf_bytes)} "
            f"for protocol_id={protocol_id}"
        )
        
        # Return PDF directly
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"inline; filename=protocol_{protocol_id}_preview.pdf"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"[practitioner.preview_pdf] Unexpected error: {e}",
            exc_info=True,
        )
=======

        logger.info(f"[practitioner.preview_pdf] Generating preview for protocol_id={protocol_id}")

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute('SELECT protocol FROM "Protocol" WHERE id = %s', (protocol_id,))
        row = cur.fetchone()

        cur.close()
        conn.close()

        if not row:
            raise HTTPException(status_code=404, detail="Protocol not found")

        markdown = row['protocol'].get('markdown', '')
        if not markdown:
            raise HTTPException(status_code=400, detail="Protocol has no content")

        pdf_bytes = markdown_to_pdf(markdown)
        logger.info(f"[practitioner.preview_pdf] Generated preview PDF bytes={len(pdf_bytes)}")

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"inline; filename=protocol_{protocol_id}_preview.pdf"}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[practitioner.preview_pdf] Unexpected error: {e}", exc_info=True)
>>>>>>> Stashed changes
        raise HTTPException(status_code=500, detail=str(e))
