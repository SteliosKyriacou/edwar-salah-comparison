# Post-2025 Failure Analysis — V24 Upgrade Notes

## Purpose
This document captures all systematic failure modes observed when running Edward V23 + Salah V23 on the 2025 drug dataset (N=29, 22 approved, 7 failed). Use this as the primary reference when upgrading to V24.

---

## 1. HEADLINE RESULT

V23 achieved **AUC 0.643** on 2025 drugs vs **AUC 0.877** on modern (1999–2024) drugs. The approved median score (81) was nearly identical to the failed median (82), giving a discrimination gap of **1 point** vs **20 points** on modern data. The system is essentially random on 2025 drugs.

---

## 2. ROOT CAUSE: PARADIGM SHIFT IN DRUG DESIGN

### 2.1 The 2025 drug landscape is structurally different

| Metric | Modern Approved (1999–2024) | 2025 Approved |
|---|---|---|
| Mean MW | ~369 (enzymes), ~400 (overall) | ~480 |
| % molecules MW > 500 | 17% | 31% |
| % peptide-like (>=3 amides) | 2% | 7% |
| % "beyond rule-of-5" | 20% | 38% |
| Dominant approved classes | SGLT2i, DPP-4i, PPIs, SSRIs | Kinases, BTK inhibitors, topoisomerases, GPCRs |

### 2.2 Target class approval rates inverted

| Target Class | Pre-2025 Approval Rate | 2025 Approval Rate | Pre-2025 Approved Median Score | 2025 Approved Median Score |
|---|---|---|---|---|
| Enzyme | 34% | **100%** | 55 | 78 (+23) |
| Kinase | **0%** (all failed) | **83%** | — | 85 |
| GPCR | 43% | 62% | 68 | 82 (+14) |
| Ion Channel | 55% | **100%** | 70 | 80 (+10) |

**Critical**: The modern dataset has ZERO approved kinase inhibitors. Edward has never been calibrated to know what a "good" kinase inhibitor looks like.

---

## 3. SYSTEMATIC FAILURE MODES

### 3.1 Edward's Physicochemical Rules Are Obsolete for 2025 Drugs

**The "Brick" Rule (MW > 500 + TPSA < 40 = ROCK)** penalizes molecules that modern formulation science has made viable:
- `elinzanetant` (MW=668, Approved) — scored 82, called a "physicochemical monstrosity"
- `rilzabrutinib` (MW=665, Approved) — scored 85, called "structurally bloated"
- `tradipitant` (MW=587, Approved) — scored 88, called a "physicochemical disaster"
- `elamipretide` (MW=639, Approved) — scored 85, "blatantly violates all small-molecule metrics"

**The "Balloon" Rule (RotBonds > 10)** flags molecules with modern flexibility management:
- `sebetralstat` (10 RotB, Approved) — scored 68

**The "Grease Tax" (high cLogP)** over-penalizes lipophilic drugs with validated targets:
- `tradipitant` (cLogP >5, NK1 antagonist) — functional lipophilicity is acceptable for GPCR binding
- `atrasentan` (cLogP >4.5, ETA antagonist) — endothelin antagonists are inherently lipophilic

**FIX NEEDED**: Edward's hard thresholds need era-aware calibration. Consider:
- Raising MW threshold from 450 to 500 for oncology/rare disease/hematology
- Making "Brick"/"Balloon" warnings rather than hard penalties when the target class requires large scaffolds (kinases, covalent inhibitors)
- Adding a "Formulation Credit" — if a molecule has properties that modern delivery (nanoparticles, topical, subcutaneous) can overcome, reduce the penalty

### 3.2 hERG Hard Kill Misapplied to Ion Channel Drugs

`etripamil` (Score=88, Approved, Ion Channel, Cardiovascular) was hard-killed for "textbook hERG pharmacophore" — but it's literally a calcium channel blocker designed to interact with ion channels. The hERG pharmacophore alert should not apply the same way when the target IS an ion channel.

**FIX NEEDED**: Add context-awareness to the hERG Hard Kill:
- If target_class is "Ion Channel" and the molecule is designed for cardiac use, the hERG pharmacophore is expected, not a liability
- Penalize for hERG SELECTIVITY concern, not mere presence of the pharmacophore

