"""
JSON Parser - Parse questionnaire JSON and map to INTAKE_SCHEMA format
"""
import json
from typing import Dict, Any
from utils.error_handler import DataMappingError, logger


def parse_nested_json_string(json_string: str) -> Dict[str, Any]:
    """Parse nested JSON string (e.g., threeDayFoodLog, threeDayMacros)"""
    try:
        if not json_string or json_string.strip() == "":
            return {}
        return json.loads(json_string)
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse nested JSON: {e}")
        return {}


def parse_three_day_food_log(food_log_str: str) -> Dict[str, Dict[str, str]]:
    """Parse threeDayFoodLog nested JSON string"""
    parsed = parse_nested_json_string(food_log_str)
    
    result = {
        "day_1": {"breakfast": "", "snack": "", "lunch": "", "snack_2": "", "dinner": ""},
        "day_2": {"breakfast": "", "snack": "", "lunch": "", "snack_2": "", "dinner": ""},
        "day_3": {"breakfast": "", "snack": "", "lunch": "", "snack_2": "", "dinner": ""}
    }
    
    for key, value in parsed.items():
        parts = key.split("|||")
        if len(parts) == 2:
            meal_type = parts[0].strip().lower().replace(" ", "_")
            day = parts[1].strip().lower().replace(" ", "_")
            
            if day in result and meal_type in result[day]:
                result[day][meal_type] = value
    
    return result


def parse_three_day_macros(macros_str: str) -> Dict[str, Dict[str, str]]:
    """Parse threeDayMacros nested JSON string"""
    parsed = parse_nested_json_string(macros_str)
    
    result = {
        "day_1": {"protein": "", "fat": "", "carbohydrates": "", "calories": ""},
        "day_2": {"protein": "", "fat": "", "carbohydrates": "", "calories": ""},
        "day_3": {"protein": "", "fat": "", "carbohydrates": "", "calories": ""}
    }
    
    for key, value in parsed.items():
        parts = key.split("|||")
        if len(parts) == 2:
            day = parts[0].strip().lower().replace(" ", "_")
            macro_type = parts[1].strip().lower()
            
            if day in result:
                if "protein" in macro_type:
                    result[day]["protein"] = value
                elif "fat" in macro_type:
                    result[day]["fat"] = value
                elif "carb" in macro_type:
                    result[day]["carbohydrates"] = value
                elif "calor" in macro_type:
                    result[day]["calories"] = value
    
    return result


def map_questionnaire_to_intake_schema(questionnaire: Dict[str, Any]) -> Dict[str, Any]:
    """Map questionnaire JSON to INTAKE_SCHEMA format"""
    
    answers = questionnaire.get("answers", {})
    
    # Handle flat structure (direct fields) or nested structure
    if not answers:
        answers = questionnaire

    # If answers is already in INTAKE_SCHEMA format (has personal_info sub-dict), use it directly
    if "personal_info" in answers:
        logger.info("Detected INTAKE_SCHEMA format — using directly")
        pi = answers.get("personal_info", {})
        if not answers.get("client_name"):
            answers["client_name"] = f"{pi.get('legal_first_name', '')} {pi.get('last_name', '')}".strip() or "Client"
        if "main_symptoms" not in answers:
            answers["main_symptoms"] = answers.get("health_info", {}).get("main_symptoms_ordered", [])
        return answers
    
    # Parse nested JSON strings if they exist
    food_log_raw = answers.get("threeDayFoodLog", "")
    macros_raw = answers.get("threeDayMacros", "")
    
    # If already dict, use directly; otherwise parse as JSON string
    if isinstance(food_log_raw, dict):
        food_log = answers.get("typical_meals", food_log_raw)
    else:
        food_log = parse_three_day_food_log(food_log_raw)
    
    if isinstance(macros_raw, dict):
        macros = answers.get("macros", macros_raw)
    else:
        macros = parse_three_day_macros(macros_raw)
    
    # Extract client name
    client_name = f"{answers.get('legalFirstName', answers.get('legal_first_name', ''))} {answers.get('lastName', answers.get('last_name', ''))}".strip()
    if not client_name:
        client_name = "Client"
    
    # Map to INTAKE_SCHEMA structure
    intake_data = {
        "client_name": client_name,
        "personal_info": {
            "legal_first_name": answers.get("legalFirstName", answers.get("legal_first_name", "")),
            "last_name": answers.get("lastName", answers.get("last_name", "")),
            "street": answers.get("street", ""),
            "unit": answers.get("unit", ""),
            "city": answers.get("city", ""),
            "state_province": answers.get("stateProvince", answers.get("state_province", "")),
            "postal_code": answers.get("postalCode", answers.get("postal_code", "")),
            "home_phone": answers.get("homePhone", answers.get("home_phone", "")),
            "mobile_phone": answers.get("mobilePhone", answers.get("mobile_phone", "")),
            "email": answers.get("email", ""),
            "date_of_birth": answers.get("dateOfBirth", answers.get("date_of_birth", "")),
            "gender": answers.get("gender", ""),
            "relationship_status": answers.get("relationshipStatus", answers.get("relationship_status", "")),
            "occupation": answers.get("occupation", ""),
            "hours_per_week": answers.get("hoursPerWeek", answers.get("hours_per_week", "")),
            "current_weight": answers.get("currentWeight", answers.get("current_weight", "")),
            "height": answers.get("height", "")
        },
        "health_info": answers.get("health_info", {}),
        "diet_history": {
            "chronic_dieting_history": answers.get("eatingDisorderHistory", ""),
            "typical_meals": food_log,
            "macros": macros
        },
        "nutrition_preferences": answers.get("nutrition_preferences", {}),
        "fitness": answers.get("fitness", {}),
        "digestive_health": answers.get("digestive_health", {}),
        "lifestyle": answers.get("lifestyle", {}),
        "medical_history": answers.get("medical_history", {}),
        "personal_care": answers.get("personal_care", {}),
        "supplement_preferences": answers.get("supplement_preferences", {}),
        "goals": answers.get("goals", {}),
        "main_symptoms": answers.get("health_info", {}).get("main_symptoms_ordered", [])
    }
    
    logger.info(f"Mapped questionnaire JSON to INTAKE_SCHEMA format")
    return intake_data


def parse_questionnaire_json(questionnaire_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main function to parse questionnaire JSON and return INTAKE_SCHEMA format
    
    Args:
        questionnaire_json: Raw questionnaire JSON with nested 'answers' object
        
    Returns:
        Dict in INTAKE_SCHEMA format
    """
    try:
        if not questionnaire_json:
            raise DataMappingError("Questionnaire JSON is empty")
        
        if "answers" not in questionnaire_json:
            raise DataMappingError("Questionnaire JSON missing 'answers' object")
        
        logger.info("Parsing questionnaire JSON...")
        intake_data = map_questionnaire_to_intake_schema(questionnaire_json)
        
        logger.info("Successfully parsed questionnaire JSON")
        return intake_data
        
    except Exception as e:
        logger.error(f"Failed to parse questionnaire JSON: {e}")
        raise DataMappingError(f"Questionnaire parsing failed: {e}")
