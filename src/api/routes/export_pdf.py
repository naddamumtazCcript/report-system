"""PDF export endpoint"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
import logging
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_LEFT, TA_CENTER

logger = logging.getLogger(__name__)

from ..config import OUTPUT_DIR

router = APIRouter()

@router.get("/export/pdf/{job_id}")
async def export_pdf(job_id: str):
    """Export protocol as PDF"""
    try:
        logger.info(f"Exporting PDF for job_id: {job_id}")
        
        # Find protocol markdown file
        protocol_file = OUTPUT_DIR / f"{job_id}_protocol.md"
        if not protocol_file.exists():
            raise HTTPException(status_code=404, detail="Protocol not found")
        
        # Read markdown
        with open(protocol_file, 'r') as f:
            content = f.read()
        
        # Generate PDF
        pdf_file = OUTPUT_DIR / f"{job_id}_protocol.pdf"
        doc = SimpleDocTemplate(str(pdf_file), pagesize=letter,
                                rightMargin=72, leftMargin=72,
                                topMargin=72, bottomMargin=18)
        
        # Styles
        styles = getSampleStyleSheet()
        story = []
        
        # Parse markdown and convert to PDF elements
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                story.append(Spacer(1, 0.2*inch))
            elif line.startswith('# '):
                p = Paragraph(line[2:], styles['Title'])
                story.append(p)
                story.append(Spacer(1, 0.3*inch))
            elif line.startswith('## '):
                p = Paragraph(line[3:], styles['Heading1'])
                story.append(p)
                story.append(Spacer(1, 0.2*inch))
            elif line.startswith('### '):
                p = Paragraph(line[4:], styles['Heading2'])
                story.append(p)
                story.append(Spacer(1, 0.1*inch))
            elif line.startswith('* ') or line.startswith('- '):
                p = Paragraph('• ' + line[2:], styles['Normal'])
                story.append(p)
            elif line == '---':
                story.append(Spacer(1, 0.3*inch))
            else:
                p = Paragraph(line, styles['Normal'])
                story.append(p)
        
        doc.build(story)
        
        logger.info(f"PDF generated: {pdf_file}")
        
        return FileResponse(
            path=pdf_file,
            media_type="application/pdf",
            filename=f"protocol_{job_id}.pdf"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF export failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"PDF export failed: {str(e)}")
