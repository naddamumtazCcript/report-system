"""
Template Populator - Fills protocol template with extracted client data
"""
import json
from datetime import datetime
from ai.knowledge_base import (get_nutrition_recommendations, analyze_symptom_drivers, 
                            generate_nutrition_recommendations, generate_supplement_recommendations,
                            generate_lifestyle_recommendations)
from utils.error_handler import TemplatePopulationError, logger

def load_template(template_path):
    """Load protocol template"""
    try:
        with open(template_path, 'r') as f:
            content = f.read()
        logger.info(f"Template loaded: {template_path}")
        return content
    except FileNotFoundError:
        raise TemplatePopulationError(f"Template file not found: {template_path}")
    except Exception as e:
        raise TemplatePopulationError(f"Failed to load template: {e}")

def load_data(json_path):
    """Load extracted client data"""
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
        logger.info(f"Client data loaded: {json_path}")
        return data
    except FileNotFoundError:
        raise TemplatePopulationError(f"Data file not found: {json_path}")
    except json.JSONDecodeError as e:
        raise TemplatePopulationError(f"Invalid JSON in data file: {e}")
    except Exception as e:
        raise TemplatePopulationError(f"Failed to load data: {e}")

def get_value(data, *keys, default="Not reported"):
    """Safely get nested value from dict"""
    value = data
    for key in keys:
        if isinstance(value, dict):
            value = value.get(key, default)
        else:
            return default
    return value if value else default

