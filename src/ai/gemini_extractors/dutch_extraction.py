import os
from typing import List, Optional
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from dotenv import load_dotenv
from core.schema import LabResult
from ai.lab_analyzer import analyze_lab_results

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
        parsed_data = response.parsed
        
        # Section map: (category, type) -> biomarker list
        sections = [
            ("SEX HORMONES", "Progesterone Metabolites", parsed_data.sex_hormones.progesterone_metabolites),
            ("SEX HORMONES", "Estrogens and Metabolites", parsed_data.sex_hormones.estrogens_and_metabolites),
            ("SEX HORMONES", "Metabolite Ratios", parsed_data.sex_hormones.metabolite_ratios),
            ("SEX HORMONES", "Androgens and Metabolites", parsed_data.sex_hormones.androgens_and_metabolites),
            ("ADRENAL", "Daily Free Cortisol and Cortisone", parsed_data.adrenal_hormones.daily_free_cortisol_cortisone),
            ("ADRENAL", "Creatinine", parsed_data.adrenal_hormones.creatinine),
            ("ADRENAL", "Cortisol Metabolites and DHEA-S", parsed_data.adrenal_hormones.cortisol_metabolites_dheas),
            ("ORGANIC ACIDS", "Nutritional Markers", parsed_data.organic_acids.nutritional_markers),
            ("ORGANIC ACIDS", "Neuro-Related Markers", parsed_data.organic_acids.neuro_related_markers),
            ("ORGANIC ACIDS", "Additional Markers", parsed_data.organic_acids.additional_markers),
        ]

        lab_results = []
        structured_results = []

        for category, section_type, biomarkers in sections:
            for biomarker in biomarkers:
                flag = "Normal"
                if biomarker.range_flag:
                    range_flag_lower = biomarker.range_flag.lower()
                    if "above" in range_flag_lower or "high" in range_flag_lower:
                        flag = "H"
                    elif "below" in range_flag_lower or "low" in range_flag_lower:
                        flag = "L"

                lab_results.append(LabResult(
                    test_name=biomarker.marker_name,
                    value=biomarker.result_value,
                    unit=biomarker.units,
                    reference_range=biomarker.normal_range,
                    flag=flag,
                    summary=None
                ))
                structured_results.append({
                    "category": category,
                    "type": section_type,
                    "title": biomarker.marker_name,
                    "result": biomarker.result_value,
                    "unit": biomarker.units,
                    "reference": biomarker.normal_range,
                    "flag": biomarker.range_flag or "Normal"
                })

        print("[DEBUG] Analyzing DUTCH results for out-of-range markers...")
        lab_results = analyze_lab_results(lab_results)

        return parsed_data, lab_results, structured_results
        
    except Exception as e:
        print(f"[DEBUG] Gemini API error: {type(e).__name__}")
        print(f"[DEBUG] Error message: {str(e)}")
        print(f"[DEBUG] Error details: {repr(e)}")
        if hasattr(e, '__dict__'):
            print(f"[DEBUG] Error attributes: {e.__dict__}")
        raise

# data = extract_dutch_test("dutch_sample.pdf")