# Be Balanced AI — Implementation Summary

## What Was Built

A FastAPI backend that takes client health questionnaires and lab reports, runs them through a multi-step AI pipeline, and produces two personalized PDFs — a full health protocol and a lab interpretation report. Approved protocols are stored in ChromaDB per client so clients can chat with their own data.

---

## Phase 1 — Lab Extraction Format Fix

**Problem**: DUTCH and GI-MAP extractors returned inconsistent, flat marker structures that lost the hierarchical context of the lab report (e.g. which hormone category a marker belonged to).

**What changed**:
- `dutch_extraction.py` — Refactored to iterate sections as `(category, type, biomarkers)` tuples. Returns 3 values: `parsed_data`, `lab_results`, `structured_results`
- `gi_map.py` — All GI-MAP sections mapped to `category/type/title` format
- `gemini_lab_extractor.py` — Both `extract_dutch()` and `extract_gi_map()` updated to unpack 3-value returns and pass `structured_results` into `LabReport`
- `schema.py` — Added `structured_results: Optional[List[dict]] = None` to `LabReport`
- `lab_extraction.py` — Added `build_report_results()` helper: returns `structured_results` for DUTCH/GI-MAP, flat format for bloodwork

**Result**: DUTCH and GI-MAP return `category/type/title/result/reference/flag`. Bloodwork unchanged with `test_name/value/unit/reference_range/flag`.

---

## Phase 2 — PDF Questionnaire Input

**Problem**: The only way to generate a protocol was to send a pre-structured JSON questionnaire. Practitioners needed to upload a PDF questionnaire directly.

**What changed**:
- `json_parser.py` — Added `parse_questionnaire_pdf(pdf_path)`: uses Gemini structured extraction with a Pydantic schema matching INTAKE_SCHEMA fields, returns normalized `intake_data` dict
- `practitioner.py` — Added `POST /api/practitioner/generate-protocol-from-pdf` endpoint accepting `multipart/form-data` with `questionnaire_pdf` + optional `lab_report_pdfs` (max 3). Shares `_build_protocol_json()` core logic with the JSON endpoint

**Key decision**: Two separate endpoints (JSON vs PDF) sharing the same `_build_protocol_json()` core — not one combined endpoint.

---

## Phase 3 — Dynamic Knowledge Libraries via ChromaDB

**Problem**: Knowledge libraries (nutrition, supplement, lifestyle) were static `.md` files baked into the repo. Admins had no way to update them without a code deploy.

**What changed**:
- `library_vectordb.py` (new) — ChromaDB CRUD for `knowledge_library` collection. Functions: `index_library()`, `delete_library()`, `query_library()`, `list_libraries()`. Uses OpenAI `text-embedding-3-small`. Persistent storage at `vectordb/library_db/`
- `library_loader.py` — Rewritten to query ChromaDB first via `_query_chromadb()`, falls back to static `.md` files if ChromaDB is empty
- `library.py` — Rewritten with 3 new endpoints placed **before** the wildcard `GET /{filename}` route to avoid FastAPI routing conflicts

**New endpoints**:
| Endpoint | Purpose |
|---|---|
| `POST /api/library/upload-library` | Upload `.md` file → chunk → embed → store in ChromaDB |
| `GET /api/library/chromadb-libraries` | List all stored libraries |
| `DELETE /api/library/delete-library/{library_id}` | Remove library from ChromaDB |

**Key decision**: `library_type` and `library_id` passed as query params (not form fields) to avoid `multipart/form-data` parsing conflicts.

**Libraries uploaded and tested**:
- `nutrition_library` → 19 chunks
- `supplement_library` → 25 chunks
- `lifestyle_library` → 23 chunks

---

## Phase 4 — Client RAG Chat

**Problem**: `client_context.py` saved `protocol_json` as a raw JSON string to a `.md` file, and `client_vectordb.py` chunked by markdown `##` headers — but the data was JSON, not markdown. Chunking produced garbage.

**What changed**:

**`client_context.py`**:
- `protocol_path` changed from `protocol.md` → `protocol.json`
- `save_protocol()` accepts both dict and JSON string, normalizes to dict, saves as formatted JSON
- `load_protocol()` returns `dict` instead of `str`
- Removed dead `parse_sections()` method (was markdown-based, no longer relevant)

