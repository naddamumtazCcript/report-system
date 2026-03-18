"""
JSON Schema for intake questionnaire data extraction and lab reports
"""
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class LabResult:
    """Single lab test result"""
    test_name: str
    value: str
    unit: str
    reference_range: str
    flag: str
    summary: Optional[str] = None
    what_we_found: Optional[str] = None
    why_this_matters: Optional[str] = None
    symptoms: Optional[str] = None

@dataclass
class LabReport:
    """Parsed lab report data"""
    report_date: str
    report_type: str  # e.g., "DUTCH Complete", "Blood Panel"
    results: List[LabResult]
    key_findings: List[str]
    abnormal_markers: List[str]
    structured_results: Optional[List[dict]] = None  # category/type/title format for DUTCH & GI-MAP

@dataclass
class LabData:
    """Container for all lab reports"""
    reports: List[LabReport]
    summary: str

INTAKE_SCHEMA = {
    "personal_info": {
        "legal_first_name": "",
        "last_name": "",
        "street": "",
        "unit": "",
        "city": "",
        "state_province": "",
        "postal_code": "",
        "home_phone": "",
        "mobile_phone": "",
        "email": "",
        "date_of_birth": "",
        "gender": "",
        "relationship_status": "",
        "occupation": "",
        "hours_per_week": "",
        "current_weight": "",
        "height": ""
    },
    "health_info": {
        "official_diagnoses": "",
        "health_history": "",
        "main_symptoms_ordered": [],
        "short_term_goals": "",
        "long_term_goals": "",
        "current_supplements": "",
        "prescription_medications": "",
        "allergies": "",
        "previous_healing_methods": ""
    },
    "diet_history": {
        "chronic_dieting_history": "",
        "typical_meals": {
            "day_1": {"breakfast": "", "snack": "", "lunch": "", "snack_2": "", "dinner": ""},
            "day_2": {"breakfast": "", "snack": "", "lunch": "", "snack_2": "", "dinner": ""},
            "day_3": {"breakfast": "", "snack": "", "lunch": "", "snack_2": "", "dinner": ""}
        },
        "macros": {
            "day_1": {"protein": "", "fat": "", "carbohydrates": "", "calories": ""},
            "day_2": {"protein": "", "fat": "", "carbohydrates": "", "calories": ""},
            "day_3": {"protein": "", "fat": "", "carbohydrates": "", "calories": ""}
        }
    },
    "nutrition_preferences": {
        "nutrition_support_type": "",
        "nutritional_support_preference": "",
        "nutrition_struggles": "",
        "recipe_preference": "",
        "wants_macro_breakdowns": "",
        "foods_to_avoid": ""
    },
    "fitness": {
        "weekly_workout_description": "",
        "workout_limitations": ""
    },
    "digestive_health": {
        "digestive_symptoms": "",
        "bowel_movement_frequency": "",
        "bowel_movement_type": "",
        "menstrual_cycle_description": ""
    },
    "lifestyle": {
        "energy_levels": "",
        "sleep_quality": "",
        "birth_control_history": "",
        "mental_health_issues": "",
        "therapy_status": "",
        "eating_disorder_history": "",
        "alcohol_frequency": "",
        "additional_symptoms": "",
        "typical_day": "",
        "daily_routine_struggles": ""
    },
    "medical_history": {
        "previous_practitioner_experience": "",
        "high_blood_pressure": "",
        "currently_on_hormonal_birth_control": "",
        "mold_exposure": "",
        "long_term_antibiotic_use": "",
        "family_estrogen_cancer_history": "",
        "other_family_health_history": ""
    },
    "personal_care": {
        "skincare_haircare_products": "",
        "hair_coloring_frequency": "",
        "heat_styling_frequency": "",
        "on_fertility_journey": ""
    },
    "supplement_preferences": {
        "supplement_preference": ""
    },
    "goals": {
        "wellness_journey_excitement": ""
    }
}
