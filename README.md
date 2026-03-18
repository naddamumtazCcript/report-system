# Be Balanced AI - Practitioner Agent

AI-powered system that automates creation of personalized health protocols from client intake questionnaires and lab reports.

## Overview

Converts client-filled questionnaires and lab reports into two personalized documents:
- **PDF 1 — Full Protocol**: Nutrition, lifestyle, supplement plan
- **PDF 2 — Lab Interpretation Report**: EndoAxis-style narrative report (only when labs are attached)

Both documents are generated as JSON + PDF, stored in PostgreSQL and Cloudinary, and require admin approval before delivery. Approved protocols are automatically indexed in ChromaDB per client, enabling RAG-based client chat.

## Features

- **2-PDF Generation** — Protocol PDF + Lab Interpretation Report per run
- **AI Data Mapping** — GPT-4o-mini maps questionnaire JSON to structured intake data
- **PDF Questionnaire Parsing** — Gemini extracts structured intake data from questionnaire PDFs
- **Lab Extraction** — Gemini 2.5 Flash extracts structured markers from DUTCH, GI-MAP, Bloodwork PDFs
- **Batch Lab Analysis** — All markers analyzed in a single GPT call (what we found, why it matters, symptoms)
- **Smart Recommendations** — GPT generates nutrition, supplement, lifestyle, what-to-expect, and goals plans
- **Admin Approval Flow** — Protocols require admin approval before PDFs are generated and delivered
- **Dynamic Knowledge Libraries** — Admin uploads `.md` knowledge libraries to ChromaDB; RAG queries replace static files
- **Client RAG Chat** — Approved protocols indexed in ChromaDB per client; clients chat with their own protocol
- **Cloud Storage** — PDFs stored on Cloudinary CDN
- **PostgreSQL Storage** — Protocol JSON saved to DB with full lifecycle tracking
- **Error Handling** — Production-ready error handling and logging

## Project Structure

```
report-system/
├── src/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── practitioner.py      # Protocol generation & approval endpoints
│   │   │   ├── lab_extraction.py    # Standalone lab extraction endpoint
│   │   │   ├── client.py            # Client chat endpoints
│   │   │   ├── library.py           # Knowledge library management endpoints
│   │   │   ├── generate.py          # Legacy generate endpoints
│   │   │   ├── upload.py            # File upload endpoints
│   │   │   └── pdf_to_json.py       # PDF to JSON converter
│   │   ├── app.py                   # FastAPI app entry point
│   │   └── config.py                # Path and directory config
│   ├── ai/
│   │   ├── gemini_extractors/
│   │   │   ├── dutch_extraction.py  # DUTCH Complete extractor
│   │   │   ├── gi_map.py            # GI-MAP extractor
│   │   │   └── functional_bloodwork.py  # Bloodwork extractor
│   │   ├── gemini_lab_extractor.py  # Routes PDFs to correct extractor
│   │   ├── lab_analyzer.py          # Batch GPT marker analysis
│   │   ├── lab_report_generator.py  # GPT lab interpretation JSON
│   │   ├── knowledge_base.py        # GPT protocol recommendations
│   │   ├── library_vectordb.py      # ChromaDB CRUD for knowledge libraries
│   │   ├── library_loader.py        # Queries ChromaDB, falls back to static files
│   │   ├── client_chat.py           # RAG chat engine with guardrails
│   │   ├── client_context.py        # Saves/loads client protocol JSON
│   │   └── client_vectordb.py       # ChromaDB CRUD for client protocols
│   ├── core/
│   │   ├── json_parser.py           # Questionnaire JSON + PDF → intake_data
│   │   ├── html_pdf_generator.py    # Jinja2 HTML → PDF via Playwright
│   │   ├── schema.py                # LabResult, LabData, LabReport dataclasses
│   │   └── data_mapper.py           # Field mapping utilities
│   ├── db/
│   │   └── database.py              # psycopg2 connection helper
│   └── utils/
│       ├── cloudinary_helper.py     # PDF upload to Cloudinary
│       └── error_handler.py         # Logging setup
├── templates/
│   ├── template.html                # Protocol PDF HTML template
│   └── lab_report_template.html     # Lab interpretation PDF HTML template
├── knowledge_base/                  # Static fallback knowledge libraries (.md)
├── vectordb/
│   ├── library_db/                  # ChromaDB: knowledge_library collection
│   └── client_db/                   # ChromaDB: client_{id} collections
├── data/
│   ├── client_protocols/            # Per-client protocol.json + metadata.json
│   ├── uploads/                     # Temp uploaded files
│   └── output/                      # Generated JSONs and PDFs
└── output/                          # Legacy output directory
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
generate-protocol ──────────────────────────────► pending_approval
generate-protocol-from-pdf ─────────────────────►      │
                                                        │
                                                  approve-protocol
                                                        │
                                                        ▼
                                                      final
                                                   (PDFs generated,
                                                    client ChromaDB
                                                    indexed)
                                                        │
                                                  reopen-protocol
                                                        │
                                                        ▼
                                                      draft
                                                        │
                                                  submit-for-approval
                                                        │
                                                        ▼
                                                  pending_approval
```

