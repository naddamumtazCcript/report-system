"""
Pattern Detector - Identifies client patterns to determine which libraries to load
"""

def detect_patterns(client_data):
    """Detect patterns from client data to determine which library sections to load"""
    patterns = {
        'pcos': False,
        'bloating': False,
        'fatigue': False,
        'stress': False,
        'hormone_issues': False,
        'digestive_issues': False,
        'has_labs': False
    }
    
    # Check diagnoses
    diagnoses = client_data.get('health_info', {}).get('official_diagnoses', '').lower()
    if 'pcos' in diagnoses:
        patterns['pcos'] = True
    
    # Check symptoms
    symptoms = client_data.get('health_info', {}).get('main_symptoms_ordered', [])
    symptoms_text = ' '.join([s.lower() for s in symptoms])
    
    if 'bloat' in symptoms_text or 'digestive' in symptoms_text or 'gas' in symptoms_text:
        patterns['bloating'] = True
        patterns['digestive_issues'] = True
    
    if 'fatigue' in symptoms_text or 'tired' in symptoms_text or 'energy' in symptoms_text:
        patterns['fatigue'] = True
    
    if 'stress' in symptoms_text or 'anxiety' in symptoms_text:
        patterns['stress'] = True
    
    # Check digestive health
    digestive_symptoms = client_data.get('digestive_health', {}).get('digestive_symptoms', '').lower()
    if digestive_symptoms and digestive_symptoms != 'not reported':
        patterns['digestive_issues'] = True
    
    # Check for hormone-related symptoms
    cycle_desc = client_data.get('digestive_health', {}).get('menstrual_cycle_description', '').lower()
    if 'irregular' in cycle_desc or 'heavy' in cycle_desc or 'painful' in cycle_desc:
        patterns['hormone_issues'] = True
    
    return patterns

def get_required_libraries(patterns):
    """Determine which library files to load based on detected patterns"""
    libraries = {
        'nutrition': True,  # Always load
        'lifestyle': True,  # Always load
        'supplement': False,
        'lab': False
    }
    
    # Load supplement library if any health issues detected
    if patterns['pcos'] or patterns['bloating'] or patterns['fatigue'] or patterns['hormone_issues']:
        libraries['supplement'] = True
    
    # Load lab library if labs are present (future enhancement)
    if patterns['has_labs']:
        libraries['lab'] = True
    
    return libraries
