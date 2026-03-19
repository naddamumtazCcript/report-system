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
- `practitioner.py` — Added PDF questionnaire parsing path; detects `content_type` to route to `parse_questionnaire_json()` or `parse_questionnaire_pdf()`

---

## Merged Generate Endpoint

**Problem**: Two separate endpoints (`/generate-protocol` JSON and `/generate-protocol-from-pdf`) duplicated routing logic and required the frontend to call different URLs.

**What changed**:
- `practitioner.py` — Merged into single `POST /api/practitioner/generate-protocol` accepting `multipart/form-data`
- Questionnaire field accepts PDF or JSON file — detected via `content_type`
- `lab_reports` accepts PDF or JSON files (max 3), also auto-detected
- `libraries` (JSON file) is **required** — FastAPI returns 422 if missing
- `template` (JSON file) is **optional** — falls back to `templates/protocol_template.json`
- `_build_protocol_json(intake_data, lab_markers, client_name, template, libraries_json)` reads template section titles and only calls the AI functions needed for sections present in the template — skips GPT calls for absent sections
- `get_library_context_from_json(libraries_json)` builds the library context string directly from the provided dict — AI functions never query ChromaDB during protocol generation

**Key decisions**:
- Libraries are required per-request (not pulled from ChromaDB at generation time) — practitioner controls exactly which library content is used
- Template controls which AI functions are called — no wasted GPT calls for unused sections
- ChromaDB is still used for: admin library management (`/api/library/*`) and client RAG chat (`client_{id}` collections)

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

## Hardening & ClientAgent Fixes

### JSON Parsing — `knowledge_base.py`

