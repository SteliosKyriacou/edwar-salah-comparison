"""Batch blinded critique of neurodegenerative clinical candidates."""

import json
import time
import requests

API = "http://localhost:8000/api/analyze"

MOLECULES = [
    {"name": "Ambroxol", "smiles": "NC1=C(CNC2CCC(O)CC2)C=C(Br)C=C1Br", "target": "GCase (GBA1) Chaperone / Lysosomal", "indication": "GBA-PD (disease modifying)"},
    {"name": "Blarcamesine (ANAVEX2-73)", "smiles": "CN(C)CC1CCOC1(C1=CC=CC=C1)C1=CC=CC=C1", "target": "sigma-1R Agonist", "indication": "Alzheimer's Disease"},
    {"name": "DNL343", "smiles": "O=C(COC1=CC=C(Cl)C=C1)NC12CC(C3=NN=C(C4CC(OC(F)(F)F)C4)O3)(C1)C2", "target": "eIF2B Activator", "indication": "ALS (ISR Modulation)"},
    {"name": "Deferiprone", "smiles": "CC1=C(O)C(=O)C=CN1C", "target": "Iron Chelator", "indication": "Parkinson's Disease"},
    {"name": "Masitinib", "smiles": "CC1=C(NC2=NC(C3=CN=CC=C3)=CS2)C=C(NC(=O)C2=CC=C(CN3CCN(C)CC3)C=C2)C=C1", "target": "Tyrosine Kinase Inhibitor (c-Kit)", "indication": "Mild-to-Moderate AD (adjunct)"},
    {"name": "Neflamapimod (VX-745)", "smiles": "O=C1N=CN2N=C(SC3=C(F)C=C(F)C=C3)C=CC2=C1C1=C(Cl)C=CC=C1Cl", "target": "p38a MAPK Inhibitor", "indication": "Dementia with Lewy Bodies"},
    {"name": "Nilotinib", "smiles": "CC1=CN(C2=CC(C(F)(F)F)=CC(NC(=O)C3=CC(NC4=NC=CC(C5=CN=CC=C5)=N4)=C(C)C=C3)=C2)C=N1", "target": "BCR-ABL / c-Kit TK Inhibitor", "indication": "Dementia with Lewy Bodies"},
    {"name": "Pridopidine", "smiles": "CCCN1CCC(C2=CC(S(C)(=O)=O)=CC=C2)CC1", "target": "sigma-1R Agonist", "indication": "ALS"},
    {"name": "Simufilam (PTI-125)", "smiles": "CN1CCC2(CC1)NCC(=O)N2CC1=CC=CC=C1", "target": "Filamin A", "indication": "Mild-to-Moderate AD"},
    {"name": "Taurursodiol (AMX0035)", "smiles": "C[C@H](CCC(=O)NCCS(=O)(=O)O)[C@H]1CC[C@H]2[C@@H]3[C@@H](O)C[C@@H]4C[C@H](O)CC[C@]4(C)[C@H]3CC[C@]12C", "target": "ER/Mitochondrial Stress Modulation", "indication": "ALS"},
    {"name": "Tavapadon", "smiles": "CC1=C(C2=C(C)C(=O)NC(=O)N2C)C=CC(OC2=C(C(F)(F)F)C=CC=N2)=C1", "target": "D1/D5 Partial Agonist", "indication": "Parkinson's Disease (Motor Fluctuations)"},
    {"name": "Troriluzole", "smiles": "CN(CC(=O)NC1=NC2=C(C=C(OC(F)(F)F)C=C2)S1)C(=O)CNC(=O)CN", "target": "Glutamatergic Modulation", "indication": "Spinocerebellar Ataxia"},
    {"name": "Valiltramiprosate (ALZ-801)", "smiles": "CC(C)[C@H](N)C(=O)NCCCS(=O)(=O)O", "target": "Anti-Abeta (Oligomer Inhibitor)", "indication": "Early AD (APOE e4/e4)"},
    {"name": "Vatiquinone (PTC743)", "smiles": "CC(C)=CCC/C(C)=C/CC/C(C)=C/CC[C@@](C)(O)CCC1=C(C)C(=O)C(C)=C(C)C1=O", "target": "Redox/Mitochondrial Pathway Modulator", "indication": "Friedreich's Ataxia"},
    {"name": "Verdiperstat (BHV-3241)", "smiles": "CC(C)OCCN1C(=S)NC(=O)C2=C1C=CN2", "target": "Myeloperoxidase Inhibitor", "indication": "ALS"},
    {"name": "Votoplam (PTC518)", "smiles": "CC1(C)CC(N2N=NC3=CC(C4=C(O)C=C(N5N=CC=N5)C=C4)=NN=C32)CC(C)(C)N1", "target": "Splicing Modulator (HTT Lowering)", "indication": "Huntington's Disease"},
    {"name": "Xanamem", "smiles": "O=C(C1=CSC(C2=CNN=C2)=C1)N1[C@@H]2CC[C@H]1C[C@](O)(C1=NC=CC=N1)C2", "target": "11beta-HSD1 Inhibitor", "indication": "AD Dementia"},
    {"name": "Zervimesine (CT1812)", "smiles": "CC(C)(C)OC1=C(O)C=CC(CCC(C)(C)N2CC3=C(C=C(S(C)(=O)=O)C=C3)C2)=C1", "target": "sigma-2R/TMEM97 Antagonist", "indication": "Early AD"},
    {"name": "anle138b", "smiles": "BrC1=CC=CC(C2=NNC(C3=CC4=C(C=C3)OCO4)=C2)=C1", "target": "alpha-Synuclein Modulator", "indication": "Parkinson's Disease"},
]

OUTPUT_FILE = "/Users/stylianoskyriacou/Edward_Salah/edwar-salah-comparison/web/neuro_batch_results.json"

results = []

for i, mol in enumerate(MOLECULES):
    print(f"[{i+1}/{len(MOLECULES)}] {mol['name']}...", flush=True)
    t0 = time.time()
    try:
        resp = requests.post(API, json={
            "smiles": mol["smiles"],
            "target": mol["target"],
            "indication": mol["indication"],
        }, timeout=300)
        resp.raise_for_status()
        data = resp.json()
        elapsed = time.time() - t0
        results.append({
            "name": mol["name"],
            "smiles": mol["smiles"],
            "target": mol["target"],
            "indication": mol["indication"],
            "edward": data["edward"],
            "salah": data["salah"],
            "elapsed_sec": round(elapsed, 1),
        })
        e = data["edward"]
        s = data["salah"]
        tcsp = e.get("tcsp", 0)
        tcsp_pct = tcsp * 100 if isinstance(tcsp, float) and tcsp <= 1 else tcsp
        print(f"    Score={e.get('edward_score')}  Verdict={s.get('salah_verdict')}  TCSP={tcsp_pct:.2f}%  ({elapsed:.0f}s)")
    except Exception as ex:
        print(f"    FAILED: {ex}")
        results.append({"name": mol["name"], "error": str(ex)})

with open(OUTPUT_FILE, "w") as f:
    json.dump(results, f, indent=2)

print(f"\nDone. Results saved to {OUTPUT_FILE}")
