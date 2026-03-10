import os
from typing import List, Optional
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

# --- Schema Definition ---
class BloodworkEntry(BaseModel):
    test_name: str = Field(description="Name of the test, e.g., 'Cholesterol, Total' or 'LDL Chol Calc (NIH)'")
    result: str = Field(description="The numerical result.")
    flag: Optional[str] = Field(description="Capture 'H' for High or 'L' for Low if present next to the result.")
    reference_range: str = Field(description="The expected normal range, e.g., '100 - 199'.")
    units: str = Field(description="The unit of measure, e.g., 'mg/dL' or 'x10E3/uL'.")

class BloodworkReport(BaseModel):
    report_date: str = Field(description="Date the report was generated.")
    results: List[BloodworkEntry] = Field(description="A flat list of every single lab test found in the document.")

# --- Extraction Function ---
def extract_bloodwork(file_path: str):
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment")
    
    client = genai.Client(api_key=api_key)
    
    print(f"Uploading {file_path}...")
    with open(file_path, 'rb') as f:
        uploaded_file = client.files.upload(file=f, config={'mime_type': 'application/pdf'})

    prompt = """
    Extract every lab test from this functional bloodwork panel. 
    1. Separate the numerical result from the 'H' or 'L' flag (e.g., Result: '213', Flag: 'H').
    2. Capture the full reference range (e.g., '100-199').
    3. If a test has sub-components (like the CBC with Differential), list each one as an individual entry.
    4. For the Leptin section, only extract the final result and the relevant range. COMPLETELY IGNORE the "Female Ranges by Body Mass Index (BMI)" lookup table.
    5. CRITICAL: Explicitly look for and extract the 'Vitamin D, 25-Hydroxy' test, which is located after the Leptin section and before the Testosterone section. Do not skip it.
    """

    print("Extracting data with Gemini 2.5 Flash...")
    response = client.models.generate_content(
        model="models/gemini-2.5-flash",
        contents=[uploaded_file, prompt],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=BloodworkReport,
            temperature=0.0
        ),
    )
    
    parsed_data = response.parsed
    
    # Deduplication: Keep last occurrence of each test
    unique_results_dict = {entry.test_name: entry for entry in parsed_data.results}
    parsed_data.results = list(unique_results_dict.values())
    
    return parsed_data

# data = extract_bloodwork("bloodwork_sample.pdf")