**Problem**: Every AI function stripped ` ```json ` fences manually and silently returned `{}` or `[]` on parse failure. No indication of which section failed — protocol silently had empty sections with no log output.

**What changed**:
- Added `_parse_json_response(raw, fn_name, fallback)` helper at module level
- Strips both ` ```json ` and plain ` ``` ` fences, attempts `json.loads()`, logs `[fn_name] JSON parse failed: <error> Raw output: <first 500 chars>` on failure, returns typed fallback (`{}` or `[]`)
- All 6 AI functions (`analyze_symptom_drivers`, `generate_lifestyle_recommendations`, `generate_supplement_recommendations`, `generate_nutrition_recommendations`, `generate_what_to_expect`, `generate_goals_action_plan`) now use the helper

### Temp File Cleanup — `practitioner.py`

**Problem**: Questionnaire PDFs, lab PDFs, protocol PDFs, and lab report PDFs were written to disk but never deleted. Slow disk leak over time.

**What changed**: All 4 file write sites wrapped in `try/finally` with `Path.unlink(missing_ok=True)` — files are deleted even if the AI call, PDF generation, or Cloudinary upload throws.

### Protocol Chunk Granularity — `client_vectordb.py`

**Problem**: `_chunk_protocol()` created one chunk per top-level JSON key with no size limit. Large list keys like `active_supplements` (4 objects) or `goals` (3 objects) produced a single oversized chunk — embedding was a blurry average, retrieval precision degraded.

**What changed**:
- Lists → one chunk per item: `active_supplements[0]`, `active_supplements[1]`, etc.
- Dicts → one chunk per sub-key: `titration_schedule.week_1`, `titration_schedule.week_2`, etc.
- Long strings → split by sentence at 500 char boundary
- Short strings → single chunk unchanged
- Result: a 18-key protocol now produces ~31-43 chunks instead of 18, each with a precise embedding
- Added `get_by_section(client_id, section)` — fetches all chunks for a given section key by ChromaDB metadata filter

### Conversation History Cap — `client_chat.py`

**Problem**: Full `conversation_history` was passed to GPT every turn with no trimming. Long sessions would hit token limits.

**What changed**: `conversation_history[-10:]` — only last 10 messages (5 turns) passed to GPT.

### ClientAgent RAG Search — `client_chat.py`

**Problem 1 — Stale history in search query**: Search query was built from the last 4 history messages. After a multi-turn supplement conversation, asking "What should I eat for breakfast?" pulled supplement chunks instead of `core_habits` — GPT fired the guardrail on a valid protocol question.

**Problem 2 — Incomplete list retrieval**: `n_results=4` sometimes returned only 2 of 3 goal chunks, the 3rd slot taken by an irrelevant chunk. GPT answered with incomplete goals.

**Problem 3 — Overly broad topic guardrail**: System prompt rule 2 said "if the question is NOT related to health, nutrition, or wellness" — GPT pattern-matched question topics instead of checking whether the retrieved chunks contained an answer.

**What changed**:
- Search query now uses only the immediately prior user message (1 turn back) — topic switches retrieve the correct section
- Added `_expand_list_sections(sections)` in `ClientChat` — when any chunk from a multi-chunk section is retrieved, all remaining chunks from that section are fetched via `get_by_section()` and added to context before GPT sees it
- Guardrail rewritten: rule 2 now says deflect only when retrieved chunks genuinely don’t contain the answer; rule 3 handles truly off-topic questions (movies, sports, etc.)
- Sources deduped: `list(dict.fromkeys(...))` so `['active_supplements', 'active_supplements', 'active_supplements']` becomes `['active_supplements']`

**Tested results** (7-turn live conversation, real GPT + ChromaDB):

| Question | Before | After |
|---|---|---|
| "What supplements am I taking?" | 3 of 4 listed | All 4 listed |
| "When do I start Ashwagandha?" | Correct | Correct |
| "And what is it for?" (pronoun) | Correct | Correct |
| "What should I eat for breakfast?" | Guardrail fired (false positive) | Answered from `core_habits` |
| "Why am I tired?" | Correct | Correct |
| "What are my goals?" | 2 of 3 goals | All 3 goals |
| "Recommend a Netflix show" | Guardrail fired | Guardrail fired |

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
| `src/api/routes/practitioner.py` | Merged into single `multipart/form-data` endpoint; template-aware AI call gating; all 4 temp file sites wrapped in `try/finally` cleanup |
| `src/ai/knowledge_base.py` | All 3 AI functions accept `library_context=None`; shared `_parse_json_response()` helper replaces 6 manual strip+parse blocks |
| `src/ai/library_loader.py` | Added `get_library_context_from_json()` — builds context string from provided dict |
| `src/ai/library_vectordb.py` | **New** — ChromaDB CRUD for knowledge libraries |
| `src/api/routes/library.py` | Rewritten — new ChromaDB endpoints before wildcard route |
| `src/ai/client_context.py` | Saves/loads `protocol.json` (dict); removed `parse_sections()` |
| `src/ai/client_vectordb.py` | Granular chunking (list → per item, dict → per sub-key, long string → by sentence); added `get_by_section()` |
| `src/ai/client_chat.py` | 1-turn history search query; `_expand_list_sections()` for complete list retrieval; rewritten guardrail; history capped at 10; sources deduped |
| PostgreSQL `Protocol` table | Added `lab_report_pdf_url TEXT` column |

---

## Key Technical Decisions

| Decision | Reason |
|---|---|
| Single merged generate endpoint (multipart/form-data) | One URL handles all combinations (PDF/JSON questionnaire × PDF/JSON/none labs); content_type detection keeps routing clean |
| Libraries required per-request (not ChromaDB at generation time) | Practitioner controls exactly which library content is injected; no stale ChromaDB reads during generation |
| Template controls which AI functions are called | Skips GPT calls for sections not in template — no wasted tokens |
| ChromaDB for libraries, not templates | Templates stay in PostgreSQL + S3; libraries are semantic content suited for RAG |
| `library_type`/`library_id` as query params | Avoids `multipart/form-data` field parsing conflicts with file upload |
| Specific routes before wildcard in FastAPI | FastAPI matches routes in declaration order; wildcard `GET /{filename}` would swallow specific routes if declared first |
| JSON key chunking for client protocols | Protocol is structured JSON, not prose — chunking by key preserves semantic meaning per section |
| `run_in_executor` for Playwright | `sync_playwright` cannot run inside an asyncio event loop; thread executor bridges sync/async |
| Separate ChromaDB instances for libraries vs clients | Prevents collection name collisions; allows independent scaling and cleanup |
