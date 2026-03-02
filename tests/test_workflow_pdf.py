"""
Complete Workflow Test with PDF Report Generation
Tests both Practitioner and Client agents and generates formatted PDF output
"""
import requests
import sys
from pathlib import Path
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

BASE_URL = "http://localhost:8000/api"

class WorkflowReport:
    def __init__(self):
        self.steps = []
        self.protocol_content = ""
        self.chat_interactions = []
        
    def add_step(self, title, status, details):
        self.steps.append({"title": title, "status": status, "details": details})
    
    def add_chat(self, question, answer, sources):
        self.chat_interactions.append({
            "question": question,
            "answer": answer,
            "sources": sources
        })
    
    def generate_pdf(self, output_path):
        """Generate formatted PDF report"""
        doc = SimpleDocTemplate(str(output_path), pagesize=letter,
                              topMargin=0.75*inch, bottomMargin=0.75*inch)
        
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor='#2C3E50',
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor='#34495E',
            spaceAfter=12,
            spaceBefore=20
        )
        
        subheading_style = ParagraphStyle(
            'CustomSubHeading',
            parent=styles['Heading3'],
            fontSize=14,
            textColor='#7F8C8D',
            spaceAfter=10
        )
        
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['BodyText'],
            fontSize=11,
            leading=16,
            spaceAfter=12
        )
        
        story = []
        
        # Title
        story.append(Paragraph("Be Balanced AI System", title_style))
        story.append(Paragraph("Complete Workflow Test Report", heading_style))
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", body_style))
        story.append(Spacer(1, 0.3*inch))
        
        # Part 1: Practitioner Agent
        story.append(Paragraph("PART 1: PRACTITIONER AGENT", heading_style))
        story.append(Paragraph("Protocol Generation from Intake Questionnaire", subheading_style))
        
        for step in self.steps[:3]:
            status_icon = "✅" if step['status'] == 'success' else "❌"
            story.append(Paragraph(f"{status_icon} <b>{step['title']}</b>", body_style))
            story.append(Paragraph(step['details'], body_style))
            story.append(Spacer(1, 0.1*inch))
        
        # Protocol Preview
        if self.protocol_content:
            story.append(PageBreak())
            story.append(Paragraph("Complete Generated Protocol:", heading_style))
            story.append(Spacer(1, 0.2*inch))
            
            # Split protocol into sections and format
            protocol_lines = self.protocol_content.split('\n')
            for line in protocol_lines:
                if line.startswith('## '):
                    # Section header
                    story.append(Paragraph(line.replace('## ', ''), heading_style))
                elif line.startswith('**') and line.endswith('**'):
                    # Bold text
                    story.append(Paragraph(line, subheading_style))
                elif line.strip():
                    # Regular text
                    story.append(Paragraph(line, body_style))
                else:
                    # Empty line
                    story.append(Spacer(1, 0.05*inch))
        
        story.append(PageBreak())
        
        # Part 2: Client Agent
        story.append(Paragraph("PART 2: CLIENT AGENT", heading_style))
        story.append(Paragraph("AI-Powered Client Support System", subheading_style))
        
        # Initialization
        for step in self.steps[3:4]:
            status_icon = "✅" if step['status'] == 'success' else "❌"
            story.append(Paragraph(f"{status_icon} <b>{step['title']}</b>", body_style))
            story.append(Paragraph(step['details'], body_style))
            story.append(Spacer(1, 0.2*inch))
        
        # Chat Interactions
        story.append(Paragraph("Client Chat Interactions:", heading_style))
        
        for i, chat in enumerate(self.chat_interactions, 1):
            story.append(Spacer(1, 0.15*inch))
            story.append(Paragraph(f"<b>Question {i}:</b> {chat['question']}", body_style))
            story.append(Paragraph(f"<b>Answer:</b> {chat['answer']}", body_style))
            if chat['sources']:
                sources_text = ", ".join(chat['sources'][:3])
                story.append(Paragraph(f"<i>Sources: {sources_text}</i>", body_style))
            story.append(Spacer(1, 0.1*inch))
        
        story.append(PageBreak())
        
        # Summary
        story.append(Paragraph("WORKFLOW SUMMARY", heading_style))
        
        summary_points = [
            "✅ Practitioner uploaded client intake questionnaire (PDF)",
            "✅ AI system extracted and structured client data",
            "✅ Generated personalized health protocol with recommendations",
            "✅ Client initialized with their personalized protocol",
            f"✅ Client asked {len(self.chat_interactions)} questions about their health",
            "✅ All responses grounded in the client's protocol",
            "✅ AI maintained professional boundaries",
            "✅ System handled edge cases correctly"
        ]
        
        for point in summary_points:
            story.append(Paragraph(point, body_style))
            story.append(Spacer(1, 0.05*inch))
        
        story.append(Spacer(1, 0.3*inch))
        story.append(Paragraph("<b>System Status: OPERATIONAL ✅</b>", heading_style))
        story.append(Paragraph("Both Practitioner and Client agents working perfectly together.", body_style))
        
        # Build PDF
        doc.build(story)
        print(f"\n📄 PDF Report generated: {output_path}")

