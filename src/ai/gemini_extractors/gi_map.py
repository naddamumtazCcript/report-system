import os
from typing import List, Optional
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

# --- Schema Definition ---
class LabMarker(BaseModel):
    marker_name: str = Field(description="The name of the organism or marker, e.g., 'Campylobacter'.")
    result: str = Field(description="The numerical result or '< dl'. Maintain scientific notation like '1.21e5'.")
    status: Optional[str] = Field(description="Extract any flag like 'High', 'High↑', or 'L'. Leave null if blank.")
    reference: str = Field(description="The reference range, e.g., '< 1.00e3'.")

class GeneMarker(BaseModel):
    gene_name: str = Field(description="The name of the gene, e.g., 'PBP1A S414R'.")
    result: str = Field(description="The status of the gene, usually 'Present' or 'Absent'.")

class AntibioticResistance(BaseModel):
    antibiotic_name: str = Field(description="e.g., 'Amoxicillin' or 'Clarithromycin'.")
    result: str = Field(description="Overall status, 'Positive' or 'Negative'.")
    reference: str = Field(description="Usually 'Negative'.")
    resistance_genes: List[GeneMarker] = Field(description="The specific genes listed underneath this antibiotic.")

class PathogensSection(BaseModel):
    bacterial: List[LabMarker] = Field(description="Items under 'BACTERIAL PATHOGENS'")
    parasitic: List[LabMarker] = Field(description="Items under 'PARASITIC PATHOGENS'")
    viral: List[LabMarker] = Field(description="Items under 'VIRAL PATHOGENS'")

class HPyloriSection(BaseModel):
    h_pylori_result: LabMarker = Field(description="The main Helicobacter pylori result row.")
    virulence_factors: List[LabMarker] = Field(description="All rows starting with 'Virulence Factor'")

class IntestinalHealthSection(BaseModel):
    digestion: List[LabMarker] = Field(description="Markers under 'DIGESTION'")
    gi_markers: List[LabMarker] = Field(description="Markers under 'GI MARKERS'")
    immune_response: List[LabMarker] = Field(description="Markers under 'IMMUNE RESPONSE'")
    inflammation: List[LabMarker] = Field(description="Markers under 'INFLAMMATION'")

class GIMapReport(BaseModel):
    pathogens: PathogensSection
    h_pylori: HPyloriSection
    commensal_bacteria: List[LabMarker] = Field(description="COMMENSAL/KEYSTONE BACTERIA")
    bacterial_phyla: List[LabMarker] = Field(description="BACTERIAL PHYLA")
    opportunistic_microbes: List[LabMarker] = Field(description="All dysbiotic, overgrowth, and inflammatory bacteria.")
    fungi_yeast: List[LabMarker] = Field(description="FUNGI/YEAST")
    viruses: List[LabMarker] = Field(description="VIRUSES")
    parasites: List[LabMarker] = Field(description="PARASITES (Protozoa and Worms)")
    intestinal_health: IntestinalHealthSection
    h_pylori_antibiotic_resistance: List[AntibioticResistance] = Field(description="H. PYLORI ANTIBIOTIC RESISTANCE GENES")

# --- Extraction Function ---
def extract_gi_map(file_path: str):
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment")
    
    client = genai.Client(api_key=api_key)
    
    print(f"[DEBUG] Uploading {file_path}...")
    try:
        with open(file_path, 'rb') as f:
            uploaded_file = client.files.upload(file=f, config={'mime_type': 'application/pdf'})
        print(f"[DEBUG] File uploaded successfully")
    except Exception as e:
        print(f"[DEBUG] Upload error: {type(e).__name__}: {str(e)}")
        raise

    prompt = """
    You are a meticulous clinical data extraction assistant. Extract all tables from this Diagnostic Solutions Laboratory (GI-MAP) report.
    1. Preserve all scientific notation exactly as written (e.g., '1.21e5' or '< 1.00e3').
    2. Pay close attention to the 'Result' column for flags like 'High', 'High↑', or 'L'. Extract this into the status field.
    3. For Antibiotic Resistance, group the individual resistance genes underneath their parent antibiotic.
    4. Do not hallucinate data. Return empty lists for missing sections.
    """

    print("[DEBUG] Extracting data with Gemini 2.5 Flash...")
    try:
        response = client.models.generate_content(
            model="models/gemini-2.5-flash",
            contents=[uploaded_file, prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=GIMapReport,
                temperature=0.0 # Force deterministic output
            ),
        )
        print(f"[DEBUG] Gemini response received successfully")
        return response.parsed
    except Exception as e:
        print(f"[DEBUG] Gemini API error: {type(e).__name__}")
        print(f"[DEBUG] Error message: {str(e)}")
        print(f"[DEBUG] Error details: {repr(e)}")
        if hasattr(e, '__dict__'):
            print(f"[DEBUG] Error attributes: {e.__dict__}")
        raise

# data = extract_gi_map("gi_map_sample.pdf")