"""
Knowledge Base V2 - JSON-based libraries
"""
import json
from openai import OpenAI
import os
from dotenv import load_dotenv
from utils.token_tracker import TokenTracker

load_dotenv()

token_tracker = TokenTracker()

def get_library_context_from_json(libraries_json, patterns=None):
    """Convert library JSON objects to formatted string for AI context"""
    context = "# KNOWLEDGE BASE\n\n"
    
    for library_name, library_data in libraries_json.items():
        context += f"## {library_name.upper()} LIBRARY\n\n"
        context += json.dumps(library_data, indent=2)
        context += "\n\n---\n\n"
    
    return context

def analyze_symptom_drivers(client_data):
    """Analyze symptoms and suggest root cause drivers"""
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
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
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

def generate_nutrition_recommendations_json(client_data, libraries_json, lab_data=None):
    """Generate nutrition recommendations using JSON libraries"""
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        return {}
    
    client = OpenAI(api_key=api_key)
    library_context = get_library_context_from_json(libraries_json)
    
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
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
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

def generate_supplement_recommendations_json(client_data, libraries_json, lab_data=None):
    """Generate supplement recommendations using JSON libraries"""
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        return {}
    
    client = OpenAI(api_key=api_key)
    library_context = get_library_context_from_json(libraries_json)
    
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
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
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

def generate_lifestyle_recommendations_json(client_data, libraries_json):
    """Generate lifestyle recommendations using JSON libraries"""
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        return {}
    
    client = OpenAI(api_key=api_key)
    library_context = get_library_context_from_json(libraries_json)
    
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
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
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
