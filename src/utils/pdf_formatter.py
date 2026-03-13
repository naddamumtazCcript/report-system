"""
PDF Formatter - Convert markdown protocol to professionally formatted PDF
"""
import re
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable
)
from reportlab.lib import colors


def create_styles():
    """Create custom styles for the protocol PDF"""
    styles = getSampleStyleSheet()
    
    # Title style (client name)
    styles.add(ParagraphStyle(
        name='ProtocolTitle',
        parent=styles['Title'],
        fontSize=22,
        textColor=HexColor('#111827'),
        spaceAfter=4,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
    ))
    
    # Date style
    styles.add(ParagraphStyle(
        name='ProtocolDate',
        parent=styles['Normal'],
        fontSize=12,
        textColor=HexColor('#4a5568'),
        alignment=TA_CENTER,
        spaceAfter=20,
    ))
    
    # Section header (## SECTION X)
    styles.add(ParagraphStyle(
        name='SectionHeader',
        parent=styles['Heading1'],
        fontSize=14,
        textColor=HexColor('#1a365d'),
        spaceBefore=16,
        spaceAfter=8,
        fontName='Helvetica-Bold',
    ))
    
    # Subsection header (## other headings)
    styles.add(ParagraphStyle(
        name='SubsectionHeader',
        parent=styles['Heading2'],
        fontSize=13,
        textColor=HexColor('#1a365d'),
        spaceBefore=12,
        spaceAfter=6,
        fontName='Helvetica-Bold',
    ))
    
    # Sub-subsection (### headings)
    styles.add(ParagraphStyle(
        name='SubSubHeader',
        parent=styles['Heading3'],
        fontSize=11,
        textColor=HexColor('#374151'),
        spaceBefore=8,
        spaceAfter=4,
        fontName='Helvetica-Bold',
    ))
    
    # Normal body text
    styles.add(ParagraphStyle(
        name='ProtocolBody',
        parent=styles['Normal'],
        fontSize=10,
        textColor=HexColor('#374151'),
        spaceBefore=2,
        spaceAfter=2,
        leading=13,
    ))
    
    # Bullet point
    styles.add(ParagraphStyle(
        name='BulletPoint',
        parent=styles['Normal'],
        fontSize=10,
        textColor=HexColor('#374151'),
        leftIndent=18,
        spaceBefore=1,
        spaceAfter=1,
        bulletIndent=8,
        leading=13,
    ))
    
    # Concern/label style
    styles.add(ParagraphStyle(
        name='ConcernLabel',
        parent=styles['Normal'],
        fontSize=11,
        textColor=HexColor('#1a365d'),
        fontName='Helvetica-Bold',
        spaceBefore=10,
        spaceAfter=3,
    ))
    
    # Disclaimer style
    styles.add(ParagraphStyle(
        name='Disclaimer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=HexColor('#718096'),
        spaceBefore=20,
        spaceAfter=10,
        leading=12,
    ))
    
    return styles


def convert_inline_markdown(text):
    """Convert inline markdown to ReportLab XML tags"""
    if not text:
        return ""
    
    # First, remove strikethrough content completely (AI instructions)
    text = re.sub(r'~~[^~]+~~', '', text)
    
    # Remove any remaining tildes
    text = text.replace('~~', '')
    
    # Escape special XML characters
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    
    # Bold: **text** or __text__
    text = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'__([^_]+)__', r'<b>\1</b>', text)
    
    # Italic: *text* or _text_ (but not inside bold)
    text = re.sub(r'(?<![*])\*([^*]+)\*(?![*])', r'<i>\1</i>', text)
    text = re.sub(r'(?<!_)_([^_]+)_(?!_)', r'<i>\1</i>', text)
    
    # Code: `text`
    text = re.sub(r'`([^`]+)`', r'<font face="Courier">\1</font>', text)
    
    return text.strip()


def should_skip_line(line):
    """Check if a line should be skipped (AI instructions, etc.)"""
    line_lower = line.lower().strip()
    
    # Skip patterns - check lowercase
    skip_patterns = [
        'instructions for ai',
        'populate all fields',
        'do not invent',
        'if data is missing',
        'use clear, professional',
        'do not diagnose',
        'use word for word',
    ]
    
    for pattern in skip_patterns:
        if pattern in line_lower:
            return True
    
    # Skip lines that are just strikethrough
    if line.strip().startswith('~~') and line.strip().endswith('~~'):
        return True
    
    # Skip lines that contain only strikethrough content
    cleaned = re.sub(r'~~[^~]+~~', '', line).strip()
    if not cleaned and '~~' in line:
        return True
    
    return False


def clean_line(line):
    """Clean a line by removing AI instructions and strikethrough"""
    # Remove strikethrough content
    line = re.sub(r'~~[^~]+~~', '', line)
    line = line.replace('~~', '')
    return line.strip()


def parse_table(lines, start_idx):
    """Parse a markdown table starting at start_idx, return (table_data, end_idx)"""
    table_data = []
    i = start_idx
    
    while i < len(lines):
        line = lines[i].strip()
        if not line.startswith('|'):
            break
        
        # Skip separator line (|---|---|)
        if re.match(r'^\|[\s:\-|]+\|$', line):
            i += 1
            continue
        
        # Parse cells
        cells = [cell.strip() for cell in line.split('|')[1:-1]]
        if cells and any(c for c in cells):  # Skip if all cells are empty
            table_data.append(cells)
        i += 1
    
    return table_data, i