### 3.3 Covalent Inhibitor Warheads Treated as Suicide Inhibition

`remibrutinib` (Score=85, Approved) — Edward flagged the acrylamide Michael acceptor as a "terminal, deliberate reactive warhead" and treated it as MBI. But modern covalent kinase inhibitors (ibrutinib, osimertinib, acalabrutinib) are an established and FDA-validated drug class.

`brensocatib` (Score=85, Approved) — the alpha-amino nitrile reversible covalent warhead was penalized as a structural alert, despite being the intended mechanism.

**FIX NEEDED**: Add a "Covalent Inhibitor Credit":
- If the molecule contains a known covalent warhead (acrylamide, nitrile, alpha-cyanoacrylamide) AND the target is a kinase or protease, this is deliberate design, not accidental toxicity
- Reduce the MBI penalty for established covalent mechanisms with approved precedent
- Still flag novel/unusual reactive warheads appropriately

### 3.4 Salah Never Issues ELITE Verdicts on 2025 Drugs

| Verdict | Modern Approved | 2025 Approved |
|---|---|---|
| ELITE | 11 (13%) | **0 (0%)** |
| CAUTION | 72 (83%) | 22 (100%) |
| TERMINATE | 4 (5%) | 0 (0%) |

Salah gave CAUTION to every single 2025 approved drug. On modern data, 13% of approved drugs received ELITE — these are the ones that get significant score reductions. Without any ELITE verdicts, Edward never gets the "this target is validated and safe" signal to lower scores.

**Why**: Salah's target attrition database is anchored to historical failures. For 2025 targets, Salah hedges because it lacks confidence — it knows kinases CAN fail, enzymes CAN cause DILI, GPCRs CAN have off-target effects. It never says "this specific mechanism is clean."

**FIX NEEDED**: Salah needs a "Validated Mechanism Credit":
- If a target class has >=3 approved drugs in the same indication (e.g., BTK inhibitors in hematology), the base verdict should start at ELITE, not CAUTION
- Salah should distinguish between "novel, unvalidated target" (CAUTION) and "well-trodden mechanism with approved peers" (ELITE)
- Add specific approved-class precedent lists: BTK inhibitors, MEK inhibitors, topoisomerase inhibitors, endothelin antagonists

### 3.5 Topical/Local Delivery Drugs Penalized for Systemic Properties

`etripamil` (nasal spray for SVT) and `delgocitinib` (topical JAK inhibitor for dermatology) and `acoltremon` (ophthalmic) are NOT systemic drugs. Edward evaluated them as if they need oral bioavailability and systemic safety margins.

**FIX NEEDED**: Add route-of-administration awareness:
- If indication is Ophthalmology, Dermatology, or route is topical/nasal/inhaled, systemic DILI/hERG concerns are dramatically reduced
- Reduce "High Dose = DILI" penalty for non-oral drugs

### 3.6 Rare Disease / Oncology Drugs Held to Chronic Safety Standards

Edward applies the same safety bar to a rare disease drug (elamipretide for Barth syndrome, ~300 patients worldwide) as to a chronic cardiovascular drug (millions of patients). The risk-benefit calculus is fundamentally different.

**FIX NEEDED**: Add indication-severity weighting:
- Rare disease / orphan drugs: relax safety thresholds (patients have no alternatives)
- Oncology: accept higher toxicity if efficacy signal is strong
- Chronic metabolic: maintain strict safety standards

---

## 4. WHAT V23 GOT RIGHT ON 2025

Despite the poor AUC, V23 correctly identified several failures:

- `Monlunabant` (95, TERMINATE) — CB1 inverse agonist for metabolism. Salah correctly flagged the neuropsychiatric suicide risk (Rimonabant effect). This is EXACTLY what Salah was built for.
- `Azelaprag` (88, TERMINATE) — APJ agonist for metabolism. Salah flagged novel target with no clinical precedent.
- `BAY3630914` (82, TERMINATE) — Transcription factor for oncology. Salah correctly identified undruggable target class.
- `Repibresib` (82, TERMINATE) — Epigenetic for dermatology. Salah flagged chronic epigenetic modulation risks.
- `Simufilam` (78, TERMINATE) — Scaffold protein for neurology. Salah flagged PPI target + Alzheimer's graveyard.

