"""
HTML-based PDF Generator using Playwright
Renders HTML template and converts to PDF with full CSS support
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from jinja2 import Template
from playwright.sync_api import sync_playwright
from typing import Dict, Any
from datetime import datetime
import logging
import os

logger = logging.getLogger(__name__)


def generate_protocol_pdf(protocol_data: Dict[str, Any], output_path: str) -> str:
    """Generate PDF from HTML template using Playwright"""
    try:
        logger.info("Generating PDF from HTML template...")
        
        # Prepare data
        formatted_data = prepare_protocol_data(protocol_data)
        
        # Load template
        template_path = Path(__file__).parent.parent.parent / "templates" / "template.html"
        with open(template_path, 'r') as f:
            template_content = f.read()
        
        # Render template
        template = Template(template_content)
        html_content = template.render(**formatted_data)
        
        # Save HTML temporarily
        html_output = output_path.replace('.pdf', '.html')
        with open(html_output, 'w') as f:
            f.write(html_content)
        
        logger.info(f"HTML generated: {html_output}")
        
        # Convert HTML to PDF using Playwright
        logger.info("Converting HTML to PDF...")
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            
            # Load HTML file
            html_file_path = f"file://{os.path.abspath(html_output)}"
            page.goto(html_file_path)
            
            # Generate PDF
            page.pdf(
                path=output_path,
                format='Letter',
                print_background=True,
                margin={
                    'top': '0',
                    'right': '0',
                    'bottom': '0',
                    'left': '0'
                }
            )
            
            browser.close()
        
        logger.info(f"PDF generated: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
        raise


def prepare_protocol_data(protocol_data: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare protocol data with defaults"""
    protocol_data['current_year'] = datetime.now().year
    
    defaults = {
        'client_name': 'Client',
        'date': datetime.now().strftime('%B %d, %Y'),
        'focus_items': [],
        'concerns': [],
        'lab_review_content': '',
        'primary_nutrition_goal': '',
        'hydration_target': '',
        'core_habits': [],
        'additional_supports': [],
        'why_nutrition_helps': '',
        'program_length': '',
        'calories': '',
        'protein': '',
        'carbohydrates': '',
        'fat': '',
        'fiber': '',
        'food_recommendations_content': '',
        'daily_steps_target': '',
        'strength_frequency': '',
        'strength_split': '',
        'stress_supports': [],
        'avoid_mindful': '',
        'pause_supplements': [],
        'active_supplements_content': '',
        'titration_schedule': {},
        'early_changes': '',
        'mid_changes': '',
        'long_term_changes': '',
        'progress_criteria': '',
        'next_phase_focus': '',
        'goals': [],
        'follow_up_recommended': '',
        'booking_link': '',
        'follow_up_tests': [],
        'video_link': ''
    }
    
    for key, default in defaults.items():
        if key not in protocol_data:
            protocol_data[key] = default
    
    return protocol_data


if __name__ == "__main__":
    test_data = {
        'client_name': 'Sarah Mitchell',
        'date': 'March 13, 2026',
        'focus_items': ['Balance hormones', 'Improve energy', 'Support digestion'],
        'concerns': [
            {
                'description': 'Low energy and fatigue throughout the day',
                'drivers': 'Blood sugar dysregulation, elevated cortisol'
            },
            {
                'description': 'Irregular menstrual cycles',
                'drivers': 'Elevated estrogen, low progesterone'
            }
        ],
        'primary_nutrition_goal': 'Balance blood sugar and support hormone health',
        'calories': '1800-2000 kcal',
        'protein': '120-140g',
        'carbohydrates': '150-180g',
        'fat': '60-70g',
        'fiber': '30-35g',
        'daily_steps_target': '8,000-10,000 steps',
        'strength_frequency': '3-4x per week',
        'strength_split': 'Upper/Lower split'
    }
    
    output = "/tmp/test_playwright_pdf.pdf"
    generate_protocol_pdf(test_data, output)
    print(f"Test PDF: {output}")
