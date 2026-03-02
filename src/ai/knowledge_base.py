"""
Knowledge Base - Nutrition calculations and AI recommendations with token tracking
"""
import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from ai.pattern_detector import detect_patterns, get_required_libraries
from ai.library_loader import get_library_context
from utils.token_tracker import TokenTracker

load_dotenv()

token_tracker = TokenTracker()

def calculate_bmr(weight_lbs, height_inches, age, gender):
    weight_kg = weight_lbs * 0.453592
    height_cm = height_inches * 2.54
    if gender.lower() in ['female', 'f']:
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) - 161
    else:
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) + 5
    return round(bmr)

def calculate_dee(bmr, activity_level="moderate"):
    multipliers = {"sedentary": 1.2, "light": 1.375, "moderate": 1.55, "active": 1.725, "very_active": 1.9}
    return round(bmr * multipliers.get(activity_level.lower(), 1.55))

def calculate_macros(weight_lbs, dee, goal="maintenance"):
    protein_g = round(weight_lbs * 0.9)
    calories = dee if goal == "maintenance" else round(dee * (0.85 if goal == "fat_loss" else 1.1))
    protein_cal = protein_g * 4
    fat_g = round((calories * 0.28) / 9)
    carb_g = round((calories - protein_cal - (fat_g * 9)) / 4)
    return {"calories": calories, "protein_g": protein_g, "carbs_g": carb_g, "fat_g": fat_g, "fiber_g": 30}

def get_nutrition_recommendations(client_data):
    weight_lbs = int(''.join(filter(str.isdigit, client_data.get('personal_info', {}).get('current_weight', '165'))))
    height_str = client_data.get('personal_info', {}).get('height', "5'6\"")
    feet = int(height_str.split("'")[0]) if "'" in height_str else 5
    inches = int(''.join(filter(str.isdigit, height_str.split("'")[1]))) if "'" in height_str else 6
    height_inches = (feet * 12) + inches
    dob_str = client_data.get('personal_info', {}).get('date_of_birth', '03/15/1985')
    age = 2026 - int(dob_str.split('/')[-1]) if '/' in dob_str else 35
    gender = client_data.get('personal_info', {}).get('gender', 'Female')
    bmr = calculate_bmr(weight_lbs, height_inches, age, gender)
    dee = calculate_dee(bmr, "moderate")
    macros = calculate_macros(weight_lbs, dee, "maintenance")
    return {"bmr": bmr, "dee": dee, "macros": macros}

def analyze_symptom_drivers(client_data):
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        return {}
    client = OpenAI(api_key=api_key)
    symptoms = client_data.get('health_info', {}).get('main_symptoms_ordered', [])
    diagnoses = client_data.get('health_info', {}).get('official_diagnoses', '')
    health_history = client_data.get('health_info', {}).get('health_history', '')
    medications = client_data.get('health_info', {}).get('prescription_medications', '')
    
    prompt = f"""You are a functional health practitioner. Analyze the client's symptoms and suggest likely root cause drivers.

Client Information:
- Diagnoses: {diagnoses}
- Health History: {health_history}
- Current Medications: {medications}

Symptoms:
{chr(10).join([f"{i+1}. {s}" for i, s in enumerate(symptoms)])}

For each symptom, provide 1-2 likely drivers in a concise format. Focus on functional health root causes (hormonal, metabolic, digestive, stress-related).

Return ONLY a JSON object with this structure:
{{
  "symptom_drivers": [
    {{"symptom": "symptom text", "drivers": "likely driver explanation"}}
  ]
}}"""
    
    try:
        response = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}], temperature=0.3)
        token_tracker.track("symptom_analysis", response)
        result = response.choices[0].message.content.strip()
        if result.startswith('```json'):
            result = result[7:]
        if result.endswith('```'):
            result = result[:-3]
        return json.loads(result.strip())
    except Exception as e:
        print(f"Error analyzing symptoms: {e}")
        return {}

def generate_lifestyle_recommendations(client_data):
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        return {}
    client = OpenAI(api_key=api_key)
    patterns = detect_patterns(client_data)
    libraries_needed = get_required_libraries(patterns)
    library_context = get_library_context(libraries_needed, patterns)
    symptoms = client_data.get('health_info', {}).get('main_symptoms_ordered', [])
    diagnoses = client_data.get('health_info', {}).get('official_diagnoses', '')
    current_workout = client_data.get('fitness', {}).get('weekly_workout_description', '')
    limitations = client_data.get('fitness', {}).get('workout_limitations', '')
    
    prompt = f"""{library_context}

---

# CLIENT DATA

**Diagnoses:** {diagnoses}
**Top Symptoms:** {', '.join(symptoms[:5])}
**Current Workout:** {current_workout}
**Limitations:** {limitations}

**Detected Patterns:**
{', '.join([k for k, v in patterns.items() if v])}

---

# YOUR TASK

Using the lifestyle library rules above, generate movement and lifestyle recommendations for this client.

Return ONLY a JSON object with this structure:
{{
  "daily_steps_target": "8,000-10,000 steps",
  "strength_training": {{
    "frequency": "3-4x per week",
    "split": "2 upper / 2 lower"
  }},
  "stress_support": ["practice 1", "practice 2", "practice 3"],
  "avoid_or_mindful": ["thing to avoid 1", "thing to avoid 2"]
}}

Rules:
- Match intensity to client's current capacity
- Prioritize recovery if fatigue/stress is present
- Emphasize strength training for PCOS/metabolic patterns
- Include nervous system support when stress is detected
"""
    
    try:
        response = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}], temperature=0.3)
        token_tracker.track("lifestyle_recommendations", response)
        result = response.choices[0].message.content.strip()
        if result.startswith('```json'):
            result = result[7:]
        if result.endswith('```'):
            result = result[:-3]
        return json.loads(result.strip())
    except Exception as e:
        print(f"Error generating lifestyle recommendations: {e}")
        return {}

