"""
Practitioner Agent Endpoint - Protocol Generation with DB
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import List, Optional
import json
import sys
import tempfile
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from db.database import get_db_connection
from core.pdf_extractor import PDFExtractor
from ai.lab_analyzer import build_lab_markers_for_protocol
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
from ai.gemini_lab_extractor import analyze_lab_with_gemini
from utils.cloudinary_helper import upload_pdf_bytes
from utils.error_handler import logger

router = APIRouter()


def _build_protocol_json(intake_data: dict, lab_markers: list, client_name: str) -> dict:
    """Run AI recommendations and assemble protocol JSON."""
    symptom_data = analyze_symptom_drivers(intake_data)
    lifestyle_data = generate_lifestyle_recommendations(intake_data)
    supplement_data = generate_supplement_recommendations(intake_data)
    nutrition_data = generate_nutrition_recommendations(intake_data)
    macros = get_nutrition_recommendations(intake_data).get('macros', {})
    what_to_expect = generate_what_to_expect(intake_data, supplement_data)
    goals_plan = generate_goals_action_plan(intake_data, nutrition_data, lifestyle_data, supplement_data)

    concerns = [
        {'description': sd['symptom'], 'drivers': sd['drivers']}
        for sd in symptom_data.get('symptom_drivers', [])[:5]
    ]

    return {
        'client_name': client_name,
        'date': datetime.now().strftime('%B %d, %Y'),
        'focus_items': nutrition_data.get('focus_items', []),
        'concerns': concerns,
        'lab_markers': lab_markers,
        'follow_up_tests': [],
        'video_link': '',
        'primary_nutrition_goal': 'Balance blood sugar and support hormone health',
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
        doc_types_list = json.loads(doc_types)
        logger.info(f"[generate_protocol] user={user_id} client={client_id} labs={len(lab_reports)}")

        upload_dir = Path(f"src/data/uploads")
        upload_dir.mkdir(parents=True, exist_ok=True)

        # Save + extract questionnaire
        q_path = upload_dir / f"{user_id}_questionnaire.pdf"
        q_path.write_bytes(await questionnaire.read())
        text = PDFExtractor(str(q_path)).extract_text()

        # Save text and use data_mapper (GPT) to extract structured intake data from PDF text
        text_file = str(upload_dir / f"{user_id}_text.txt")
        with open(text_file, 'w') as f:
            f.write(text)
        from core.data_mapper import extract_data
        intake_data = extract_data(text_file)

        # Client name from extracted data
        pi = intake_data.get('personal_info', {})
        client_name = f"{pi.get('legal_first_name', pi.get('name', ''))} {pi.get('last_name', '')}".strip() or 'Client'

        # Process lab reports
        lab_results = []
        lab_report_json = None
        report_type = 'Lab Report'

        for i, (lab_file, doc_type) in enumerate(zip(lab_reports, doc_types_list)):
            lab_path = str(upload_dir / f"{user_id}_lab_{i}_{doc_type}.pdf")
            Path(lab_path).write_bytes(await lab_file.read())

            lab_data = analyze_lab_with_gemini(lab_path)
            report_type = lab_data.reports[0].report_type if lab_data.reports else doc_type
            for report in lab_data.reports:
                lab_results.extend(report.results)

        analyzed = lab_results  # already analyzed inside extractors
        lab_markers = build_lab_markers_for_protocol(analyzed)

        # Build protocol JSON
        protocol_json = _build_protocol_json(intake_data, lab_markers, client_name)

        # Build lab report JSON (only if labs present)
        if lab_results:
            lab_report_json = generate_lab_interpretation_json(
                lab_results=analyzed,
                report_type=report_type,
                client_name=client_name,
                client_age=str(pi.get('age', '')),
                client_gender=pi.get('gender', 'Female'),
                report_date=datetime.now().strftime('%B %d, %Y')
            )

        # Save to DB
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO "Protocol" (protocol, status, "clientId", "createdById")
            VALUES (%s, 'pending_approval', %s, %s)
            RETURNING id
        """, (json.dumps({
            'protocol_json': protocol_json,
            'lab_report_json': lab_report_json,
            'template_type': template_type
        }), client_id, int(user_id)))
        protocol_id = cur.fetchone()['id']
        conn.commit()
        cur.close()
        conn.close()

        logger.info(f"[generate_protocol] Saved protocol id={protocol_id}")
        return {
            "protocol_id": protocol_id,
            "status": "pending_approval",
            "has_lab_report": lab_report_json is not None
        }

    except Exception as e:
        logger.error(f"[generate_protocol] Error: {e}", exc_info=True)
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
    Finalize protocol: generate PDFs, upload to Cloudinary, initialize client agent
    """
    try:
        from core.html_pdf_generator import generate_protocol_pdf, generate_lab_report_pdf

        logger.info(f"[finalize_protocol] Start finalize for protocol_id={protocol_id}")

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT status, protocol, "clientId" FROM "Protocol" WHERE id = %s', (protocol_id,))
        row = cur.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Protocol not found")
        if row['status'] != 'draft':
            raise HTTPException(status_code=400, detail="Protocol already finalized")

        stored = row['protocol']
        protocol_json = stored.get('protocol_json', {})
        lab_report_json = stored.get('lab_report_json')
        client_id = row['clientId']
        client_name = protocol_json.get('client_name', 'client')

        # Generate PDF 1 (Protocol)
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            protocol_pdf_path = f.name
        generate_protocol_pdf(protocol_json, protocol_pdf_path)
        protocol_pdf_bytes = Path(protocol_pdf_path).read_bytes()
        protocol_cloudinary = upload_pdf_bytes(protocol_pdf_bytes, f"protocol_{protocol_id}")
        logger.info(f"[finalize_protocol] Protocol PDF uploaded: {protocol_cloudinary.get('url')}")

        # Generate PDF 2 (Lab Report) if present
        lab_report_url = None
        if lab_report_json:
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
                lab_pdf_path = f.name
            generate_lab_report_pdf(lab_report_json, lab_pdf_path)
            lab_pdf_bytes = Path(lab_pdf_path).read_bytes()
            lab_cloudinary = upload_pdf_bytes(lab_pdf_bytes, f"lab_report_{protocol_id}")
            lab_report_url = lab_cloudinary.get('url')
            logger.info(f"[finalize_protocol] Lab report PDF uploaded: {lab_report_url}")

        cur.execute(
            'UPDATE "Protocol" SET status = %s, pdf_url = %s, lab_report_pdf_url = %s WHERE id = %s',
            ('final', protocol_cloudinary['url'], lab_report_url, protocol_id)
        )
        conn.commit()
        cur.close()
        conn.close()

        # Initialize client agent (non-fatal)
        try:
            from ai.client_context import ClientContext
            from ai.client_chat import ClientChat
            from api.config import CLIENT_PROTOCOLS_DIR
            import json as _json
            context = ClientContext(str(client_id), CLIENT_PROTOCOLS_DIR)
            context.save_protocol(_json.dumps(protocol_json), {
                'name': client_name,
                'client_id': client_id,
                'protocol_id': protocol_id
            })
            chunks = ClientChat(str(client_id), CLIENT_PROTOCOLS_DIR).initialize()
            logger.info(f"[finalize_protocol] Client agent initialized, chunks={chunks}")
        except Exception as agent_err:
            logger.warning(f"[finalize_protocol] Client agent init failed (non-fatal): {agent_err}")

        return {
            "protocol_id": protocol_id,
            "status": "final",
            "pdf_url": protocol_cloudinary['url'],
            "lab_report_pdf_url": lab_report_url,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[finalize_protocol] Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/practitioner/submit-for-approval/{protocol_id}")
async def submit_for_approval(protocol_id: int):
    """
    Submit a draft protocol for admin approval (status: draft -> pending_approval)
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT status FROM "Protocol" WHERE id = %s', (protocol_id,))
        row = cur.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Protocol not found")
        if row['status'] != 'draft':
            raise HTTPException(status_code=400, detail=f"Only draft protocols can be submitted. Current status: {row['status']}")

        cur.execute(
            'UPDATE "Protocol" SET status = %s WHERE id = %s',
            ('pending_approval', protocol_id)
        )
        conn.commit()
        cur.close()
        conn.close()

        logger.info(f"[submit_for_approval] Protocol {protocol_id} submitted for admin approval")
        return {"protocol_id": protocol_id, "status": "pending_approval"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[submit_for_approval] Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/practitioner/approve-protocol/{protocol_id}")
async def approve_protocol(protocol_id: int):
    """
    Admin approves protocol: generates PDFs, uploads to Cloudinary (status: pending_approval -> final)
    """
    try:
        from core.html_pdf_generator import generate_protocol_pdf, generate_lab_report_pdf

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT status, protocol, "clientId" FROM "Protocol" WHERE id = %s', (protocol_id,))
        row = cur.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Protocol not found")
        if row['status'] != 'pending_approval':
            raise HTTPException(status_code=400, detail=f"Only pending_approval protocols can be approved. Current status: {row['status']}")

        stored = row['protocol']
        protocol_json = stored.get('protocol_json', {})
        lab_report_json = stored.get('lab_report_json')
        client_id = row['clientId']
        client_name = protocol_json.get('client_name', 'client')

        # Generate + upload PDF 1 (Protocol)
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            protocol_pdf_path = f.name
        generate_protocol_pdf(protocol_json, protocol_pdf_path)
        protocol_cloudinary = upload_pdf_bytes(Path(protocol_pdf_path).read_bytes(), f"protocol_{protocol_id}")

        # Generate + upload PDF 2 (Lab Report) if present
        lab_report_url = None
        if lab_report_json:
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
                lab_pdf_path = f.name
            generate_lab_report_pdf(lab_report_json, lab_pdf_path)
            lab_cloudinary = upload_pdf_bytes(Path(lab_pdf_path).read_bytes(), f"lab_report_{protocol_id}")
            lab_report_url = lab_cloudinary.get('url')

        cur.execute(
            'UPDATE "Protocol" SET status = %s, pdf_url = %s, lab_report_pdf_url = %s WHERE id = %s',
            ('final', protocol_cloudinary['url'], lab_report_url, protocol_id)
        )
        conn.commit()

        # Initialize client agent (non-fatal)
        try:
            from ai.client_context import ClientContext
            from ai.client_chat import ClientChat
            from api.config import CLIENT_PROTOCOLS_DIR
            import json as _json
            context = ClientContext(str(client_id), CLIENT_PROTOCOLS_DIR)
            context.save_protocol(_json.dumps(protocol_json), {
                'name': client_name, 'client_id': client_id, 'protocol_id': protocol_id
            })
            ClientChat(str(client_id), CLIENT_PROTOCOLS_DIR).initialize()
        except Exception as agent_err:
            logger.warning(f"[approve_protocol] Client agent init failed (non-fatal): {agent_err}")

        cur.close()
        conn.close()

        logger.info(f"[approve_protocol] Protocol {protocol_id} approved and finalized")
        return {
            "protocol_id": protocol_id,
            "status": "final",
            "pdf_url": protocol_cloudinary['url'],
            "lab_report_pdf_url": lab_report_url,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[approve_protocol] Error: {e}", exc_info=True)
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

        stored = row['protocol']
        return {
            "protocol_id": row['id'],
            "status": row['status'],
            "client_id": row['clientId'],
            "created_by_id": row['createdById'],
            "protocol_json": stored.get('protocol_json'),
            "lab_report_json": stored.get('lab_report_json'),
            "template_type": stored.get('template_type')
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
    Generate and return a PDF preview (works for draft or final protocols)
    """
    try:
        from fastapi.responses import Response
        from utils.pdf_formatter import markdown_to_pdf

        logger.info(f"[practitioner.preview_pdf] Generating preview for protocol_id={protocol_id}")

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute('SELECT protocol FROM "Protocol" WHERE id = %s', (protocol_id,))
        row = cur.fetchone()

        cur.close()
        conn.close()

        if not row:
            raise HTTPException(status_code=404, detail="Protocol not found")

        from core.html_pdf_generator import generate_protocol_pdf
        protocol_json = row['protocol'].get('protocol_json', {})
        if not protocol_json:
            raise HTTPException(status_code=400, detail="Protocol has no content")

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            tmp_path = f.name
        generate_protocol_pdf(protocol_json, tmp_path)
        pdf_bytes = Path(tmp_path).read_bytes()
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
        raise HTTPException(status_code=500, detail=str(e))
