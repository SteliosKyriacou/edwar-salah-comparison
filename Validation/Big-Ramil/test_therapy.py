import pandas as pd
from google import genai
from google.genai import types

client = genai.Client(api_key="AIzaSyAJP1zaHjk0zPPdwTRygPABhKJwKVgYBhw")
MODEL = "gemini-3.1-pro-preview"

def classify_therapy_type(drug_name, indication):
    prompt = f"""
    You are a pharmaceutical clinical trial analyst. 
    Use your web search capabilities to research the clinical trial design for the drug {drug_name} (studied for {indication}).
    
    Determine if the drug was primarily evaluated as a single agent or in combination with other active drugs.
    
    Classify the therapy type into one of these exact strings:
    - "Monotherapy" (Tested alone, single agent)
    - "Combination Therapy" (Tested in combination with standard of care, another active drug, or as a fixed-dose combo)
    - "Unknown" (If you cannot find the information)
    
    Return ONLY the exact string from the list above. Do not provide explanations.
    """
    resp = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.0,
            tools=[types.Tool(google_search=types.GoogleSearch())],
        ),
    )
    clean_result = (resp.text or "").strip().strip('"').strip("'")
    return clean_result

# AL-335 is for Hepatitis C
# GS-9451 (Tegobuvir) is also for Hepatitis C
drugs_to_test = [
    ("AL-335", "Hepatitis C"),
    ("GS-9451", "Hepatitis C")
]

for name, ind in drugs_to_test:
    print(f"Testing {name} for {ind}...")
    try:
        res = classify_therapy_type(name, ind)
        print(f"Result: {res}\n")
    except Exception as e:
        print(f"Error: {e}\n")