---

### POST `/api/practitioner/generate-protocol`

Generate a protocol from a JSON questionnaire + optional lab results. Saves to DB with `pending_approval` status.

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
        }
      ]
    }
  ]
}
```

**Notes:**
- `questionnaire.answers` accepts INTAKE_SCHEMA format (nested `personal_info`, `health_info`, etc.) or flat camelCase (`legalFirstName`, `lastName`, etc.)
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

### POST `/api/practitioner/generate-protocol-from-pdf`

Generate a protocol from a PDF questionnaire + optional lab report PDFs. Questionnaire is parsed via Gemini.

**Request** — `multipart/form-data`:
```
user_id: 3
client_id: 4
template_type: standard
questionnaire_pdf: <questionnaire.pdf>
lab_report_pdfs: <lab.pdf>   (optional, repeat for multiple, max 3)
```

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

Admin approves a `pending_approval` protocol. Generates both PDFs, uploads to Cloudinary, indexes protocol in client ChromaDB, sets status to `final`.

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

**Side effects on approval:**
- Protocol PDF generated and uploaded to Cloudinary
- Lab report PDF generated and uploaded (if labs present)
- `protocol.json` saved to `data/client_protocols/{client_id}/`
- Protocol JSON chunked by key and indexed into ChromaDB `client_{client_id}` collection

---

### POST `/api/practitioner/submit-for-approval/{protocol_id}`

Re-submit a `draft` protocol for admin approval.

**Response** `200`:
```json
{ "protocol_id": 36, "status": "pending_approval" }
```

---

### POST `/api/practitioner/reopen-protocol/{protocol_id}`

Reopen a `final` protocol for editing. Clears `pdf_url`, sets status to `draft`.

**Response** `200`:
```json
{ "protocol_id": 36, "status": "draft" }
```

---

### PUT `/api/practitioner/edit-protocol/{protocol_id}`

Edit the `protocol_json` of a `draft` protocol. Request body is the full replacement `protocol_json` object.

**Response** `200`:
```json
{ "protocol_id": 36, "status": "draft" }
```

---

### GET `/api/practitioner/protocol/{protocol_id}`

Fetch the full protocol record by ID. Returns `protocol_json`, `lab_report_json`, status, and metadata.

---

### GET `/api/practitioner/protocol/{protocol_id}/pdf`

Redirect to the Cloudinary PDF URL. Only works for `final` protocols.

**Response** `302` — redirect to Cloudinary URL.

---

### GET `/api/practitioner/protocol/{protocol_id}/preview-pdf`

Generate and stream a PDF preview for any protocol (draft or final). Does not save to Cloudinary.

**Response** `200` — `application/pdf` binary stream.

---

### POST `/api/labs/extract`

Extract structured markers from 1–3 lab report PDFs. Auto-detects lab type (DUTCH, GI-MAP, Bloodwork).

**Request** — `multipart/form-data`:
```bash
curl -X POST "http://localhost:8000/api/labs/extract" \
  -F "files=@dutch_report.pdf" \
  -F "files=@gi_map_report.pdf"
