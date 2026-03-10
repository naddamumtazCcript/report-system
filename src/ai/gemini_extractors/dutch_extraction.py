import os
from typing import List, Optional
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

# --- Schema Definition ---
class DutchBiomarker(BaseModel):
    marker_name: str = Field(description="The exact name of the biomarker, e.g., 'b-Pregnanediol'")
    result_value: str = Field(description="The numerical result extracted.")
    range_flag: Optional[str] = Field(description="The text indicating status, e.g., 'Above range', 'Low end of range', 'Within luteal range'.")
    units: str = Field(description="The unit of measurement, e.g., 'ng/mg' or 'ug/mg'.")
    normal_range: str = Field(description="The numeric range provided in the far right column.")

class SexHormones(BaseModel):
    progesterone_metabolites: List[DutchBiomarker] = Field(description="Markers under 'Progesterone Metabolites (Urine)'")
    estrogens_and_metabolites: List[DutchBiomarker] = Field(description="Markers under 'Estrogens and Metabolites (Urine)'")
    metabolite_ratios: List[DutchBiomarker] = Field(description="Extract the ratios like 2-OH/16-OH-E1 Balance.")
    androgens_and_metabolites: List[DutchBiomarker] = Field(description="Markers under 'Androgens and Metabolites (Urine)'")

class AdrenalHormones(BaseModel):
    daily_free_cortisol_cortisone: List[DutchBiomarker] = Field(description="Markers under 'Daily Free Cortisol and Cortisone (Urine)'")
    creatinine: List[DutchBiomarker] = Field(description="Markers under 'Creatinine (Urine)'")
    cortisol_metabolites_dheas: List[DutchBiomarker] = Field(description="Markers under 'Cortisol Metabolites and DHEA-S (Urine)'")

class OrganicAcids(BaseModel):
    nutritional_markers: List[DutchBiomarker] = Field(description="Markers under 'Nutritional Organic Acids (Urine)'")
    neuro_related_markers: List[DutchBiomarker] = Field(description="Markers under 'Neuro-Related Markers (Urine)'")
    additional_markers: List[DutchBiomarker] = Field(description="Markers under 'Additional Markers (Urine)'")

class DutchReport(BaseModel):
    patient_sex: str = Field(description="Identify if this is a Male or Female Sample Report.")
    patient_age: str = Field(description="Age of the patient.")
    sex_hormones: SexHormones
    adrenal_hormones: AdrenalHormones
    organic_acids: OrganicAcids

# --- Extraction Function ---
def extract_dutch_test(file_path: str):
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment")
    
    client = genai.Client(api_key=api_key)
    
    print(f"[DEBUG] Uploading {file_path}...")
    try:
        with open(file_path, 'rb') as f:
            uploaded_file = client.files.upload(file=f, config={'mime_type': 'application/pdf'})
        print(f"[DEBUG] File uploaded successfully: {uploaded_file}")
    except Exception as e:
        print(f"[DEBUG] Upload error: {type(e).__name__}: {str(e)}")
        raise

    prompt = """
    You are a clinical data extraction assistant. Extract the patient data from this DUTCH Complete hormone test. 
    1. Identify if the report is for a Male or Female patient.
    2. IGNORE the graphical dials and visual hormone flowcharts completely.
    3. Extract the exact values, units, and normal ranges STRICTLY from the tabular summary pages titled 'Sex Hormones & Metabolites', 'Adrenal Hormones & Metabolites', and 'Organic Acid Tests (OATs)'.
    4. Capture the exact wording used for the range status (e.g., 'Above range', 'Low end of range') in the range_flag field.
    """

    print("[DEBUG] Extracting data with Gemini 2.5 Flash...")
    try:
        response = client.models.generate_content(
            model="models/gemini-2.5-flash",
            contents=[uploaded_file, prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=DutchReport,
                temperature=0.0
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

# data = extract_dutch_test("dutch_sample.pdf")