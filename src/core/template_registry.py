"""
Template Registry - Manages available clinical templates
"""
from pathlib import Path
from enum import Enum

class TemplateType(str, Enum):
    """Available clinical template types"""
    STANDARD_PROTOCOL = "standard_protocol"
    DEEP_ANALYSIS = "deep_analysis"
    QUICK_SCAN = "quick_scan"

# Template metadata
TEMPLATE_METADATA = {
    TemplateType.STANDARD_PROTOCOL: {
        "name": "Standard Protocol",
        "description": "Comprehensive 12-week health protocol with nutrition, supplements, and lifestyle recommendations",
        "file": "ProtocolTemplate.md",
        "requires_labs": False,
        "processing_time": "~20s",
        "sections": ["General", "Nutrition", "Lifestyle", "Supplements"]
    },
    TemplateType.DEEP_ANALYSIS: {
        "name": "Deep Analysis",
        "description": "In-depth analysis with advanced pattern detection and root cause investigation",
        "file": "DeepAnalysisTemplate.md",
        "requires_labs": True,
        "processing_time": "~30s",
        "sections": ["Comprehensive Assessment", "Root Cause Analysis", "Advanced Recommendations"]
    },
    TemplateType.QUICK_SCAN: {
        "name": "Quick Scan",
        "description": "Rapid assessment with immediate action items and priority recommendations",
        "file": "QuickScanTemplate.md",
        "requires_labs": False,
        "processing_time": "~10s",
        "sections": ["Quick Assessment", "Priority Actions", "Next Steps"]
    }
}

def get_template_path(template_type: str) -> Path:
    """Get template file path for given template type"""
    if template_type not in TemplateType.__members__.values():
        raise ValueError(f"Invalid template type: {template_type}. Must be one of: {list(TemplateType.__members__.values())}")
    
    template_file = TEMPLATE_METADATA[template_type]["file"]
    template_path = Path(__file__).parent.parent.parent / "templates" / template_file
    
    if not template_path.exists():
        raise FileNotFoundError(f"Template file not found: {template_path}")
    
    return template_path

def get_template_metadata(template_type: str) -> dict:
    """Get metadata for given template type"""
    if template_type not in TemplateType.__members__.values():
        raise ValueError(f"Invalid template type: {template_type}")
    
    return TEMPLATE_METADATA[template_type]

def list_available_templates() -> list:
    """List all available templates with metadata"""
    return [
        {
            "type": template_type,
            "metadata": metadata
        }
        for template_type, metadata in TEMPLATE_METADATA.items()
    ]

def validate_template_type(template_type: str) -> bool:
    """Validate if template type is supported"""
    return template_type in TemplateType.__members__.values()