```

**Response** `200` — DUTCH/GI-MAP return `category/type/title/result/reference/flag` structure. Bloodwork returns `test_name/value/unit/reference_range/flag`.

---

### POST `/api/library/upload-library?library_type=nutrition&library_id=nutrition_library`

Upload a `.md` knowledge library file to ChromaDB. Replaces existing library with same `library_id`.

**Request** — `multipart/form-data`: `file: <library.md>`

**Response** `200`:
```json
{ "library_id": "nutrition_library", "library_type": "nutrition", "chunks_stored": 19 }
```

---

### GET `/api/library/chromadb-libraries`

List all knowledge libraries currently stored in ChromaDB.

**Response** `200`:
```json
[
  { "library_id": "nutrition_library", "library_type": "nutrition" },
  { "library_id": "supplement_library", "library_type": "supplement" }
]
```

---

### DELETE `/api/library/delete-library/{library_id}`

Delete a knowledge library from ChromaDB by ID.

---

### POST `/api/client/initialize`

Manually initialize a client's protocol for chat (auto-called on approval).

**Request body**:
```json
{
  "client_id": "4",
  "protocol_content": "{...protocol json string...}",
  "metadata": { "name": "Sarah Mitchell" }
}
```

---

### POST `/api/client/chat`

Chat with a client about their approved protocol. Answers are strictly grounded in the protocol via RAG.

**Request body**:
```json
{
  "client_id": "4",
  "message": "What supplements am I taking?",
  "conversation_history": []
}
```

**Response** `200`:
```json
{
  "response": "You are taking Magnesium Glycinate and Myo-Inositol...",
  "sources": ["active_supplements", "titration_schedule"]
}
```

---

## Architecture

### Core Modules
- `json_parser.py` — Maps questionnaire JSON (camelCase or INTAKE_SCHEMA) to internal intake format. Also parses questionnaire PDFs via Gemini
- `html_pdf_generator.py` — Renders Jinja2 HTML templates → PDF via Playwright (runs in thread executor inside async endpoints)
- `schema.py` — Data structure definitions (`LabResult`, `LabData`, `LabReport`)

### AI Modules
- `lab_analyzer.py` — Batch GPT analysis of all lab markers in 1 API call
- `lab_report_generator.py` — GPT generates EndoAxis-style lab interpretation JSON
- `knowledge_base.py` — GPT generates nutrition, supplement, lifestyle, what-to-expect, goals
- `library_vectordb.py` — ChromaDB CRUD for `knowledge_library` collection (admin-uploaded libraries)
- `library_loader.py` — Queries ChromaDB first, falls back to static `.md` files if ChromaDB empty
- `gemini_lab_extractor.py` — Routes lab PDFs to correct Gemini extractor, returns `LabData`
- `gemini_extractors/` — DUTCH, GI-MAP, Bloodwork specific Gemini extractors
- `client_chat.py` — RAG chat engine; retrieves relevant protocol chunks, generates GPT response with strict guardrails
- `client_context.py` — Saves/loads client `protocol.json` and `metadata.json` to disk
- `client_vectordb.py` — ChromaDB CRUD for `client_{client_id}` collections; chunks protocol by JSON key

### Utilities
- `error_handler.py` — Error handling & logging
- `cloudinary_helper.py` — PDF upload to Cloudinary

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

## ChromaDB Collections

| Collection | Managed by | Purpose |
|---|---|---|
| `knowledge_library` | `library_vectordb.py` | Admin-uploaded nutrition/supplement/lifestyle libraries |
| `client_{client_id}` | `client_vectordb.py` | Per-client protocol chunks for RAG chat |

Both collections live in the same ChromaDB instance but are fully separate.

---

## Tech Stack

- Python 3.10+
- OpenAI GPT-4o-mini
- Google Gemini 2.5 Flash (lab + questionnaire PDF extraction)
- FastAPI (REST API)
- PostgreSQL/Neon (database)
- ChromaDB 0.5.23 (vector store — libraries + client protocols)
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
✅ Lab extraction endpoint — DUTCH/GI-MAP structured format, Bloodwork flat format
✅ Auto-detect lab type (DUTCH, GI-MAP, Bloodwork)
✅ Questionnaire accepts both INTAKE_SCHEMA and camelCase flat format
✅ PDF questionnaire parsing via Gemini (`generate-protocol-from-pdf`)
✅ Dynamic knowledge libraries via ChromaDB (upload/list/delete)
✅ RAG-based knowledge retrieval during protocol generation (falls back to static files)
✅ Client RAG chat — approved protocols indexed in ChromaDB per client
✅ Comprehensive error handling and logging
