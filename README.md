# Be Balanced AI - Practitioner Agent

AI-powered system that automates creation of personalized health protocols from client intake questionnaires and lab reports.

## Overview

Converts client-filled questionnaires and lab reports into two personalized documents:
- **PDF 1 — Full Protocol**: Nutrition, lifestyle, supplement plan
- **PDF 2 — Lab Interpretation Report**: EndoAxis-style narrative report (only when labs are attached)

Both documents are generated as JSON + PDF, stored in PostgreSQL and Cloudinary, and require admin approval before delivery.

## Features

- **2-PDF Generation** - Protocol PDF + Lab Interpretation Report per run
- **AI Data Mapping** - GPT-4o-mini maps questionnaire JSON to structured intake data
- **Lab Extraction** - Gemini 2.5 Flash extracts structured markers from DUTCH, GI-MAP, Bloodwork PDFs
- **Batch Lab Analysis** - All markers analyzed in a single GPT call (what we found, why it matters, symptoms)
- **Smart Recommendations** - GPT generates nutrition, supplement, lifestyle, what-to-expect, and goals plans
- **Admin Approval Flow** - Protocols require admin approval before PDFs are generated and delivered
- **Cloud Storage** - PDFs stored on Cloudinary CDN
- **PostgreSQL Storage** - Protocol JSON saved to DB with full lifecycle tracking
- **Error Handling** - Production-ready error handling and logging

## Project Structure

```
report-system/
├── src/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── practitioner.py    # Protocol generation & approval endpoints
│   │   │   ├── lab_extraction.py  # Standalone lab extraction endpoint
│   │   │   ├── client.py          # Client chat endpoints
│   │   │   └── ...
│   │   └── app.py                 # FastAPI app entry point
│   ├── core/                      # Data mapping, HTML/PDF generation
│   ├── ai/                        # Lab analyzer, knowledge base, lab report generator
│   └── utils/                     # Error handling, logging, Cloudinary helper
├── templates/
│   ├── ProtocolTemplate.md        # Protocol structure reference
│   ├── template.html              # Protocol PDF HTML template
│   └── lab_report_template.html   # Lab interpretation PDF HTML template
├── knowledge_base/                # Practitioner knowledge libraries
└── output/                        # Generated JSONs and PDFs
```

## Setup

1. **Install dependencies**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

2. **Configure API keys** — create `.env` file:
```
OPENAI_API_KEY=your-openai-key
GEMINI_API_KEY=your-gemini-key
DATABASE_URL=your-postgres-url
CLOUD_NAME=your-cloudinary-name
CLOUDINARY_API_KEY=your-cloudinary-key
CLOUDINARY_API_SECRET=your-cloudinary-secret
```

3. **Run the API server**
```bash
cd src
python3 -m uvicorn api.app:app --reload
```

---

## API Endpoints

### Protocol Status Flow

```
generate-protocol → pending_approval
                         ↓
                   approve-protocol → final
                         ↓ (if rejected)
                   reopen-protocol → draft
                         ↓
                   submit-for-approval → pending_approval
```

---

### POST `/api/practitioner/generate-protocol`

Generate a protocol from a questionnaire + optional lab results. Saves to DB with `pending_approval` status.

**Request body** (`application/json`):
```json
{
  "user_id": 3,
  "client_id": 4,
  "template_type": "standard",
  "questionnaire": {
    "answers": {
      "personal_info": {
        "legal_first_name": "Sarah",
        "last_name": "Mitchell",
        "gender": "Female",
        "date_of_birth": "03/15/1990",
        "current_weight": "165",
        "height": "5'6\"",
        "occupation": "Office job",
        "email": "sarah@email.com",
        "mobile_phone": "(555) 123-4567"
      },
      "health_info": {
        "official_diagnoses": "PCOS",
        "main_symptoms_ordered": [
          "Chronic fatigue and low energy levels",
          "Irregular menstrual cycles",
          "Difficulty losing weight"
        ],
        "short_term_goals": "Regulate cycle, increase energy",
        "long_term_goals": "Lose 15-20 pounds, reduce stress",
        "current_supplements": "Vitamin D 2000 IU, Fish Oil",
        "prescription_medications": "None"
      },
      "nutrition_preferences": {
        "foods_to_avoid": "Dairy",
        "nutrition_struggles": "Difficulty losing weight"
      },
      "fitness": {
        "weekly_workout_description": "3x per week (yoga, walking)"
      },
      "lifestyle": {
        "energy_levels": "3/10",
        "sleep_quality": "4/10",
        "alcohol_frequency": "2-3 glasses wine per week"
      },
      "digestive_health": {
        "digestive_symptoms": "Bloating, gas"
      },
      "supplement_preferences": {
        "supplement_preference": "Prefer natural approaches"
      },
      "goals": {
        "wellness_journey_excitement": "Willing to make dietary changes"
      }
    }
  },
  "lab_reports": [
    {
      "report_type": "DUTCH Complete",
      "report_date": "2024-01-15",
      "results": [
        {
          "test_name": "Estrone (E1)",
          "value": "30.28",
          "unit": "ng/mg",
          "reference_range": "12-26",
          "flag": "Above luteal range"
        },
        {
          "test_name": "Total Estrogen",
          "value": "80.9",
          "unit": "ng/mg",
          "reference_range": "35-70",
          "flag": "Above range"
        }
      ]
    }
  ]
}
```

