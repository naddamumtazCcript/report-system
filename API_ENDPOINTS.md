# API Endpoints

Base URL: `http://localhost:8000/api/practitioner`

---

## 1. Generate Protocol

Creates a new protocol from intake questionnaire and optional lab reports.

**POST** `/generate-protocol`

**Request:**
- Content-Type: `multipart/form-data`

```
questionnaire: File (PDF)
lab_reports: File[] (PDF, optional)
user_id: string
client_id: integer
template_type: string (default: "standard")
doc_types: string (JSON array: ["bloodwork", "gi_map", "dutch"])
libraries: string (JSON array: ["BeBalancedNutritionLibrary"])
```

**Response:** `200 OK`
```json
{
  "protocol_id": 1,
  "status": "draft",
  "markdown": "# Protocol content...",
  "lab_reports_processed": 2
}
```

---

## 2. Get Protocol

Retrieves protocol details by ID.

**GET** `/protocol/{protocol_id}`

**Response:** `200 OK`
```json
{
  "protocol_id": 1,
  "status": "draft",
  "client_id": 3,
  "created_by_id": 3,
  "markdown": "# Protocol content...",
  "intake_data": {...},
  "lab_reports": [...],
  "libraries": [...],
  "template_type": "standard"
}
```

**Error:** `404 Not Found`
```json
{"detail": "Protocol not found"}
```

---

## 3. Edit Protocol

Updates protocol markdown content (draft only).

**PUT** `/edit-protocol/{protocol_id}`

**Request:**
- Content-Type: `application/x-www-form-urlencoded`

```
markdown: string
```

**Response:** `200 OK`
```json
{
  "protocol_id": 1,
  "status": "draft",
  "markdown": "# Updated content..."
}
```

**Error:** `400 Bad Request`
```json
{"detail": "Can only edit draft protocols"}
```

---

## 4. Finalize Protocol

Generates PDF, uploads to Cloudinary, and marks protocol as final.

**POST** `/finalize-protocol/{protocol_id}`

**Response:** `200 OK`
```json
{
  "protocol_id": 1,
  "status": "final",
  "pdf_url": "https://res.cloudinary.com/dasnofv6f/raw/upload/v1773171115/protocols/protocol_1"
}
```

**Error:** `400 Bad Request`
```json
{"detail": "Protocol already finalized"}
```

---

## 5. Download PDF

Redirects to Cloudinary URL for PDF download (final protocols only).

**GET** `/protocol/{protocol_id}/pdf`

**Response:** `307 Temporary Redirect`
- Redirects to Cloudinary URL

**Error:** `400 Bad Request`
```json
{"detail": "Protocol not finalized"}
```

**Error:** `404 Not Found`
```json
{"detail": "PDF not found"}
```

---

## 6. Reopen Protocol

Reverts finalized protocol back to draft status for editing.

**POST** `/reopen-protocol/{protocol_id}`

**Response:** `200 OK`
```json
{
  "protocol_id": 1,
  "status": "draft"
}
```

**Error:** `400 Bad Request`
```json
{"detail": "Can only reopen finalized protocols"}
```

---

## Workflow

```
1. Generate Protocol (draft)
   ↓
2. Edit Protocol (optional)
   ↓
3. Finalize Protocol (uploads PDF to Cloudinary)
   ↓
4. Download PDF (redirects to Cloudinary)
   ↓
5. Reopen Protocol (optional, back to draft)
   ↓
6. Edit & Re-finalize
```

---

## Status Codes

- `200` - Success
- `307` - Redirect (PDF download)
- `400` - Bad Request (invalid operation)
- `404` - Not Found
- `500` - Server Error