**`client_vectordb.py`**:
- Added `import json`
- `index_protocol()` now accepts dict or JSON string
- `_chunk_protocol()` rewritten: iterates top-level JSON keys, one chunk per key (e.g. `active_supplements`, `goals`, `concerns`). Each chunk: `"key: <json value>"`

**`practitioner.py`**:
- `approve_protocol()` passes `protocol_json` dict directly to `context.save_protocol()` (was `json.dumps(protocol_json)`)
- Fixed `sync_playwright` crash in async endpoint: PDF generation now runs via `loop.run_in_executor()` in both `approve_protocol()` and `preview_pdf()`

**Database**:
- Added missing `lab_report_pdf_url TEXT` column to `Protocol` table

**On every `approve-protocol` call**:
1. Protocol PDF generated (in thread executor) → uploaded to Cloudinary
2. Lab report PDF generated (if labs present) → uploaded to Cloudinary
3. `protocol.json` + `metadata.json` saved to `data/client_protocols/{client_id}/`
4. Protocol JSON chunked by key → embedded → indexed into ChromaDB `client_{client_id}` collection
5. DB updated: `status = final`, `pdf_url`, `lab_report_pdf_url`

**Client chat** (`POST /api/client/chat`):
- Query embedded → top-3 relevant chunks retrieved from `client_{client_id}` ChromaDB collection
- GPT-4o-mini generates response strictly grounded in retrieved chunks
- Response includes `sources` (which JSON keys were used)

---

## ChromaDB Layout

```
vectordb/
├── library_db/          ← knowledge_library collection
│   └── chroma.sqlite3       Admin-uploaded nutrition/supplement/lifestyle libraries
└── client_db/           ← client_{id} collections
    └── chroma.sqlite3       Per-client protocol chunks (one collection per client)
```

Both databases are separate `PersistentClient` instances pointing to different directories.

---

## File Change Index

| File | Change |
|---|---|
| `src/core/schema.py` | Added `structured_results` field to `LabReport` |
| `src/ai/gemini_extractors/dutch_extraction.py` | Returns 3 values with structured category/type format |
| `src/ai/gemini_lab_extractor.py` | Unpacks 3-value DUTCH return; GI-MAP fully rewritten with section mapping |
| `src/api/routes/lab_extraction.py` | Added `build_report_results()` helper |
| `src/core/json_parser.py` | Added `parse_questionnaire_pdf()` using Gemini |
| `src/api/routes/practitioner.py` | Added PDF endpoint; fixed Playwright async; fixed `json.dumps` bug |
| `src/ai/library_vectordb.py` | **New** — ChromaDB CRUD for knowledge libraries |
| `src/ai/library_loader.py` | Rewritten — ChromaDB first, static file fallback |
| `src/api/routes/library.py` | Rewritten — new ChromaDB endpoints before wildcard route |
| `src/ai/client_context.py` | Saves/loads `protocol.json` (dict); removed `parse_sections()` |
| `src/ai/client_vectordb.py` | JSON-aware chunking by top-level key; accepts dict input |
| `src/ai/client_chat.py` | No changes needed (compatible with updated context/vectordb) |
| PostgreSQL `Protocol` table | Added `lab_report_pdf_url TEXT` column |

---

## Key Technical Decisions

| Decision | Reason |
|---|---|
| Two separate generate endpoints (JSON + PDF) | Cleaner separation; both share `_build_protocol_json()` core |
| ChromaDB for libraries, not templates | Templates stay in PostgreSQL + S3; libraries are semantic content suited for RAG |
| `library_type`/`library_id` as query params | Avoids `multipart/form-data` field parsing conflicts with file upload |
| Specific routes before wildcard in FastAPI | FastAPI matches routes in declaration order; wildcard `GET /{filename}` would swallow specific routes if declared first |
| JSON key chunking for client protocols | Protocol is structured JSON, not prose — chunking by key preserves semantic meaning per section |
| `run_in_executor` for Playwright | `sync_playwright` cannot run inside an asyncio event loop; thread executor bridges sync/async |
| Separate ChromaDB instances for libraries vs clients | Prevents collection name collisions; allows independent scaling and cleanup |