**Notes:**
- `questionnaire.answers` accepts either INTAKE_SCHEMA format (nested `personal_info`, `health_info`, etc.) or flat camelCase format (`legalFirstName`, `lastName`, etc.)
- `lab_reports` is optional — omit or pass `[]` for questionnaire-only protocols
- Supported `flag` values: `Above range`, `Below range`, `Above luteal range`, `High end of range`, `Within range`, `H`, `L`, etc.

**Response** `200`:
```json
{
  "protocol_id": 36,
  "status": "pending_approval",
  "has_lab_report": true
}
```

---

### POST `/api/practitioner/approve-protocol/{protocol_id}`

Admin approves a `pending_approval` protocol. Generates both PDFs, uploads to Cloudinary, sets status to `final`.

**No request body.**

**Response** `200`:
```json
{
  "protocol_id": 36,
  "status": "final",
  "pdf_url": "https://res.cloudinary.com/.../protocol_36.pdf",
  "lab_report_pdf_url": "https://res.cloudinary.com/.../lab_report_36.pdf"
}
```

`lab_report_pdf_url` is `null` if no lab reports were attached.

---

### POST `/api/practitioner/submit-for-approval/{protocol_id}`

Re-submit a `draft` protocol for admin approval.

**No request body.**

**Response** `200`:
```json
{
  "protocol_id": 36,
  "status": "pending_approval"
}
```

**Errors:**
- `404` — protocol not found
- `400` — protocol is not in `draft` status

---

### POST `/api/practitioner/reopen-protocol/{protocol_id}`

Reopen a `final` protocol for editing. Clears `pdf_url`, sets status to `draft`.

**No request body.**

**Response** `200`:
```json
{
  "protocol_id": 36,
  "status": "draft"
}
```

**Errors:**
- `404` — protocol not found
- `400` — protocol is not in `final` status

---

### PUT `/api/practitioner/edit-protocol/{protocol_id}`

Edit the `protocol_json` of a `draft` protocol.

**Request body** — full replacement `protocol_json` object:
```json
{
  "client_name": "Sarah Mitchell",
  "date": "March 18, 2026",
  "primary_nutrition_goal": "Balance blood sugar and support hormone health",
  "active_supplements": [
    {
      "name": "Myo-Inositol",
      "purpose": "Supports insulin sensitivity and ovarian function in PCOS",
      "duration": "ongoing"
    }
  ]
}
```

**Response** `200`:
```json
{
  "protocol_id": 36,
  "status": "draft"
}
```

**Errors:**
- `404` — protocol not found
- `400` — protocol is not in `draft` status

---

### GET `/api/practitioner/protocol/{protocol_id}`

Fetch the full protocol record by ID.

