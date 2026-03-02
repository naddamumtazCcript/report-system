"""
API Configuration
"""
from pathlib import Path
import os

# Get project root (parent of src directory)
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Directories
UPLOAD_DIR = PROJECT_ROOT / "data" / "uploads"
OUTPUT_DIR = PROJECT_ROOT / "data" / "output"
KB_DIR = PROJECT_ROOT / "knowledge_base" / "libraries"
LAB_DIR = PROJECT_ROOT / "data" / "lab_reports" / "extracted"
CLIENT_PROTOCOLS_DIR = PROJECT_ROOT / "data" / "client_protocols"

# Create directories
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
KB_DIR.mkdir(parents=True, exist_ok=True)
LAB_DIR.mkdir(parents=True, exist_ok=True)
CLIENT_PROTOCOLS_DIR.mkdir(parents=True, exist_ok=True)

# API Settings
API_TITLE = "Be Balanced Protocol API"
API_VERSION = "1.0.0"
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# System files that cannot be deleted
SYSTEM_FILES = [
    'BeBalancedNutritionLibrary',
    'BeBalancedSupplementLibrary',
    'BeBalancedLifestyleLibrary',
    'BeBalancedLabLibrary',
    'NutritionPlan'
]
