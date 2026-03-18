"""
Library Loader - Loads relevant library context based on detected patterns.
Queries ChromaDB first; falls back to static files if ChromaDB is empty.
"""
import os

LIBRARY_PATH = "../knowledge_base/libraries"

STATIC_LIBRARY_FILES = {
    'nutrition': 'BeBalancedNutritionLibrary.md',
    'supplement': 'BeBalancedSupplementLibrary.md',
    'lifestyle': 'BeBalancedLifestyleLibrary.md',
    'lab': 'BeBalancedLabLibrary.md',
    'nutrition_plan': 'NutritionPlan.md'
}


def _load_static(library_name: str) -> str:
    """Load content from a static library file."""
    filename = STATIC_LIBRARY_FILES.get(library_name, '')
    if not filename:
        return ""
    file_path = os.path.join(os.path.dirname(__file__), LIBRARY_PATH, filename)
    try:
        with open(file_path, 'r') as f:
            return f.read()
    except FileNotFoundError:
        return ""


def _query_chromadb(query: str, library_types: list, n_results: int = 8) -> str:
    """Query ChromaDB for relevant chunks. Returns empty string if ChromaDB is empty."""
    try:
        from ai.library_vectordb import query_library
        results = query_library(query, library_types=library_types, n_results=n_results)
        if not results:
            return ""
        return "\n\n".join(r['text'] for r in results)
    except Exception:
        return ""


def get_library_context(libraries_needed: dict, patterns: dict) -> str:
    """
    Get combined library context for AI prompts.
    Uses ChromaDB if available, otherwise falls back to static files.
    """
    # Build a query string from detected patterns for semantic search
    pattern_labels = [k for k, v in patterns.items() if v]
    query = f"health protocol recommendations for: {', '.join(pattern_labels)}" if pattern_labels else "general health protocol"

    needed_types = [k for k, v in libraries_needed.items() if v]

    # Try ChromaDB first
    chromadb_context = _query_chromadb(query, needed_types)

    if chromadb_context:
        context = "# KNOWLEDGE BASE RULES\n\n"
        if patterns.get('pcos'):
            context += "**Focus: PCOS/Blood Sugar Pattern Detected**\n\n"
        if patterns.get('bloating') or patterns.get('digestive_issues'):
            context += "**Focus: Digestive/Bloating Pattern Detected**\n\n"
        if patterns.get('stress') or patterns.get('fatigue'):
            context += "**Focus: Stress/Fatigue Pattern Detected**\n\n"
        context += chromadb_context
        return context

    # Fallback to static files
    context = "# KNOWLEDGE BASE RULES\n\n"
    context += "## NUTRITION PLAN & FOOD LISTS\n\n"
    context += _load_static('nutrition_plan')
    context += "\n\n---\n\n"

    if libraries_needed.get('nutrition'):
        context += "## NUTRITION LIBRARY RULES\n\n"
        if patterns.get('pcos'):
            context += "**Focus: PCOS/Blood Sugar Pattern Detected**\n\n"
        if patterns.get('bloating') or patterns.get('digestive_issues'):
            context += "**Focus: Digestive/Bloating Pattern Detected**\n\n"
        context += _load_static('nutrition')
        context += "\n\n---\n\n"

    if libraries_needed.get('supplement'):
        context += "## SUPPLEMENT LIBRARY RULES\n\n"
        context += _load_static('supplement')
        context += "\n\n---\n\n"

    if libraries_needed.get('lifestyle'):
        context += "## LIFESTYLE & FITNESS LIBRARY RULES\n\n"
        if patterns.get('pcos'):
            context += "**Focus: PCOS/Metabolic Support Needed**\n\n"
        if patterns.get('stress') or patterns.get('fatigue'):
            context += "**Focus: Stress/Fatigue Pattern Detected**\n\n"
        context += _load_static('lifestyle')
        context += "\n\n---\n\n"

    if libraries_needed.get('lab'):
        context += "## LAB INTERPRETATION LIBRARY\n\n"
        context += _load_static('lab')
        context += "\n\n---\n\n"

    return context