**Response** `200`:
```json
{
  "protocol_id": 36,
  "status": "pending_approval",
  "client_id": 4,
  "created_by_id": 3,
  "template_type": "standard",
  "protocol_json": {
    "client_name": "Sarah Mitchell",
    "date": "March 18, 2026",
    "focus_items": ["Balance blood sugar", "Support hormone health", "Improve sleep"],
    "concerns": [
      {
        "description": "Chronic fatigue and low energy levels",
        "drivers": "Adrenal fatigue due to chronic stress and hormonal imbalance"
      }
    ],
    "lab_markers": [
      {
        "test_name": "Estrone (E1)",
        "value": "30.28",
        "unit": "ng/mg",
        "reference_range": "12-26",
        "flag": "Above luteal range",
        "flag_normalized": "H",
        "is_out_of_range": true,
        "what_we_found": "Estrone is elevated at 30.28 ng/mg, above the luteal range of 12-26.",
        "why_this_matters": "Elevated estrone can contribute to estrogen dominance symptoms including mood swings and weight gain.",
        "symptoms": "mood swings, weight gain, breast tenderness"
      }
    ],
    "primary_nutrition_goal": "Balance blood sugar and support hormone health",
    "hydration_target": "80-100 oz water daily",
    "core_habits": [
      "Prioritize balanced meals with protein and fiber to regulate blood sugar",
      "Stay hydrated throughout the day",
      "Practice stress-reduction techniques such as mindfulness or yoga"
    ],
    "calories": "2263",
    "protein": "148g",
    "carbohydrates": "260g",
    "fat": "70g",
    "fiber": "30g",
    "program_length": "12 weeks",
    "daily_steps_target": "8,000-10,000 steps",
    "strength_frequency": "3x per week",
    "strength_split": "2 upper / 1 lower",
    "stress_supports": ["Box breathing", "Evening walk", "Journaling"],
    "avoid_mindful": "Alcohol, refined sugar, processed foods",
    "active_supplements": [
      {
        "name": "Myo-Inositol",
        "purpose": "Supports insulin sensitivity and ovarian function in PCOS",
        "duration": "ongoing"
      },
      {
        "name": "Magnesium Glycinate",
        "purpose": "Supports energy, sleep quality, and mood regulation",
        "duration": "ongoing"
      }
    ],
    "pause_supplements": [],
    "titration_schedule": {
      "week_1": "Start Magnesium Glycinate 200mg at bedtime",
      "week_2": "Add Myo-Inositol 2g with breakfast",
      "week_3": "Assess tolerance, increase Myo-Inositol to 4g if well tolerated"
    },
    "early_changes": "Weeks 1-4: improved sleep quality, reduced bloating, steadier energy",
    "mid_changes": "Weeks 4-8: hormonal shifts, more regular cycle, gradual weight changes",
    "long_term_changes": "Weeks 8-12+: sustained energy, improved cycle regularity, clearer skin",
    "progress_criteria": "Cycle length under 35 days, energy rating above 6/10, consistent sleep",
    "next_phase_focus": "Introduce targeted detox support and reassess supplement stack",
    "goals": [
      {
        "goal": "Regulate menstrual cycle",
        "action": "Myo-Inositol + blood sugar balancing nutrition + stress reduction"
      },
      {
        "goal": "Increase energy levels",
        "action": "Magnesium Glycinate + consistent sleep routine + strength training"
      }
    ],
    "follow_up_recommended": "Yes",
    "follow_up_tests": [],
    "video_link": "",
    "booking_link": "",
    "additional_supports": [],
    "food_recommendations_content": "",
    "why_nutrition_helps": "Balancing blood sugar reduces cortisol spikes and supports ovarian function in PCOS."
  },
  "lab_report_json": {
    "client_name": "Sarah Mitchell",
    "client_age": "34",
    "client_gender": "Female",
    "report_type": "DUTCH Complete",
    "report_date": "2024-01-15",
    "overview": "Elevated total estrogen with impaired methylation pathway. Evening cortisol elevation suggests HPA axis dysregulation.",
    "hormonal_insights": [
      {
        "content": "Total estrogen is elevated at 80.9 ng/mg (ref: 35-70). Estrone and estradiol are both above range, indicating estrogen dominance."
      }
    ],
    "adrenal_insights": [
      {
        "content": "Cortisol is elevated at dinner and bedtime, disrupting the normal diurnal decline. This pattern is associated with poor sleep onset and evening anxiety."
      }
    ],
    "findings": [],
    "strategy_analysis": "Focus on estrogen clearance via methylation support (B12, folate), liver detox pathways, and cortisol regulation through evening wind-down practices.",
    "disclaimer": "This report is for educational purposes only and does not constitute medical advice."
  }
}
```

---

### GET `/api/practitioner/protocol/{protocol_id}/pdf`

Redirect to the Cloudinary PDF URL. Only works for `final` protocols.

**Response** `302` — redirect to Cloudinary URL.

**Errors:**
- `404` — protocol not found or PDF not generated
- `400` — protocol not finalized

---

### GET `/api/practitioner/protocol/{protocol_id}/preview-pdf`

Generate and stream a PDF preview for any protocol (draft or final). Does not save to Cloudinary.

**Response** `200` — `application/pdf` binary stream.

```
Content-Disposition: inline; filename=protocol_36_preview.pdf
```

---

### POST `/api/labs/extract`

Extract structured markers from 1–3 lab report PDFs. Auto-detects lab type (DUTCH, GI-MAP, Bloodwork).

**Request** — `multipart/form-data`:
```
files: <lab_report.pdf>   (repeat for multiple files, max 3)
```

