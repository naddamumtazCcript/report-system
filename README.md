# Be Balanced AI - Practitioner Agent

AI-powered system that automates creation of personalized health protocols from client intake questionnaires.

## Overview

Converts client-filled PDF questionnaires into complete, personalized health protocols with AI-powered recommendations for nutrition, supplements, and lifestyle.

## Features

- **PDF Text Extraction** - Extracts data from intake questionnaires
- **AI Data Mapping** - Converts unstructured text to structured JSON
- **Pattern Detection** - Identifies client health patterns (PCOS, gut issues, stress, etc.)
- **Smart Recommendations** - AI generates personalized nutrition, supplement, and lifestyle plans
- **Token Tracking** - Monitors OpenAI API usage and costs
- **Error Handling** - Production-ready error handling and logging

## Project Structure

```
report-system/
├── src/
│   ├── core/              # Core processing (PDF, data mapping, templates)
│   ├── ai/                # AI recommendations and pattern detection
│   └── utils/             # Error handling, logging, token tracking
├── knowledge_base/        # Practitioner knowledge libraries
├── templates/             # Protocol template
├── data/                  # Sample data and outputs
└── tests/                 # Test suite and validation
```

## Setup

1. **Install dependencies**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Configure API key**
Create `.env` file:
```
OPENAI_API_KEY=your-api-key-here
```

3. **Run pipeline**
```bash
python src/main.py data/sample_intake.pdf
```

## Usage

### Generate Protocol
```bash
python src/main.py <path-to-pdf>
```

### Run Tests
```bash
# Full validation suite
python tests/validate_system.py

# Token tracking test
python tests/test_with_tokens.py

# Error handling tests
python tests/test_error_handling.py
```

## Cost & Performance

- **Cost per protocol:** $0.000791 (0.08 cents)
- **Token usage:** ~2,253 tokens per protocol
- **Processing time:** ~20 seconds
- **Accuracy:** 100% test pass rate (30/30 tests)

## Token Breakdown

| Operation | Tokens | Cost |
|-----------|--------|------|
| Symptom Analysis | 541 | $0.000248 |
| Nutrition Recommendations | 631 | $0.000207 |
| Supplement Recommendations | 641 | $0.000227 |
| Lifestyle Recommendations | 440 | $0.000109 |
| **Total** | **2,253** | **$0.000791** |

## Architecture

### Core Modules
- `pdf_extractor.py` - PDF text extraction
- `data_mapper.py` - AI-powered data extraction
- `template_populator.py` - Protocol generation
- `schema.py` - Data structure definitions

### AI Modules
- `knowledge_base.py` - AI recommendations engine
- `pattern_detector.py` - Client pattern detection
- `library_loader.py` - Smart library loading

### Utilities
- `error_handler.py` - Error handling & logging
- `token_tracker.py` - OpenAI usage tracking

## Documentation

- `PROJECT_STRUCTURE.md` - Detailed architecture
- `MODULAR_REFACTORING_SUMMARY.md` - Token analysis & optimization
- `ERROR_REFERENCE.md` - Error troubleshooting guide
- `tests/VALIDATION_REPORT.md` - Test results
- `tests/ERROR_HANDLING_SUMMARY.md` - Error handling details

## Tech Stack

- Python 3.10+
- OpenAI GPT-4o-mini
- pdfplumber (PDF extraction)
- python-dotenv (environment management)

## Status

✅ Production-ready  
✅ 100% test coverage  
✅ Comprehensive error handling  
✅ Token tracking & cost monitoring  
✅ 92% under budget estimate