def create_table_flowable(table_data, styles):
    """Create a ReportLab Table from parsed table data"""
    if not table_data:
        return None
    
    # Convert markdown in cells
    processed_data = []
    for row in table_data:
        processed_row = [
            Paragraph(convert_inline_markdown(cell), styles['ProtocolBody'])
            for cell in row
        ]
        processed_data.append(processed_row)
    
    # Calculate column widths
    num_cols = len(processed_data[0]) if processed_data else 1
    col_width = (letter[0] - 144) / num_cols  # 144 = margins
    
    table = Table(processed_data, colWidths=[col_width] * num_cols)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#e2e8f0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#2d3748')),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#cbd5e0')),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
    ]))
    
    return table


def markdown_to_pdf(markdown_content):
    """
    Convert markdown protocol content to a formatted PDF.
    Returns PDF bytes.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72,
    )
    
    styles = create_styles()
    story = []
    
    lines = markdown_content.split('\n')
    i = 0
    
    while i < len(lines):
        original_line = lines[i]
        line = original_line.strip()
        
        # Skip empty lines with small spacer
        if not line:
            story.append(Spacer(1, 0.06 * inch))
            i += 1
            continue
        
        # Skip AI instruction lines
        if should_skip_line(line):
            i += 1
            continue
        
        # Clean the line (remove strikethrough, etc.)
        line = clean_line(line)
        if not line:
            i += 1
            continue
        
        # Skip horizontal rules
        if line == '---':
            story.append(HRFlowable(
                width="100%",
                thickness=0.5,
                color=HexColor('#d1d5db'),
                spaceBefore=6,
                spaceAfter=6,
            ))
            i += 1
            continue
        
        # Handle tables
        if line.startswith('|'):
            table_data, end_idx = parse_table(lines, i)
            if table_data:
                table = create_table_flowable(table_data, styles)
                if table:
                    story.append(Spacer(1, 0.1 * inch))
                    story.append(table)
                    story.append(Spacer(1, 0.1 * inch))
            i = end_idx
            continue
        
        # Title (# heading - usually client name)
        if line.startswith('# '):
            text = convert_inline_markdown(line[2:])
            if text:
                # Check if it's "Goals Action Plan" or similar
                if 'goal' in text.lower() or 'action plan' in text.lower():
                    story.append(Spacer(1, 0.12 * inch))
                    story.append(Paragraph(text, styles['SectionHeader']))
                else:
                    story.append(Paragraph(text, styles['ProtocolTitle']))
            i += 1
            continue
        
        # Section headers (## **SECTION X: ...**) - remove ** markers
        if line.startswith('## '):
            text = line[3:]
            # Remove ** markers for processing
            text = text.replace('**', '')
            text = convert_inline_markdown(text)
            
            if text:
                if 'SECTION' in text.upper():
                    story.append(Spacer(1, 0.15 * inch))
                    story.append(Paragraph(text, styles['SectionHeader']))
                else:
                    story.append(Paragraph(text, styles['SubsectionHeader']))
            i += 1
            continue
        
        # Sub-headers (### heading)
        if line.startswith('### '):
            text = line[4:].replace('**', '')
            text = convert_inline_markdown(text)
            if text:
                story.append(Paragraph(text, styles['SubSubHeader']))
            i += 1
            continue
        
        # Numbered list
        if re.match(r'^\d+\.\s', line):
            text = re.sub(r'^\d+\.\s*', '', line)
            text = convert_inline_markdown(text)
            num_match = re.match(r'^(\d+)\.', line)
            num = num_match.group(1) if num_match else '•'
            if text:
                story.append(Paragraph(f'{num}. {text}', styles['BulletPoint']))
            i += 1
            continue
        
        # Bullet points (* or -)
        if line.startswith('* ') or line.startswith('- '):
            text = line[2:]
            text = convert_inline_markdown(text)
            if text:
                story.append(Paragraph(f'• {text}', styles['BulletPoint']))
            i += 1
            continue
        
        # Empty bullet points (just * or -)
        if line == '*' or line == '-':
            i += 1
            continue
        
        # Concern labels (**Concern 1:** etc)
        if re.match(r'^\*\*Concern \d+:', line):
            text = convert_inline_markdown(line)
            if text:
                story.append(Paragraph(text, styles['ConcernLabel']))
            i += 1
            continue
        
        # Bold-only lines (like **SECTION 1: GENERAL**) - treat as headers
        if line.startswith('**') and line.endswith('**') and line.count('**') == 2:
            text = line[2:-2]  # Remove ** from start and end
            text = convert_inline_markdown(text)
            if text:
                if 'SECTION' in text.upper():
                    story.append(Spacer(1, 0.15 * inch))
                    story.append(Paragraph(text, styles['SectionHeader']))
                elif 'DISCLAIMER' in text.upper():
                    story.append(Spacer(1, 0.15 * inch))
                    story.append(Paragraph(text, styles['SubsectionHeader']))
                else:
                    story.append(Paragraph(text, styles['SubsectionHeader']))
            i += 1
            continue
        
        # Check if it's a date line (like "March 12, 2026")
        if re.match(r'^(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d', line):
            text = convert_inline_markdown(line)
            if text:
                story.append(Paragraph(text, styles['ProtocolDate']))
            i += 1
            continue
        
        # Regular paragraph
        text = convert_inline_markdown(line)
        if text:
            # Check if it's disclaimer text
            if 'educational purposes only' in line.lower() or 'not intended to replace' in line.lower():
                story.append(Paragraph(text, styles['Disclaimer']))
            else:
                story.append(Paragraph(text, styles['ProtocolBody']))
        
        i += 1
    
    doc.build(story)
    return buffer.getvalue()
