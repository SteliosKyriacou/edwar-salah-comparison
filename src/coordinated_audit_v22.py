import pandas as pd
import json
import os
import time
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

os.environ["GOOGLE_API_KEY"] = "AIzaSyAE4QTjaE2K_28m3QlSdhpbBJBN8ZmH3fA"

# Load Agents
with open("/home/node/.openclaw/workspace/Agents/edward-medchem-rationalist/INSTRUCTIONS.md", "r") as f:
    EDWARD_PROMPT = f.read()
with open("/home/node/.openclaw/workspace/Agents/salah-biological-rationalist/INSTRUCTIONS.md", "r") as f:
    SALAH_PROMPT = f.read()

llm = ChatGoogleGenerativeAI(model="gemini-3-pro-preview", temperature=0.0)

def run_coordinated_audit(smiles, target, indication):
    print(f"🦾 Coordinating Audit for: {smiles[:20]}...")
    
    # 1. SALAH'S TURN (Biological Risk)
    salah_input = f"Evaluate the biological risk: Target {target}, Indication {indication} for molecule {smiles}."
    salah_resp = llm.invoke([SystemMessage(content=SALAH_PROMPT), HumanMessage(content=salah_input)])
    
    salah_content = salah_resp.content
    if isinstance(salah_content, list):
        salah_content = "".join([str(c.get('text', '')) if isinstance(c, dict) else str(c) for c in salah_content])
    
    salah_data = json.loads(salah_content.replace("```json", "").replace("```", "").strip())
    
    # 2. EDWARD'S TURN (MedChem Critique)
    edward_input = f"""
    Molecule SMILES: {smiles}
    Target Class: {target}
    Indication: {indication}
    
    BIO-ADVISORY FROM SALAH (Biological/Clinical Expert):
    Verdict: {salah_data['salah_verdict']}
    Biological Rationale: {salah_data['biological_rationale']}
    Penalty for Historical Target Stigma: {salah_data['target_stigma_penalty']} points
    
    TASK: Provide your final MedChem audit as Edward. Integrate the Biological Advisory above into your rationale and final Edward Score. If Salah suggests a penalty, add it to your score. 
    """
    print("  Salah finished. Edward starting...")
    edward_resp = llm.invoke([SystemMessage(content=EDWARD_PROMPT), HumanMessage(content=edward_input)])
    
    edward_content = edward_resp.content
    if isinstance(edward_content, list):
        edward_content = "".join([str(c.get('text', '')) if isinstance(c, dict) else str(c) for c in edward_content])
        
    print(f"  Edward Raw Content: {edward_content[:200]}...")
    
    clean_edward = edward_content.replace("```json", "").replace("```", "").strip()
    start_idx = clean_edward.find('{')
    end_idx = clean_edward.rfind('}') + 1
    if start_idx != -1 and end_idx != -1:
        edward_data = json.loads(clean_edward[start_idx:end_idx])
    else:
        raise ValueError(f"Failed to find JSON in Edward's response: {edward_content}")
    
    return {**edward_data, "salah_verdict": salah_data['salah_verdict'], "biological_risk": salah_data['biological_rationale']}

if __name__ == "__main__":
    # Test on Atabecestat (BACE failure)
    SMILES = "C1[C@H]2CSC(=N[C@]2(CO1)C3=C(C=CC(=C3)NC(=O)C4=NC=C(C=C4)F)F)N"
    res = run_coordinated_audit(SMILES, "BACE1", "Alzheimer's")
    print(json.dumps(res, indent=2))