```bash
curl -X POST "http://localhost:8000/api/labs/extract" \
  -F "files=@dutch_report.pdf" \
  -F "files=@gi_map_report.pdf"
```

**Response** `200`:
```json
{
  "job_id": "3f702bba-e86e-4d6b-90e9-8dc2314ebca4",
  "status": "completed",
  "processing_time": "12.43s",
  "extracted_labs": [
    {
      "type": "DUTCH Complete",
      "filename": "dutch_report.pdf",
      "json_file": "3f702bba_dutch_complete.json",
      "markers_count": 22,
      "out_of_range_count": 8,
      "data": {
        "summary": "DUTCH Complete analysis for Female patient, age 34. 22 markers extracted.",
        "reports": [
          {
            "report_type": "DUTCH Complete",
            "report_date": "2024-01-15",
            "key_findings": ["Elevated total estrogen", "Evening cortisol elevation"],
            "abnormal_markers": ["Estrone (E1)", "Total Estrogen", "Cortisol (U3) - Dinner"],
            "results": [
              {
                "test_name": "Estrone (E1)",
                "value": "30.28",
                "unit": "ng/mg",
                "reference_range": "12-26",
                "flag": "Above luteal range"
              }
            ]
          }
        ],
        "markers": [
          {
            "test_name": "Estrone (E1)",
            "value": "30.28",
            "unit": "ng/mg",
            "reference_range": "12-26",
            "flag": "Above luteal range",
            "flag_normalized": "H",
            "is_out_of_range": true,
            "what_we_found": "Estrone is elevated at 30.28 ng/mg, above the luteal range of 12-26.",
            "why_this_matters": "Elevated estrone contributes to estrogen dominance and can worsen PCOS symptoms.",
            "symptoms": "mood swings, weight gain, breast tenderness, irregular cycles"
          }
        ]
      }
    }
  ]
}
```

**`flag_normalized` values:** `H` (high/above range), `L` (low/below range), `N` (normal/within range)

---

## Architecture

### Core Modules
- `json_parser.py` - Maps questionnaire JSON (camelCase or INTAKE_SCHEMA) to internal intake format
- `html_pdf_generator.py` - Renders Jinja2 HTML templates → PDF via Playwright
- `schema.py` - Data structure definitions (`LabResult`, `LabData`, `LabReport`)

### AI Modules
- `lab_analyzer.py` - Batch GPT analysis of all lab markers in 1 API call
- `lab_report_generator.py` - GPT generates EndoAxis-style lab interpretation JSON
- `knowledge_base.py` - GPT generates nutrition, supplement, lifestyle, what-to-expect, goals
- `gemini_lab_extractor.py` - Routes lab PDFs to correct Gemini extractor, returns `LabData`
- `gemini_extractors/` - DUTCH, GI-MAP, Bloodwork specific Gemini extractors

### Utilities
- `error_handler.py` - Error handling & logging
- `cloudinary_helper.py` - PDF upload to Cloudinary

---

## Database Schema

**Protocol table** (`PostgreSQL`):

| Column | Type | Description |
|--------|------|-------------|
| `id` | integer | Primary key |
| `status` | enum | `draft`, `pending_approval`, `final` |
| `protocol` | jsonb | `{protocol_json, lab_report_json, template_type}` |
| `clientId` | integer | FK to client |
| `createdById` | integer | FK to practitioner |
| `pdf_url` | text | Cloudinary URL for protocol PDF |
| `lab_report_pdf_url` | text | Cloudinary URL for lab report PDF |
| `createdAt` | timestamp | Creation time |

---

## Tech Stack

- Python 3.10+
- OpenAI GPT-4o-mini
- Google Gemini 2.5 Flash (lab extraction)
- FastAPI (REST API)
- PostgreSQL/Neon (database)
- Cloudinary (PDF storage)
- Playwright + Chromium (HTML → PDF)
- Jinja2 (HTML templating)
- python-dotenv (environment management)

---

## Status

✅ 2-PDF generation (Protocol + Lab Interpretation Report)  
✅ Admin approval flow (`pending_approval` → `final`)  
✅ Batch lab marker analysis (1 API call for all markers)  
✅ Full protocol JSON saved to PostgreSQL  
✅ PDFs uploaded to Cloudinary on approval  
✅ Lab extraction endpoint with enriched marker output  
✅ Auto-detect lab type (DUTCH, GI-MAP, Bloodwork)  
✅ Questionnaire accepts both INTAKE_SCHEMA and camelCase flat format  
✅ Comprehensive error handling and logging  
