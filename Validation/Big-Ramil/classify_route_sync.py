import os
import time
import pandas as pd
from tqdm import tqdm
from google import genai
from google.genai import types
from google.genai.errors import APIError

client = genai.Client(api_key="AIzaSyAJP1zaHjk0zPPdwTRygPABhKJwKVgYBhw")
MODEL = "gemini-3.1-pro-preview"

def classify_drug_route(drug_name, indication):
    prompt = f"""
    You are a pharmaceutical clinical trial analyst. 
    Use your web search capabilities to research the clinical administration route for the drug {drug_name} (studied for {indication}).
    
    Classify the administration route into one of these exact strings:
    - "Oral" (e.g., tablets, capsules)
    - "Intravenous" (e.g., IV infusions)
    - "Subcutaneous" (e.g., SC injections)
    - "Topical" (e.g., creams, eye drops, ointments)
    - "Inhalation" (e.g., inhalers, nebulizers)
    - "Intramuscular" (e.g., IM injections)
    - "Other" (Any other specific route)
    - "Unknown" (If you cannot find the information)
    
    Return ONLY the exact string from the list above. Do not provide explanations.
    """
    
    max_retries = 5
    for attempt in range(max_retries):
        try:
            resp = client.models.generate_content(
                model=MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.0,
                    tools=[types.Tool(google_search=types.GoogleSearch())],
                ),
            )
            
            clean_result = (resp.text or "").strip().strip('"').strip("'")
            valid_routes = ["Oral", "Intravenous", "Subcutaneous", "Topical", "Inhalation", "Intramuscular", "Other", "Unknown"]
            
            for route in valid_routes:
                if route.lower() in clean_result.lower():
                    return route
            return "Unknown"
            
        except APIError as e:
            if "429" in str(e) or "503" in str(e):
                time.sleep(10 + attempt * 5)
            else:
                return "Error"
        except Exception as e:
            return "Error"
    return "Error"

if __name__ == "__main__":
    df = pd.read_csv("V25_big.csv")
    
    if "administration route" not in df.columns:
        df["administration route"] = ""
        
    df["administration route"] = df["administration route"].fillna("")
    target_rows = df[df["administration route"] == ""]
    
    print(f"Synchronously classifying the final {len(target_rows)} drugs...")
    
    for idx, row in tqdm(target_rows.iterrows(), total=len(target_rows)):
        route = classify_drug_route(row["Name"], row["Indication (highest phase)"])
        df.at[idx, "administration route"] = route
        
        # Save incrementally
        df.to_csv("V25_big.csv", index=False)
                
    df.to_csv("V25_big.csv", index=False)
    print("Classification completely finished!")