def generate_supplement_recommendations(client_data, lab_data=None):
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        return {}
    client = OpenAI(api_key=api_key)
    patterns = detect_patterns(client_data)
    libraries_needed = get_required_libraries(patterns)
    library_context = get_library_context(libraries_needed, patterns)
    symptoms = client_data.get('health_info', {}).get('main_symptoms_ordered', [])
    diagnoses = client_data.get('health_info', {}).get('official_diagnoses', '')
    current_supplements = client_data.get('health_info', {}).get('current_supplements', '')
    medications = client_data.get('health_info', {}).get('prescription_medications', '')
    
    # Add lab context if available
    lab_context = ""
    if lab_data and lab_data.reports:
        lab_context = "\n\n# LAB DATA\n\n"
        for report in lab_data.reports:
            lab_context += f"**{report.report_type}** ({report.report_date}):\n"
            if report.abnormal_markers:
                lab_context += f"Abnormal markers: {', '.join(report.abnormal_markers[:5])}\n"
            for result in report.results[:10]:
                if result.flag.lower() in ['high', 'low', 'out of range', 'above range', 'below range']:
                    lab_context += f"- {result.test_name}: {result.value} {result.unit} ({result.flag})\n"
    
    prompt = f"""{library_context}

---

# CLIENT DATA

**Diagnoses:** {diagnoses}
**Top Symptoms:** {', '.join(symptoms[:5])}
**Current Supplements:** {current_supplements}
**Medications:** {medications}

**Detected Patterns:**
{', '.join([k for k, v in patterns.items() if v])}
{lab_context}
---

# YOUR TASK

Using the supplement library rules above and lab data (if provided), generate supplement recommendations for this client.

Return ONLY a JSON object with this structure:
{{
  "supplements_to_pause": ["supplement name with reason"],
  "active_supplements": [
    {{
      "name": "supplement name",
      "purpose": "why this supplement (reference lab values if relevant)",
      "duration": "time-bound or ongoing"
    }}
  ],
  "titration_schedule": {{
    "week_1": "instructions",
    "week_2": "instructions",
    "week_3": "instructions"
  }}
}}

Rules:
- Maximum 4-5 active supplements
- Every supplement needs clear purpose
- Reference specific lab values when recommending supplements
- Check if current supplements conflict with recommendations
- Use conservative, supportive language
- Include titration if introducing multiple new supplements
"""
    
    try:
        response = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}], temperature=0.3)
        token_tracker.track("supplement_recommendations", response)
        result = response.choices[0].message.content.strip()
        if result.startswith('```json'):
            result = result[7:]
        if result.endswith('```'):
            result = result[:-3]
        return json.loads(result.strip())
    except Exception as e:
        print(f"Error generating supplement recommendations: {e}")
        return {}

def generate_nutrition_recommendations(client_data, lab_data=None):
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        return {}
    client = OpenAI(api_key=api_key)
    patterns = detect_patterns(client_data)
    libraries_needed = get_required_libraries(patterns)
    library_context = get_library_context(libraries_needed, patterns)
    symptoms = client_data.get('health_info', {}).get('main_symptoms_ordered', [])
    diagnoses = client_data.get('health_info', {}).get('official_diagnoses', '')
    goals = client_data.get('health_info', {}).get('short_term_goals', '')
    foods_to_avoid = client_data.get('nutrition_preferences', {}).get('foods_to_avoid', '')
    nutrition_struggles = client_data.get('nutrition_preferences', {}).get('nutrition_struggles', '')
    
    # Add lab context if available
    lab_context = ""
    if lab_data and lab_data.reports:
        lab_context = "\n\n# LAB DATA\n\n"
        for report in lab_data.reports:
            lab_context += f"**{report.report_type}:**\n"
            if report.key_findings:
                lab_context += f"Key findings: {', '.join(report.key_findings[:3])}\n"
    
    prompt = f"""{library_context}

---

# CLIENT DATA

**Diagnoses:** {diagnoses}
**Top Symptoms:** {', '.join(symptoms[:3])}
**Goals:** {goals}
**Foods to Avoid:** {foods_to_avoid}
**Nutrition Struggles:** {nutrition_struggles}
{lab_context}
---

# YOUR TASK

Using the library rules above and lab data (if provided), generate nutrition recommendations for this client.

Return ONLY a JSON object with this structure:
{{
  "core_habits": ["habit 1", "habit 2", "habit 3", "habit 4"],
  "why_this_helps": "1-2 sentence explanation (reference lab findings if relevant)",
  "foods_to_focus": {{
    "protein": ["food1", "food2", ...],
    "carbohydrates": ["food1", "food2", ...],
    "fats": ["food1", "food2", ...],
    "fiber": ["food1", "food2", ...]
  }},
  "foods_to_limit": ["food1", "food2", ...],
  "focus_items": ["focus 1", "focus 2", "focus 3"]
}}

Rules:
- Filter out foods the client wants to avoid
- Keep it simple (10-15 foods per category max)
- Focus items should be 3-5 high-level actions
- Use supportive, non-restrictive language
- Reference lab findings when relevant
"""
    
    try:
        response = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}], temperature=0.3)
        token_tracker.track("nutrition_recommendations", response)
        result = response.choices[0].message.content.strip()
        if result.startswith('```json'):
            result = result[7:]
        if result.endswith('```'):
            result = result[:-3]
        return json.loads(result.strip())
    except Exception as e:
        print(f"Error generating nutrition recommendations: {e}")
        return {}

def get_token_summary():
    return token_tracker.get_summary()

def print_token_summary():
    token_tracker.print_summary()
