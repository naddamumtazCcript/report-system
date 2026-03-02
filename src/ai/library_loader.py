"""
Library Loader - Loads relevant library files based on detected patterns
"""
import os

LIBRARY_PATH = "../knowledge_base/libraries"

def load_library_content(library_name):
    """Load content from a library file"""
    library_files = {
        'nutrition': 'BeBalancedNutritionLibrary.md',
        'supplement': 'BeBalancedSupplementLibrary.md',
        'lifestyle': 'BeBalancedLifestyleLibrary.md',
        'lab': 'BeBalancedLabLibrary.md',
        'nutrition_plan': 'NutritionPlan.md'
    }
    
    if library_name not in library_files:
        return ""
    
    file_path = os.path.join(os.path.dirname(__file__), LIBRARY_PATH, library_files[library_name])
    
    try:
        with open(file_path, 'r') as f:
            return f.read()
    except FileNotFoundError:
        return ""

def get_library_context(libraries_needed, patterns):
    """Get combined library context for AI based on what's needed"""
    context = "# KNOWLEDGE BASE RULES\n\n"
    
    # Always include nutrition plan for food lists
    context += "## NUTRITION PLAN & FOOD LISTS\n\n"
    context += load_library_content('nutrition_plan')
    context += "\n\n---\n\n"
    
    if libraries_needed.get('nutrition'):
        context += "## NUTRITION LIBRARY RULES\n\n"
        nutrition_content = load_library_content('nutrition')
        
        # Filter to relevant sections based on patterns
        if patterns.get('pcos'):
            context += "**Focus: PCOS/Blood Sugar Pattern Detected**\n\n"
        if patterns.get('bloating') or patterns.get('digestive_issues'):
            context += "**Focus: Digestive/Bloating Pattern Detected**\n\n"
        
        context += nutrition_content
        context += "\n\n---\n\n"
    
    if libraries_needed.get('supplement'):
        context += "## SUPPLEMENT LIBRARY RULES\n\n"
        context += load_library_content('supplement')
        context += "\n\n---\n\n"
    
    if libraries_needed.get('lifestyle'):
        context += "## LIFESTYLE & FITNESS LIBRARY RULES\n\n"
        lifestyle_content = load_library_content('lifestyle')
        
        # Filter to relevant sections
        if patterns.get('pcos'):
            context += "**Focus: PCOS/Metabolic Support Needed**\n\n"
        if patterns.get('stress') or patterns.get('fatigue'):
            context += "**Focus: Stress/Fatigue Pattern Detected**\n\n"
        
        context += lifestyle_content
        context += "\n\n---\n\n"
    
    if libraries_needed.get('lab'):
        context += "## LAB INTERPRETATION LIBRARY\n\n"
        context += load_library_content('lab')
        context += "\n\n---\n\n"
    
    return context
