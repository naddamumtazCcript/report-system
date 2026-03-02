# Project Structure - Modular Architecture

## New Directory Structure

```
report-system/
├── src/
│   ├── __init__.py
│   ├── main.py                    # Main pipeline orchestrator
│   │
│   ├── core/                      # Core processing modules
│   │   ├── __init__.py
│   │   ├── pdf_extractor.py       # PDF text extraction
│   │   ├── data_mapper.py         # AI data extraction from text
│   │   ├── template_populator.py  # Template population logic
│   │   └── schema.py              # JSON schema definition
│   │
│   ├── ai/                        # AI/ML modules
│   │   ├── __init__.py
│   │   ├── knowledge_base.py      # AI recommendations engine
│   │   ├── pattern_detector.py    # Client pattern detection
│   │   └── library_loader.py      # Smart library loading
│   │
│   └── utils/                     # Utility modules
│       ├── __init__.py
│       ├── error_handler.py       # Error handling & logging
│       └── token_tracker.py       # OpenAI token tracking
│
├── knowledge_base/
│   └── libraries/                 # Practitioner knowledge libraries
│       ├── BeBalancedNutritionLibrary.md
│       ├── BeBalancedSupplementLibrary.md
│       ├── BeBalancedLifestyleLibrary.md
│       ├── BeBalancedLabLibrary.md
│       └── NutritionPlan.md
│
├── templates/
│   └── ProtocolTemplate.md        # Protocol template
│
├── data/
│   ├── sample_filled_text.txt     # Sample questionnaire
│   ├── extracted_data.json        # Extracted structured data
│   └── output/                    # Generated protocols
│       └── generated_protocol.md
│
├── tests/
│   ├── test_profiles.py           # Test client profiles
│   ├── validate_system.py         # System validation suite
│   ├── test_error_handling.py     # Error handling tests
│   ├── test_with_tokens.py        # Token tracking test
│   ├── VALIDATION_REPORT.md       # Validation results
│   └── ERROR_HANDLING_SUMMARY.md  # Error handling docs
│
├── logs/                          # Daily log files
│   └── report_system_YYYYMMDD.log
│
├── .env                           # Environment variables
├── requirements.txt               # Python dependencies
└── README.md                      # Project documentation
```

## Module Responsibilities

### Core Modules (`src/core/`)

**pdf_extractor.py**
- Extracts text from PDF files
- Validates PDF format and content
- Error handling for corrupted/empty PDFs

**data_mapper.py**
- Uses OpenAI to extract structured JSON from text
- Validates extracted data completeness
- Handles API errors gracefully

**template_populator.py**
- Populates protocol template with client data
- Integrates all AI recommendations
- Generates final protocol document

**schema.py**
- Defines JSON schema for intake data
- Ensures data structure consistency

### AI Modules (`src/ai/`)

**knowledge_base.py**
- BMR/DEE/Macro calculations
- AI-powered symptom analysis
- AI-powered nutrition recommendations
- AI-powered supplement recommendations
- AI-powered lifestyle recommendations
- Token tracking for all AI operations

**pattern_detector.py**
- Detects client patterns (PCOS, bloating, fatigue, stress, etc.)
- Determines which libraries to load
- Pattern-based recommendation routing

**library_loader.py**
- Loads relevant library sections based on patterns
- Filters content to reduce token usage
- Combines library context for AI

### Utility Modules (`src/utils/`)

**error_handler.py**
- Custom exception classes
- Validation functions
- Centralized logging system
- User-friendly error messages

**token_tracker.py**
- Tracks OpenAI API token usage
- Calculates costs per operation
- Generates usage reports

## Benefits of Modular Structure

### 1. Separation of Concerns
- Core processing separate from AI logic
- Utilities isolated for reusability
- Clear module boundaries

### 2. Maintainability
- Easy to locate and update specific functionality
- Changes in one module don't affect others
- Clear import paths

### 3. Testability
- Each module can be tested independently
- Mock dependencies easily
- Isolated unit tests

### 4. Scalability
- Easy to add new AI features in `ai/`
- Easy to add new utilities in `utils/`
- Core processing remains stable

### 5. Readability
- Clear module names indicate purpose
- Logical grouping of related functions
- Easier onboarding for new developers

## Import Patterns

### From main.py
```python
from core.pdf_extractor import PDFExtractor
from core.data_mapper import extract_data
from core.template_populator import populate
from utils.error_handler import ReportSystemError, logger
```

### From template_populator.py
```python
from ai.knowledge_base import (
    get_nutrition_recommendations,
    analyze_symptom_drivers,
    generate_nutrition_recommendations,
    generate_supplement_recommendations,
    generate_lifestyle_recommendations
)
from utils.error_handler import TemplatePopulationError, logger
```

### From knowledge_base.py
```python
from ai.pattern_detector import detect_patterns, get_required_libraries
from ai.library_loader import get_library_context
from utils.token_tracker import TokenTracker
```

## Token Tracking

### Usage
```python
from ai.knowledge_base import print_token_summary, get_token_summary

# After running AI operations
print_token_summary()  # Print to console
summary = get_token_summary()  # Get JSON summary
```

### Output Format
```json
{
  "operations": [
    {
      "operation": "symptom_analysis",
      "prompt_tokens": 170,
      "completion_tokens": 371,
      "total_tokens": 541,
      "cost": 0.000248
    }
  ],
  "total_tokens": 2253,
  "total_cost": 0.000791,
  "timestamp": "2026-02-20T03:15:42.123456"
}
```

## Running Tests

### Full System Validation
```bash
python tests/validate_system.py
```

### Error Handling Tests
```bash
python tests/test_error_handling.py
```

### Token Tracking Test
```bash
python tests/test_with_tokens.py
```

## Migration Notes

All files have been reorganized into the new structure with updated imports. The system maintains 100% backward compatibility with existing functionality while providing better organization and new features (token tracking).