**Pattern**: Salah's TERMINATE verdicts are reliable — 5/5 TERMINATE calls were on failed drugs. The problem is that Salah doesn't give enough ELITE calls to pull approved drug scores down.

---

## 5. SPECIFIC MOLECULE LESSONS

### Approved drugs Edward should learn from:

| Compound | Score | Why Edward Failed | What V24 Should Learn |
|---|---|---|---|
| elamipretide | 85 | "Violates all small-molecule metrics" | Peptide-like drugs for rare disease can succeed despite rule violations |
| mirdametinib | 85 | "Halogenation nightmare, iodine atom" | MEK inhibitors are validated; heavy halogenation is acceptable in oncology |
| rilzabrutinib | 85 | "Structurally bloated covalent inhibitor" | BTK covalent inhibitors are an established approved class |
| remibrutinib | 85 | "Terminal reactive warhead" | Acrylamide warheads in BTK inhibitors are feature, not bug |
| zoliflodacin | 88 | "Physicochemical brick, barbiturate" | Novel spirocyclic antibiotics can succeed; high TPSA is OK for anti-infectives |
| tradipitant | 88 | "Physicochemical disaster, Brick" | NK1 antagonists for GI/nausea are validated; high MW is tolerable |
| etripamil | 88 | "hERG Hard Kill" | Nasal calcium channel blockers don't need systemic hERG safety |

### Failed drugs Edward correctly flagged:

| Compound | Score | Salah Verdict | Why It Failed (ground truth) |
|---|---|---|---|
| Monlunabant | 95 | TERMINATE | CB1 inverse agonism → neuropsychiatric risk (class effect) |
| Azelaprag | 88 | TERMINATE | Novel APJ agonist, no validated mechanism |
| PF-06882961 | 88 | CAUTION | Oral GLP-1 peptide, massive dose requirement |
| BAY3630914 | 82 | TERMINATE | Transcription factor — historically undruggable |
| Repibresib | 82 | TERMINATE | Chronic epigenetic modulation, safety concerns |
| Simufilam | 78 | TERMINATE | Scaffold protein PPI in Alzheimer's (graveyard) |
| Gartisertib | 68 | CAUTION | ATR kinase — on-target bone marrow toxicity |

---

## 6. V24 UPGRADE PRIORITIES (ordered by impact)

1. **Salah: Add Validated Mechanism Credit** — enable ELITE verdicts for targets with >=3 approved drugs in the same class. This alone could recover 10-15 points for BTK inhibitors, endothelin antagonists, etc. (HIGHEST IMPACT)

2. **Edward: Era-aware MW/LogP thresholds** — raise hard limits for oncology/rare disease. 2025 approved drugs routinely exceed MW 500.

3. **Edward: Covalent Inhibitor Credit** — don't treat acrylamide/nitrile warheads as MBI when targeting kinases/proteases with approved covalent precedent.

4. **Edward: Route-of-administration awareness** — reduce systemic safety penalties for topical/nasal/ophthalmic drugs.

5. **Edward: hERG context for ion channel drugs** — don't hard-kill a calcium channel blocker for having an hERG pharmacophore.

6. **Salah: Indication-severity weighting** — rare disease and oncology drugs have different risk-benefit thresholds than chronic metabolic drugs.

7. **Edward: Peptide/macrocycle tolerance** — MW >500 with high TPSA should not auto-penalize if the molecule is a peptide or designed for non-oral delivery.

---

## 7. DATASET STATISTICS FOR REFERENCE

```
2025 Dataset: N=29 (22 approved, 7 failed)
  - Removed: Pasodacigib, BAY-2965501, Bitopertin (data quality)
  - AUC: 0.643, AP: 0.697 (baseline 0.69)
  - Approved median: 81, Failed median: 82, Gap: 1

Modern Dataset: N=219 (87 approved, 132 failed)
  - AUC: 0.877, AP: 0.836
  - Approved median: 68, Failed median: 88, Gap: 20

V22 Modern (for comparison): AUC 0.933
```

---

*Generated 2026-03-10 from V23 analysis of 2025_drug_data_complete.csv*
