import pandas as pd
from google import genai
from google.genai import types

client = genai.Client(api_key="AIzaSyAJP1zaHjk0zPPdwTRygPABhKJwKVgYBhw")
MODEL = "gemini-3.1-pro-preview"

df = pd.read_csv("V25_big.csv")
df["failure reason"] = df["failure reason"].fillna("")

failed_mask = (df["Status categorized"].str.lower().str.strip() == "failed")
unclassified_mask = (df["failure reason"] == "")
target_rows = df[failed_mask & unclassified_mask]

print(f"Finishing the last {len(target_rows)} drugs synchronously...")

for idx, row in target_rows.iterrows():
    drug_name = row["Name"]
    indication = row["Indication (highest phase)"]
    prompt = f"""
    You are a pharmaceutical clinical trial analyst. 
    Use your web search capabilities to research why the drug {drug_name} for {indication} failed or was discontinued in clinical trials.
    
    Classify the failure into one of these exact two strings:
    - "Scientific failure": Failed due to lack of efficacy, safety, toxicity, or biological reasons.
    - "Market failure": Discontinued for commercial, strategic, funding, or reprioritization reasons.
    
    Return ONLY the exact string "Scientific failure" or "Market failure". Do not provide explanations.
    """
    
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
        if "Scientific failure" in clean_result:
            df.at[idx, "failure reason"] = "Scientific failure"
        elif "Market failure" in clean_result:
            df.at[idx, "failure reason"] = "Market failure"
        else:
            df.at[idx, "failure reason"] = clean_result
        print(f"Classified {drug_name}: {df.at[idx, 'failure reason']}")
    except Exception as e:
        print(f"Error on {drug_name}: {e}")
        df.at[idx, "failure reason"] = "Error"

df.to_csv("V25_big.csv", index=False)
print("Finished completely!")