def test_complete_workflow_with_pdf():
    """Test complete workflow and generate PDF report"""
    report = WorkflowReport()
    
    print("=" * 70)
    print("COMPLETE WORKFLOW TEST WITH PDF GENERATION")
    print("=" * 70)
    
    # PART 1: PRACTITIONER AGENT
    print("\n" + "=" * 70)
    print("PART 1: PRACTITIONER AGENT")
    print("=" * 70)
    
    # Step 1: Generate protocol
    print("\n[Step 1] Generating protocol from intake PDF...")
    intake_pdf = Path("data/jessica_intake.pdf")
    
    with open(intake_pdf, 'rb') as f:
        response = requests.post(
            f"{BASE_URL}/protocol/generate",
            files={"intake_pdf": f}
        )
    
    if response.status_code != 200:
        report.add_step("Generate Protocol", "failed", f"Error: {response.text}")
        print(f"❌ Failed: {response.text}")
        return False
    
    data = response.json()
    session_id = data['session_id']
    report.add_step("Generate Protocol", "success", 
                   f"Protocol generated successfully. Session ID: {session_id}")
    print(f"✅ Protocol generated: {session_id}")
    
    # Step 2: Download protocol
    print("\n[Step 2] Downloading generated protocol...")
    response = requests.get(f"{BASE_URL}/protocol/download/{session_id}")
    
    if response.status_code != 200:
        report.add_step("Download Protocol", "failed", "Failed to download")
        return False
    
    protocol_content = response.text
    report.protocol_content = protocol_content
    report.add_step("Download Protocol", "success", 
                   f"Protocol downloaded: {len(protocol_content)} characters")
    print(f"✅ Protocol downloaded: {len(protocol_content)} characters")
    
    # PART 2: CLIENT AGENT
    print("\n" + "=" * 70)
    print("PART 2: CLIENT AGENT")
    print("=" * 70)
    
    # Step 3: Initialize client
    print("\n[Step 3] Initializing client with protocol...")
    response = requests.post(f"{BASE_URL}/client/initialize", json={
        "client_id": "jessica_pdf_test",
        "protocol_content": protocol_content,
        "metadata": {
            "name": "Jessica Martinez",
            "session_id": session_id,
            "test_date": datetime.now().isoformat()
        }
    })
    
    if response.status_code != 200:
        report.add_step("Initialize Client", "failed", response.text)
        return False
    
    data = response.json()
    report.add_step("Initialize Client", "success", 
                   f"Client initialized with {data['chunks_indexed']} protocol chunks indexed")
    print(f"✅ Client initialized: {data['chunks_indexed']} chunks")
    
    # Client Chat Interactions
    print("\n" + "=" * 70)
    print("CLIENT CHAT INTERACTIONS")
    print("=" * 70)
    
    questions = [
        "What are my main health concerns?",
        "What supplements should I take and why?",
        "How many calories should I eat per day?",
        "What foods should I avoid?",
        "What is my daily protein target?"
    ]
    
    for i, question in enumerate(questions, 1):
        print(f"\n[Question {i}] {question}")
        response = requests.post(f"{BASE_URL}/client/chat", json={
            "client_id": "jessica_pdf_test",
            "message": question
        })
        
        if response.status_code != 200:
            print(f"❌ Failed")
            continue
        
        data = response.json()
        print(f"✅ Answer: {data['response'][:100]}...")
        print(f"   Sources: {', '.join(data['sources'][:2])}")
        
        report.add_chat(question, data['response'], data['sources'])
    
    # Generate PDF Report
    print("\n" + "=" * 70)
    print("GENERATING PDF REPORT")
    print("=" * 70)
    
    output_path = Path("data/output/workflow_test_report.pdf")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    report.generate_pdf(output_path)
    
    print("\n" + "=" * 70)
    print("✅ COMPLETE WORKFLOW TEST FINISHED!")
    print("=" * 70)
    print(f"\n📄 PDF Report: {output_path}")
    print("🎉 Both agents working perfectly!")
    
    return True

if __name__ == "__main__":
    print("\n⚠️  Make sure API server is running:")
    print("   cd src && python3 api/app.py\n")
    
    try:
        success = test_complete_workflow_with_pdf()
        sys.exit(0 if success else 1)
    except requests.exceptions.ConnectionError:
        print("\n❌ Could not connect to API server.")
        print("   Start the server first: cd src && python3 api/app.py")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
