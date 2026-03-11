"""Smoke test: Run V25 pipeline on 1 good molecule + 1 bad molecule.

Good: Atorvastatin — HMG-CoA reductase inhibitor, blockbuster statin.
Bad:  A deliberately toxic molecule — reactive warhead + hERG pharmacophore + high logP.

Usage:
    python test/test_v25_smoke.py
"""

import os
import sys
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from main import run_v25_pipeline  # noqa: E402

# Atorvastatin — approved blockbuster, excellent drug
GOOD_SMILES = "CC(C)c1n(CC[C@@H](O)C[C@@H](O)CC(O)=O)c(-c2ccc(F)cc2)c(-c2ccccc2)c1C(=O)Nc1ccccc1"
GOOD_TARGET = "Enzyme"
GOOD_INDICATION = "Cardiovascular"

# Fictional bad molecule — nitroaromatic + hydrazine + highly lipophilic + basic amine with long chain (hERG)
BAD_SMILES = "O=[N+]([O-])c1ccc(NNC(=O)CCCCCCCCCCc2ccc(N(C)C)cc2)cc1"
BAD_TARGET = "Unknown"
BAD_INDICATION = "Chronic Metabolic"


def run_test(label, smiles, target, indication):
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"  SMILES: {smiles[:60]}...")
    print(f"  Target: {target} | Indication: {indication}")
    print(f"{'='*60}\n")

    result = run_v25_pipeline(smiles, target, indication)

    score = result.get("MedChem Score V25", "N/A")
    bio = result.get("Bio Verdict V25", "N/A")
    toxi = result.get("Toxi Verdict V25", "N/A")
    pharma = result.get("Pharma Verdict V25", "N/A")
    tcsp = result.get("TCSP V25", 0)
    tcsp_pct = tcsp * 100 if isinstance(tcsp, float) and tcsp <= 1 else tcsp

    print(f"\n--- RESULTS ---")
    print(f"  MedChem Score: {score}")
    print(f"  TCSP:          {tcsp_pct:.2f}%")
    print(f"  Bio Verdict:   {bio}")
    print(f"  Toxi Verdict:  {toxi}")
    print(f"  Pharma Verdict:{pharma}")
    print(f"  Final P1:      {result.get('Final P1 V25', 'N/A')}")
    print(f"  Final P2:      {result.get('Final P2 V25', 'N/A')}")
    print(f"  Final P3:      {result.get('Final P3 V25', 'N/A')}")
    print(f"  Rationale:     {str(result.get('Rationale V25', ''))[:200]}...")

    return result


def main():
    print("V25 Multi-Agent Pipeline — Smoke Test")
    print("Testing with 1 good molecule and 1 bad molecule\n")

    good_result = run_test("GOOD MOLECULE: Atorvastatin (HMG-CoA inhibitor, Cardiovascular)",
                           GOOD_SMILES, GOOD_TARGET, GOOD_INDICATION)

    bad_result = run_test("BAD MOLECULE: Toxic design (nitroaromatic + hydrazine + hERG trap)",
                          BAD_SMILES, BAD_TARGET, BAD_INDICATION)

    # Sanity checks
    good_score = good_result.get("MedChem Score V25", 50)
    bad_score = bad_result.get("MedChem Score V25", 50)

    print(f"\n{'='*60}")
    print(f"  SUMMARY")
    print(f"{'='*60}")
    print(f"  Good molecule score: {good_score}  (expect low = good)")
    print(f"  Bad molecule score:  {bad_score}  (expect high = bad)")

    if good_score < bad_score:
        print(f"\n  PASS: Good molecule scored lower than bad molecule ({good_score} < {bad_score})")
    else:
        print(f"\n  WARNING: Scoring may need review — good={good_score}, bad={bad_score}")

    # Save raw results
    out_dir = os.path.join(os.path.dirname(__file__))
    with open(os.path.join(out_dir, "smoke_test_results.json"), "w") as f:
        json.dump({"good": good_result, "bad": bad_result}, f, indent=2)
    print(f"\n  Raw results saved to test/smoke_test_results.json")


if __name__ == "__main__":
    main()