def populate_template(template, data, lab_data=None):
    """Populate template with client data and lab results"""
    # Client name and date
    client_name = f"{get_value(data, 'personal_info', 'legal_first_name')} {get_value(data, 'personal_info', 'last_name')}".strip()
    template = template.replace("{Client Name}", client_name or "Not reported")
    template = template.replace("{Date}", datetime.now().strftime("%B %d, %Y"))
    
    # Lab Review Summary - populate if lab data available
    if lab_data and lab_data.reports:
        lab_section = "## **LAB REVIEW SUMMARY**\n\n"
        
        for report in lab_data.reports:
            lab_section += f"**Report:** {report.report_type} ({report.report_date})\n\n"
            
            # Show abnormal markers
            abnormal_results = [r for r in report.results if r.flag.lower() in ['high', 'low', 'out of range', 'above range', 'below range']]
            
            for i, result in enumerate(abnormal_results[:5], 1):
                lab_section += f"### **Marker {i}**\n\n"
                lab_section += f"* Marker Name: {result.test_name}\n"
                lab_section += f"* Status: {result.flag}\n"
                lab_section += f"* What We Found: {result.value} {result.unit} (Reference: {result.reference_range})\n"
                lab_section += f"* Why This Matters: To be discussed with practitioner\n"
                lab_section += f"* Symptoms This Can Contribute To: To be assessed\n\n"
            
            if len(abnormal_results) > 5:
                lab_section += f"*({len(abnormal_results) - 5} additional markers to review)*\n\n"
        
        template = template.replace(
            "## **LAB REVIEW SUMMARY**\n\n### **Marker 1**\n\n* Marker Name:  \n* Status (Low / Normal / High):  \n* What We Found:  \n* Why This Matters:  \n* Symptoms This Can Contribute To:\n\n### **Marker 2**\n\n* Marker Name:  \n* Status:  \n* What We Found:  \n* Why This Matters:  \n* Symptoms This Can Contribute To:\n\n### **Marker 3**\n\n* Marker Name:  \n* Status:  \n* Pattern (if applicable):  \n* Why This Matters:\n\n*(Repeat as needed)*",
            lab_section.strip()
        )
    else:
        # No lab data - remove section
        template = template.replace(
            "## **LAB REVIEW SUMMARY**\n\n### **Marker 1**\n\n* Marker Name:  \n* Status (Low / Normal / High):  \n* What We Found:  \n* Why This Matters:  \n* Symptoms This Can Contribute To:\n\n### **Marker 2**\n\n* Marker Name:  \n* Status:  \n* What We Found:  \n* Why This Matters:  \n* Symptoms This Can Contribute To:\n\n### **Marker 3**\n\n* Marker Name:  \n* Status:  \n* Pattern (if applicable):  \n* Why This Matters:\n\n*(Repeat as needed)*",
            "## **LAB REVIEW SUMMARY**\n\nNo lab reports provided.\n"
        )
    
    # Top Concerns (from symptoms)
    symptoms = get_value(data, 'health_info', 'main_symptoms_ordered', default=[])
    
    # Get AI-powered driver analysis
    driver_analysis = analyze_symptom_drivers(data)
    drivers_map = {}
    if driver_analysis and 'symptom_drivers' in driver_analysis:
        # Group drivers by symptom (handle multiple drivers per symptom)
        for item in driver_analysis['symptom_drivers']:
            symptom_key = item['symptom'].lower().strip()
            if symptom_key not in drivers_map:
                drivers_map[symptom_key] = []
            drivers_map[symptom_key].append(item['drivers'])
    
    if isinstance(symptoms, list):
        for i in range(5):
            concern_num = i + 1
            if i < len(symptoms):
                symptom = symptoms[i]
                # Try to find matching drivers (fuzzy match on first part)
                symptom_key = symptom.lower().split('-')[0].strip()
                matching_drivers = []
                for key, drivers in drivers_map.items():
                    if symptom_key in key or key in symptom_key:
                        matching_drivers.extend(drivers)
                
                if matching_drivers:
                    driver = " ".join(matching_drivers[:2])  # Use first 2 drivers
                else:
                    driver = "To be determined based on further assessment"
                
                template = template.replace(
                    f"**Concern {concern_num}:**\n\n* Description:  \n* Likely Driver(s):",
                    f"**Concern {concern_num}:**\n\n* Description: {symptom}\n* Likely Driver(s): {driver}"
                )
    
    # Nutrition Focus
    short_goals = get_value(data, 'health_info', 'short_term_goals')
    template = template.replace("**Primary Nutrition Goal:**", f"**Primary Nutrition Goal:** {short_goals}")
    
    # Macro Recommendations
    nutrition_recs = get_nutrition_recommendations(data)
    bmr = nutrition_recs['bmr']
    dee = nutrition_recs['dee']
    macros = nutrition_recs['macros']
    
    template = template.replace("**Program Length:**", f"**Program Length:** 12 weeks")
    template = template.replace("* Calories:  ", f"* Calories: {macros['calories']}")
    template = template.replace("* Protein:  ", f"* Protein: {macros['protein_g']}g")
    template = template.replace("* Carbohydrates:  ", f"* Carbohydrates: {macros['carbs_g']}g")
    template = template.replace("* Fat:  ", f"* Fat: {macros['fat_g']}g")
    template = template.replace("* Fiber:", f"* Fiber: {macros['fiber_g']}g")
    
    # Add BMR/DEE note
    template = template.replace("**Hydration Target:**", f"**Hydration Target:** Half body weight in ounces (aim for ~80oz daily)\n\n**Metabolic Calculations:**\n* BMR (Basal Metabolic Rate): {bmr} calories\n* DEE (Daily Energy Expenditure): {dee} calories")
    
    # Get AI-powered nutrition recommendations (with lab data)
    nutrition_recs_ai = generate_nutrition_recommendations(data, lab_data)
    
    # Core Habits
    if nutrition_recs_ai and 'core_habits' in nutrition_recs_ai:
        habits = nutrition_recs_ai['core_habits']
        for i in range(4):
            if i < len(habits):
                template = template.replace(f"{i+1}.   ", f"{i+1}. {habits[i]}")
    
    # Why This Helps
    if nutrition_recs_ai and 'why_this_helps' in nutrition_recs_ai:
        template = template.replace(
            "**Why This Nutrition Strategy Helps:**",
            f"**Why This Nutrition Strategy Helps:** {nutrition_recs_ai['why_this_helps']}"
        )
    
    # Focus Items
    if nutrition_recs_ai and 'focus_items' in nutrition_recs_ai:
        focus_items = nutrition_recs_ai['focus_items']
        focus_section = "## **FOCUS  ITEMS**\n\n"
        for item in focus_items[:5]:
            focus_section += f"* {item}\n"
        template = template.replace(
            "## **FOCUS  ITEMS**\n\n*   \n*   \n*   \n*   \n* ",
            focus_section.strip()
        )
    
    # Food Recommendations
    if nutrition_recs_ai and 'foods_to_focus' in nutrition_recs_ai:
        foods = nutrition_recs_ai['foods_to_focus']
        food_section = "## **PLATE & FOOD RECOMMENDATIONS**\n\n"
        food_section += "### **Foods to Focus On**\n\n"
        food_section += f"**Protein:** {', '.join(foods.get('protein', [])[:10])}\n\n"
        food_section += f"**Carbohydrates:** {', '.join(foods.get('carbohydrates', [])[:10])}\n\n"
        food_section += f"**Healthy Fats:** {', '.join(foods.get('fats', [])[:10])}\n\n"
        food_section += f"**Fiber Sources:** {', '.join(foods.get('fiber', [])[:10])}\n\n"
        
        if 'foods_to_limit' in nutrition_recs_ai and nutrition_recs_ai['foods_to_limit']:
            food_section += f"**Foods to Limit (This Phase):** {', '.join(nutrition_recs_ai['foods_to_limit'][:5])}"
        
        template = template.replace(
            "## **PLATE & FOOD RECOMMENDATIONS** ",
            food_section
        )
    
    # Current supplements - replace with AI recommendations (with lab data)
    supplement_recs = generate_supplement_recommendations(data, lab_data)
    
    # Supplements to Pause
    if supplement_recs and 'supplements_to_pause' in supplement_recs:
        pause_list = supplement_recs['supplements_to_pause']
        if pause_list:
            pause_section = "### **Supplements to Pause or Adjust**\n\n"
            for item in pause_list[:3]:
                pause_section += f"* {item}\n"
            template = template.replace(
                "### **Supplements to Pause or Adjust**\n\n*   \n* ",
                pause_section.strip()
            )
    
    # Active Supplements
    if supplement_recs and 'active_supplements' in supplement_recs:
        active_supps = supplement_recs['active_supplements']
        if active_supps:
            supps_section = "### **Active Supplements**\n\n"
            for supp in active_supps[:5]:
                supps_section += f"**Supplement Name:** {supp['name']}\n\n"
                supps_section += f"* Purpose: {supp['purpose']}\n"
                supps_section += f"* Duration: {supp['duration']}\n\n"
            
            template = template.replace(
                "### **Active Supplements**\n\n**Supplement Name:**\n\n* Purpose:  \n* Duration:\n\n**Supplement Name:**\n\n* Purpose:  \n* Duration:\n\n*(Repeat as needed)*",
                supps_section.strip()
            )
    
    # Titration Schedule
    if supplement_recs and 'titration_schedule' in supplement_recs:
        titration = supplement_recs['titration_schedule']
        if titration and any(titration.values()):
            titration_section = "### **SUPPLEMENT TITRATION SCHEDULE (IF APPLICABLE)**\n\n"
            titration_section += f"Week 1: {titration.get('week_1', 'Not specified')}\n"
            titration_section += f"Week 2: {titration.get('week_2', 'Not specified')}\n"
            titration_section += f"Week 3: {titration.get('week_3', 'Not specified')}"
            
            template = template.replace(
                "### **SUPPLEMENT TITRATION SCHEDULE (IF APPLICABLE)**\n\nWeek 1:  \nWeek 2:  \nWeek 3:",
                titration_section
            )
    
    # Lifestyle - AI-powered recommendations
    lifestyle_recs = generate_lifestyle_recommendations(data)
    
    if lifestyle_recs:
        # Daily Steps
        steps_target = lifestyle_recs.get('daily_steps_target', '8,000-10,000 steps')
        template = template.replace("**Daily Steps Target:**", f"**Daily Steps Target:** {steps_target}")
        
        # Strength Training
        if 'strength_training' in lifestyle_recs:
            st = lifestyle_recs['strength_training']
            template = template.replace(
                "**Strength Training:**\n\n* Frequency:  \n* Split:",
                f"**Strength Training:**\n\n* Frequency: {st.get('frequency', 'Not specified')}\n* Split: {st.get('split', 'Not specified')}"
            )
        
        # Stress Support
        if 'stress_support' in lifestyle_recs and lifestyle_recs['stress_support']:
            stress_section = "### **Stress & Nervous System Support**\n\n"
            for practice in lifestyle_recs['stress_support'][:3]:
                stress_section += f"* {practice}\n"
            template = template.replace(
                "### **Stress & Nervous System Support**\n\n*   \n*   \n* ",
                stress_section.strip()
            )
        
        # Avoid or Be Mindful Of
        if 'avoid_or_mindful' in lifestyle_recs and lifestyle_recs['avoid_or_mindful']:
            avoid_text = ", ".join(lifestyle_recs['avoid_or_mindful'][:3])
            template = template.replace("**Avoid or Be Mindful Of:**", f"**Avoid or Be Mindful Of:** {avoid_text}")
    
    # Goals table
    short_term = get_value(data, 'health_info', 'short_term_goals')
    long_term = get_value(data, 'health_info', 'long_term_goals')
    
    template = template.replace(
        "| {Goal 1} | {Summary of related actions}  |  |",
        f"| {short_term} | To be determined based on protocol recommendations |  |"
    )
    template = template.replace(
        "| {Goal 2} | {Summary of related actions}  |  |",
        f"| {long_term} | To be determined based on protocol recommendations |  |"
    )
    template = template.replace(
        "| {Goal 3} | {Summary of related actions}  |  |",
        "| | |  |"
    )
    
    return template

def populate(template_path, json_path, output_path, lab_data=None):
    """Main function to populate template"""
    try:
        logger.info("Starting template population...")
        
        template = load_template(template_path)
        data = load_data(json_path)
        
        logger.info("Populating template with client data...")
        populated = populate_template(template, data, lab_data)
        
        logger.info(f"Writing populated protocol to: {output_path}")
        with open(output_path, 'w') as f:
            f.write(populated)
        
        logger.info(f"Protocol successfully generated: {output_path}")
        return output_path
        
    except TemplatePopulationError:
        raise
    except Exception as e:
        logger.error(f"Template population failed: {e}")
        raise TemplatePopulationError(f"Failed to populate template: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 4:
        print("Usage: python3 template_populator.py <template_file> <json_file> <output_file>")
        sys.exit(1)
    
    template_file = sys.argv[1]
    json_file = sys.argv[2]
    output_file = sys.argv[3]
    
    try:
        result = populate(template_file, json_file, output_file)
        print(f"✓ Protocol generated: {result}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
