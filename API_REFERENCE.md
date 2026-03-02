# Generate Protocol API

## Workflow

```
Step 1: Select Patient → patient_id
Step 2: Click Template Button → template_type
Step 3: Upload Intake PDF → intake_file
Step 4: Upload Lab PDFs → lab_files (optional)
Step 5: Select Libraries → selected_libraries
        ↓
[Click "Start Mapping"]
        ↓
POST /api/generate-protocol
        ↓
Protocol Generated (20-30s)
```

---

## GET `/api/templates`

Get available template options.

### Response

```json
{
  "templates": [
    {
      "type": "standard_protocol",
      "metadata": {
        "name": "Standard Protocol",
        "processing_time": "~20s"
      }
    },
    {
      "type": "deep_analysis",
      "metadata": {
        "name": "Deep Analysis",
        "processing_time": "~30s"
      }
    },
    {
      "type": "quick_scan",
      "metadata": {
        "name": "Quick Scan",
        "processing_time": "~10s"
      }
    }
  ]
}
```

---

## GET `/api/library/list`

Get available libraries for selection.

### Response

```json
{
  "libraries": [
    {
      "name": "BeBalancedNutritionLibrary",
      "filename": "BeBalancedNutritionLibrary.md",
      "type": "markdown"
    },
    {
      "name": "BeBalancedSupplementLibrary",
      "filename": "BeBalancedSupplementLibrary.md",
      "type": "markdown"
    },
    {
      "name": "BeBalancedLifestyleLibrary",
      "filename": "BeBalancedLifestyleLibrary.md",
      "type": "markdown"
    },
    {
      "name": "BeBalancedLabLibrary",
      "filename": "BeBalancedLabLibrary.md",
      "type": "markdown"
    },
    {
      "name": "NutritionPlan",
      "filename": "NutritionPlan.md",
      "type": "markdown"
    }
  ]
}
```

---

## POST `/api/generate-protocol`
### Request Body

**Content-Type:** `multipart/form-data`

```
patient_id: "patient_001"
template_type: "standard_protocol"
intake_file: <PDF file>
selected_libraries: ["BeBalancedNutritionLibrary", "BeBalancedSupplementLibrary", "BeBalancedLifestyleLibrary"]
lab_files: <PDF file> (optional)
```

**Template Types:**
- `standard_protocol`
- `deep_analysis`
- `quick_scan`

**Available Libraries:**
- `BeBalancedNutritionLibrary`
- `BeBalancedSupplementLibrary`
- `BeBalancedLifestyleLibrary`
- `BeBalancedLabLibrary`
- `NutritionPlan`

### Response Body

**Success:**
```json
{
  "status": "success",
  "job_id": "abc123",
  "output": {
    "client_name": "Jessica Martinez",
    "protocol_content": "# Full protocol markdown...",
    "download_url": "/api/download/abc123"
  },
  "metadata": {
    "processing_time": "22.3s",
    "lab_reports_processed": 2
  }
}
```

**Error:**
```json
{
  "detail": "Error message"
}
```

---

## Example

```bash
curl -X POST "http://localhost:8000/api/generate-protocol" \
  -F "patient_id=patient_001" \
  -F "template_type=standard_protocol" \
  -F "intake_file=@intake.pdf" \
  -F "selected_libraries=[\"BeBalancedNutritionLibrary\",\"BeBalancedSupplementLibrary\"]"
```

---

## Test

```bash
# Start server
cd src && python -m uvicorn api.app:app --reload

# Open Swagger UI
open http://localhost:8000/docs
```
