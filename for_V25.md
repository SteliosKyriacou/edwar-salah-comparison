# V25 — Multi-Agent Advisory Pipeline

## Motivation

V24 dramatically improved discrimination on 2025 drugs (AUC 0.643 → 0.718, gap 1 → 40 points) by teaching Edward and Salah context-aware reasoning. However, one critical blind spot remains: **Gartisertib** (ATR kinase, oncology) scored 12/ELITE despite failing due to on-target bone marrow toxicity. Salah correctly recognized kinases in oncology as a validated class — but had no framework to flag that DDR kinases carry an inherent narrow therapeutic window against healthy dividing tissue.

This failure reveals a structural gap in the two-agent pipeline: Salah reasons about **biological feasibility** (is the target druggable? is the mechanism validated?) but does not deeply model **predictive toxicology** (what will this mechanism do to healthy tissue?) or **clinical pharmacology** (what dose is needed, and does the PK support a safe therapeutic window?). These are distinct disciplines with distinct reasoning frameworks.

## Architecture: Four Agents, One Chemist

```
                ┌──────────────┐
                │   SMILES +   │
                │  Target +    │
                │  Indication  │
                └──────┬───────┘
                       │
           ┌───────────┼───────────┐
           │           │           │
           ▼           ▼           ▼
    ┌──────────┐ ┌──────────┐ ┌──────────┐
    │  SALAH   │ │  TOXI    │ │  PHARMA  │
    │ Biologist│ │Toxicolog.│ │Pharmacol.│
    └────┬─────┘ └────┬─────┘ └────┬─────┘
         │            │            │
         └────────────┼────────────┘
                      │
                      ▼
               ┌──────────────┐
               │   EDWARD     │
               │  (MedChem)   │
               │              │
               │  Integrates  │
               │  all three   │
               │  advisories  │
               └──────────────┘
```

All three advisory agents run in parallel (they are independent). Edward receives all three advisories and produces the final score. No agent identifies the molecule by name. All reasoning is from structure, target, and indication alone.

---

## Agent 1: SALAH — Biological & Clinical Rationalist (exists, V24)

**What Salah focuses on in V25:**
- Target attrition analysis (graveyard detection: BACE, CB1, CETP)
- Mechanism validation depth (ELITE/CAUTION/TERMINATE)
- Indication-severity weighting (oncology vs chronic metabolic)
- Druggability of the target binding site

**What Salah should NOT do in V25 (clear domain boundaries):**
- Salah should NOT predict toxicology (on-target tissue damage, reactive metabolites, hERG) — that's Toxi's job
- Salah should NOT predict PK (dose, absorption, clearance, DDI) — that's Pharma's job
- Salah should NOT predict dose-mediated DILI — that's shared between Toxi (hepatotoxicity mechanism) and Pharma (dose prediction)
- Salah should focus purely on: is the biology sound? Is the target druggable? Is the mechanism validated for this indication? Will the biology sustain a durable response?

**V25 Salah output:**
```json
{
    "salah_verdict": "ELITE/CAUTION/TERMINATE",
    "biological_rationale": "Target validation depth, mechanism feasibility",
    "mechanism_validation": "Novel/Emerging/Established/Deep",
    "druggability_assessment": "Assessment of target binding site quality",
    "bio_p1": 0.0-1.0,
    "bio_p1_rationale": "P1 survival probability from biology perspective (is the mechanism safe enough to dose humans?)",
    "bio_p2": 0.0-1.0,
    "bio_p2_rationale": "P2 survival probability from biology perspective (will hitting this target produce a measurable clinical signal?)",
    "bio_p3": 0.0-1.0,
    "bio_p3_rationale": "P3 survival probability from biology perspective (is the mechanism durable and differentiated enough to win a pivotal trial?)"
}
```

**Salah's probability reasoning (all from mechanistic biology, NOT historical trial outcomes):**
- **bio_p1**: Is the mechanism inherently dangerous to dose in humans? CB1 inverse agonism modulates a system that controls mood/appetite via the endocannabinoid system — mechanism-based neuropsychiatric risk is biologically predictable. BACE inhibition removes a substrate (APP processing) required for synaptic maintenance — mechanism-based cognitive worsening is biologically predictable. Validated, well-understood mechanisms with no inherent on-mechanism danger → high P1.
- **bio_p2**: Does the biology support that modulating this target will produce a clinical signal in this disease? Evaluate: Is the target causally linked to disease pathology (genetic evidence, pathway biology)? Is the target tractable to pharmacological modulation (receptor agonism/antagonism is tractable; scaffolding protein PPIs are not)? Novel targets where the causal link is weak or purely correlative → low P2. Targets with strong genetic or mechanistic evidence of causality → high P2.
- **bio_p3**: Can the biology sustain a durable therapeutic effect at scale? Evaluate: Does the target pathway have feedback loops or compensatory mechanisms that would erode efficacy over time (e.g., receptor desensitization, pathway redundancy, homeostatic counter-regulation)? Is the mechanism fundamentally disease-modifying or merely symptomatic? Will the biological effect remain consistent across diverse patient populations (genetic polymorphisms in the target pathway)? Mechanisms prone to tolerance, tachyphylaxis, or compensatory upregulation → low P3. Direct, disease-modifying mechanisms without known escape routes → high P3.

---

## Agent 2: TOXI — Predictive Toxicologist (NEW)

### Mission
Senior Predictive Toxicologist. Evaluates the **safety liabilities** of a drug candidate based on its target biology, structural features, and indication. Does NOT care about efficacy or druggability — only about what will hurt the patient.

### Librarian Ban
Same as all agents. No molecule identification by name. Evaluate as NCE.

### Core Reasoning Framework

#### 1. On-Target Toxicity Assessment
The most important question in toxicology: **what happens when you hit the target in healthy tissue?**

- **Target tissue expression mapping**: Where is this target expressed beyond the disease tissue? If a kinase is essential for DNA damage repair in bone marrow stem cells, inhibiting it will cause myelosuppression regardless of how selective the molecule is.
- **DDR pathway targets** (ATR, ATM, CHK1, CHK2, WEE1, DNA-PK): These are essential for genome integrity in all dividing cells. On-target toxicity to bone marrow, GI epithelium, and hair follicles is **mechanistically guaranteed**. Therapeutic window depends entirely on differential sensitivity between tumor and healthy tissue.
- **Epigenetic targets** (BET, HDAC, EZH2, DOT1L) for non-oncology indications: Long-term epigenetic reprogramming of healthy cells carries unknown risks. Acceptable for short-course oncology, concerning for chronic dermatology/metabolic use.
- **Immune modulators** (JAK, BTK, S1P, IL-17): Immunosuppression is the mechanism AND the toxicity. Assess infection risk, malignancy risk, and whether the indication severity justifies chronic immunosuppression.

#### 2. Off-Target Toxicity Prediction (Structure-Based)
- **hERG/cardiac ion channels**: From structural features (basic center + lipophilic bulk)
- **Mitochondrial toxicity**: Uncouplers (lipophilic weak acids), ETC inhibitors
- **Phospholipidosis**: Cationic amphiphilic drugs (CADs) — basic amine + lipophilic domain
- **Reactive metabolite formation**: Structural alerts for bioactivation (anilines, thiophenes, furans, hydrazines)
- **Phototoxicity**: Extended conjugated systems, halogenated aromatics with UV absorption

#### 3. Therapeutic Window Assessment
- **Narrow window flags**: Target is essential in healthy tissue AND the disease mechanism requires near-complete target inhibition
- **Wide window indicators**: Target is overexpressed/mutated in disease tissue, healthy tissue has redundant pathways, or the mechanism requires only partial modulation
- **Route-dependent window**: Topical/local delivery can rescue a narrow systemic window

#### 4. Species Translation Risk (Mechanistic Reasoning Only)
Predict translational risk from **biochemical species differences**, not from knowledge of specific preclinical results:
- **CYP isoform differences**: Rodents rely heavily on CYP2C subfamily for oxidative metabolism; humans rely more on CYP3A4/2D6/2C9. A molecule metabolized primarily by CYP2C in rodents may have a completely different metabolite profile in humans → rodent-predicted toxicity may not translate (and human-specific metabolites may cause unpredicted toxicity).
- **GSH conjugation capacity**: Rodents have higher hepatic GSH turnover than humans → reactive metabolites quenched in rodent liver may overwhelm human detoxification capacity at equivalent doses.
- **Immune-mediated toxicity**: Idiosyncratic drug reactions (DRESS, SJS, DILI) are largely human-specific due to HLA polymorphism-driven immune recognition. Structural alerts for hapten formation (acyl glucuronides, quinone imines, nitroso metabolites) predict human risk that preclinical species typically do not model.
- **Cardiovascular translation**: hERG channel sequence is highly conserved across mammals, so ion channel toxicity generally translates well. However, action potential duration and QT sensitivity differ between species.

### Verdict Framework
- **CLEAN**: No significant on-target or off-target toxicity concerns. Wide therapeutic window expected.
- **MANAGEABLE**: Toxicity concerns exist but are monitorable and dose-manageable (e.g., routine LFT monitoring for mild hepatotoxicity risk, blood counts for mild myelosuppression).
- **NARROW**: Therapeutic window is narrow — on-target toxicity is mechanistically guaranteed but may be acceptable for severe disease (oncology, rare disease). Clinical success depends on dose optimization.
- **TOXIC**: Mechanism is inherently toxic to critical healthy tissues, or structural features guarantee severe off-target toxicity. High probability of clinical failure due to safety.

### Output Format
```json
{
    "toxi_verdict": "CLEAN/MANAGEABLE/NARROW/TOXIC",
    "toxi_rationale": "On-target and off-target toxicity assessment",
    "therapeutic_window": "Wide/Moderate/Narrow/Razor-thin",
    "primary_tox_concern": "The single most likely dose-limiting toxicity",
    "on_target_tox_risk": "None/Low/Moderate/High",
    "off_target_tox_risk": "None/Low/Moderate/High",
    "tox_p1": 0.0-1.0,
    "tox_p1_rationale": "P1 survival probability from toxicology perspective (will the molecule survive FIH dosing without DLTs?)",
    "tox_p2": 0.0-1.0,
    "tox_p2_rationale": "P2 survival probability from toxicology perspective (can a safe therapeutic dose be found?)",
    "tox_p3": 0.0-1.0,
    "tox_p3_rationale": "P3 survival probability from toxicology perspective (will chronic/expanded safety hold up at scale?)"
}
```

**Toxi's probability reasoning (all from mechanistic toxicology, NOT historical trial outcomes):**
- **tox_p1**: Does the structure or mechanism carry predictable acute toxicity risk? Reactive metabolite-forming motifs (furans, anilines, thiophenes) → CYP-mediated bioactivation is a known biochemical pathway → low P1. hERG pharmacophore (basic center + lipophilic bulk) → biophysical blockade of the hERG K+ channel is structurally predictable → low P1. DDR targets → DNA repair inhibition in rapidly dividing bone marrow is mechanistically guaranteed → moderate P1 (can dose conservatively but DLTs are predictable at pharmacologically active exposures). Clean structure with no reactive motifs and no on-mechanism toxicity to critical organs → high P1.
- **tox_p2**: Can a therapeutic dose be found that separates efficacy from toxicity? This is about the **mechanistic therapeutic window**: Is the target expressed at similar levels in disease tissue and critical healthy tissue (narrow window)? Does the mechanism require near-complete target inhibition (leaving no safety margin)? Are there tissue-selective delivery strategies that could widen the window (topical, local, antibody-drug conjugate)? Targets essential for genome integrity in all dividing cells (ATR, CHK1, WEE1) → the dose that kills tumor also damages marrow/GI epithelium → fundamentally narrow window → low P2. Targets overexpressed or mutated in disease tissue with redundant pathways in healthy tissue → wide window → high P2.
- **tox_p3**: **This assessment scales with intended treatment duration.** For acute/short-course therapies (anti-infectives, acute pain, acute cardiac events — days to weeks of exposure), cumulative toxicity is largely irrelevant → default high P3. For chronic therapies (metabolic, cardiovascular, autoimmune, psychiatric — months to years of exposure), evaluate mechanistically: Does the molecule or its metabolites accumulate in specific tissues (cationic amphiphiles → phospholipidosis, lipophilic compounds → adipose/liver accumulation)? Does the mechanism cause slow, cumulative damage to non-regenerating tissues (cardiomyocyte damage from kinase inhibitors is irreversible because cardiomyocytes do not regenerate; hepatocyte damage may be reversible because the liver regenerates)? Is there a predictable idiosyncratic toxicity risk from reactive metabolite–immune system interactions (structural alerts for hapten formation → immune-mediated organ damage with stochastic onset)? Chronic drugs with no tissue accumulation, no non-regenerating organ risk, and no hapten-forming motifs → high P3. Chronic drugs with cumulative damage to non-regenerating tissues or stochastic immune-mediated risk → low P3.

### What Toxi Would Have Caught
**Gartisertib (ATR kinase, oncology)**: Toxi would flag ATR as a DDR pathway kinase essential for genome integrity in all dividing cells → on-target myelosuppression mechanistically guaranteed → therapeutic window is NARROW → tox_p2 ≈ 0.25 (finding a therapeutic dose that spares healthy tissue is very hard). Even with Salah giving ELITE and bio_p2 ≈ 0.60, Edward would read Toxi's rationale ("DDR targets cause myelosuppression in all dividing cells — this is not an off-target effect, it IS the mechanism") and weight final_p2 toward Toxi's estimate. This alone would keep the score in the 55-65 range instead of 12.

---

## Agent 3: PHARMA — Clinical Pharmacologist (NEW)

### Mission
Senior Clinical Pharmacologist. Evaluates the **pharmacokinetic and pharmacodynamic feasibility** of a drug candidate. Does NOT care about target biology or structural alerts — only about whether the molecule can achieve and maintain therapeutic concentrations safely.

### Librarian Ban
Same as all agents. No molecule identification by name. Evaluate as NCE.

### Core Reasoning Framework

#### 1. Dose Prediction (Structure-Based)
From MW, lipophilicity, TPSA, and target class, estimate the likely clinical dose:
- **Low dose (<10 mg)**: High potency targets (GPCRs with sub-nM affinity, nuclear receptors), low MW, favorable oral absorption
- **Moderate dose (10-100 mg)**: Standard enzymes, kinases with nM affinity, reasonable oral PK
- **High dose (100-500 mg)**: Targets requiring high occupancy (metabolic enzymes, transporters), high MW reducing oral absorption
- **Very high dose (>500 mg)**: Peptides requiring near-complete target saturation, poorly absorbed molecules requiring brute-force dosing

#### 2. Absorption & Bioavailability Assessment
- **Oral feasibility**: MW, cLogP, TPSA, HBD, solubility estimate, P-gp substrate risk
- **Peptide/macrocycle PK**: Molecules with ≥3 amide bonds — predict parenteral requirement unless chameleonic properties (intramolecular H-bonding, N-methylation) are present
- **Route-of-administration match**: Does the likely PK profile match the intended route? A molecule with TPSA >140 and MW >600 is not an oral drug.

#### 3. Metabolic Clearance Prediction
- **CYP-dependent clearance**: Lipophilic molecules (cLogP >3) with multiple oxidizable sites → high hepatic extraction → short half-life → need for BID/TID dosing or modified release
- **Non-CYP clearance**: Highly polar molecules cleared renally → dose adjustment in renal impairment → compliance concerns
- **Prodrug potential**: Does the structure suggest intentional prodrug design (ester prodrugs, phosphate prodrugs)?

#### 4. Drug-Drug Interaction (DDI) Risk
- **CYP inhibition risk**: Structure contains known CYP inhibitor motifs (imidazoles for CYP3A4, methylenedioxyphenyl for CYP2D6)
- **CYP induction risk**: PXR/CAR activating scaffolds
- **Transporter interactions**: P-gp, BCRP, OATP substrate/inhibitor potential from structural features

#### 5. Therapeutic Index Estimation
Combine dose prediction + clearance + DDI risk to estimate whether steady-state plasma concentrations can be maintained within the therapeutic window:
- **Favorable**: Low dose, long half-life, wide Cmax/Cmin ratio, low DDI risk
- **Challenging**: High dose, short half-life, narrow Cmax/Cmin, significant DDI concerns
- **Unfavorable**: Very high dose, extensive first-pass, multiple DDI liabilities, variable absorption

### Verdict Framework
- **FAVORABLE**: Good oral PK predicted, low dose, manageable DDI, comfortable therapeutic index
- **ADEQUATE**: Some PK challenges but workable with standard formulation/dosing strategies
- **CHALLENGING**: Significant PK hurdles — high dose, poor absorption, short half-life, or DDI concerns that complicate clinical development
- **IMPRACTICAL**: PK profile makes clinical development extremely difficult — brute-force dosing required, unmanageable DDI, or route mismatch with indication

### Output Format
```json
{
    "pharma_verdict": "FAVORABLE/ADEQUATE/CHALLENGING/IMPRACTICAL",
    "pharma_rationale": "PK/PD feasibility assessment",
    "predicted_dose_range": "Low/Moderate/High/Very High",
    "oral_feasibility": "Good/Moderate/Poor/Non-oral",
    "ddi_risk": "Low/Moderate/High",
    "half_life_estimate": "Short (<4h)/Moderate (4-12h)/Long (>12h)",
    "pk_p1": 0.0-1.0,
    "pk_p1_rationale": "P1 survival probability from PK perspective (can therapeutic exposure be achieved safely in FIH?)",
    "pk_p2": 0.0-1.0,
    "pk_p2_rationale": "P2 survival probability from PK perspective (can PK support dose-finding and sustained target engagement?)",
    "pk_p3": 0.0-1.0,
    "pk_p3_rationale": "P3 survival probability from PK perspective (will PK variability, DDI, and compliance hold up at scale?)"
}
```

**Pharma's probability reasoning (indication-aware ADME assessment):**

Pharma MUST first identify the **target compartment** from the indication and assess ADME properties accordingly. The same molecule can be PK-favorable for one indication and PK-impractical for another.

**Target compartment inference from indication:**
- **CNS (psychiatry, neurology, pain)**: Requires BBB penetration. Evaluate: MW <450, TPSA <90 Å², cLogP 2–4.5, HBD ≤1, no P-gp substrate motifs. A molecule with TPSA >90 or HBD >2 is likely P-gp effluxed and will not achieve brain exposure → low PK probabilities regardless of peripheral PK.
- **Peripheral systemic (metabolic, cardiovascular, autoimmune)**: Standard oral PK rules. Evaluate: Lipinski compliance, solubility, CYP metabolism, half-life.
- **Oncology (solid tumor)**: Tumor penetration matters — high MW or highly polar molecules may not penetrate solid tumor interstitium. Evaluate: tumor blood flow dependency, EPR effect potential, efflux transporter expression in tumor.
- **Anti-infective**: Must achieve concentration at infection site. Pulmonary infections need lung tissue penetration. UTI drugs need renal/urinary concentration. Intracellular pathogens need cell membrane penetration.
- **Dermatology (topical)**: Needs skin penetration (moderate lipophilicity, MW <500) but minimal systemic absorption. Oral PK is irrelevant.
- **Ophthalmology**: Needs corneal permeability for anterior segment, or vitreal stability for posterior segment. Systemic PK is irrelevant.
- **Rare disease (parenteral)**: If the molecule is clearly a peptide or macrocycle, oral PK is irrelevant — evaluate parenteral PK (half-life, immunogenicity, injection site tolerability, distribution to target tissue).

- **pk_p1**: Can therapeutic exposure be achieved in the **target compartment** safely in FIH? A CNS drug with TPSA >120 → cannot cross BBB → pk_p1 is low regardless of plasma levels. A topical drug with poor skin permeability → pk_p1 is low. A peptide intended for oral delivery without clear prodrug or permeation-enhancer strategy → pk_p1 is low. Molecule well-matched to its intended compartment → high pk_p1.
- **pk_p2**: Can PK support sustained target engagement in the **target compartment** at a tolerable dose? Evaluate: Is the predicted dose high enough to saturate metabolic clearance (non-linear PK risk)? Is the half-life appropriate for the dosing frequency the indication demands (chronic QD vs acute IV)? Will the molecule distribute adequately to the disease tissue at achievable plasma concentrations? High DDI risk or variable absorption that would confound dose-finding → low pk_p2.
- **pk_p3**: Will real-world PK hold up? Evaluate based on **treatment duration and patient population**: Chronic therapy requiring years of compliance → short half-life (TID dosing), significant food effects, or narrow therapeutic index from PK variability all reduce pk_p3. Significant CYP DDI risk in a polypharmacy population (e.g., elderly cardiovascular patients on multiple drugs) → low pk_p3. Acute/short-course therapy with supervised dosing → high pk_p3. Robust QD oral PK with no food effects and low DDI → high pk_p3.

---

## Probability Calibration Anchors (All Agents)

All agents must calibrate their per-phase probabilities against **industry base rates** to ensure their outputs are on a common scale. These are not targets to hit — they are anchors so that "0.5" means the same thing across all agents.

| Phase | Industry Base Rate | What it means |
|---|---|---|
| P1 (FIH → Phase 2) | ~0.65 | About 2 in 3 molecules that enter FIH survive to Phase 2 |
| P2 (Phase 2 → Phase 3) | ~0.30 | About 1 in 3 molecules that enter Phase 2 advance |
| P3 (Phase 3 → Approval) | ~0.58 | About 3 in 5 molecules that enter Phase 3 get approved |

**How to use anchors:**
- A probability of **0.50** for any phase means "roughly average prospects — no strong reason to be optimistic or pessimistic from my domain."
- Deviations from anchor should be **justified by specific mechanistic reasoning**. Saying tox_p1 = 0.30 means "this molecule is meaningfully more dangerous than average in FIH, and here's why."
- Each agent assesses **only their domain's contribution** to phase survival. Salah's bio_p2 = 0.80 means "the biology strongly supports a clinical signal" — it does NOT account for PK or tox concerns (those are Pharma's and Toxi's job).
- When an agent has no specific concern or advantage for a phase, output a value near the base rate, not 0.5 arbitrarily.

---

## Verdicts vs Probabilities — Role Clarification

Each agent outputs BOTH a categorical verdict AND per-phase probabilities. These serve different purposes:

- **Verdicts** (ELITE/CAUTION/TERMINATE, CLEAN/MANAGEABLE/NARROW/TOXIC, FAVORABLE/ADEQUATE/CHALLENGING/IMPRACTICAL) are **summary signals** for Edward's integration. They communicate the overall posture of each advisor at a glance.
- **Probabilities** (bio_p1/p2/p3, tox_p1/p2/p3, pk_p1/p2/p3) are **granular, phase-specific assessments** that Edward uses for quantitative reasoning.

**The verdict must be consistent with the probabilities.** If Toxi gives tox_p2 = 0.25, the verdict should be NARROW or TOXIC, not MANAGEABLE. If all three probabilities are high, the verdict should be CLEAN or FAVORABLE, not CAUTION. The server-side pipeline can validate this consistency and flag mismatches.

---

## Edward V25 — Two-Pass Probability Integration

Edward operates in **two passes** to prevent advisory contamination of his structural assessment:

### Pass 1: Blind Structural Assessment
Edward receives ONLY the SMILES, target class, and indication — **no advisory data**. He performs his standard V24 structural critique and produces his own per-phase probabilities:

```
Pass 1 Input:
  - SMILES
  - Target Class
  - Indication
  (NO advisory data)

Pass 1 Output:
  - chem_p1, chem_p2, chem_p3 + rationales
  - metabolic_stability_estimate
  - potential_toxic_fragments
  - structural_assessment (text summary of MedChem critique)
```

This ensures Edward's chemistry-based assessment is unbiased by the advisors.

### Pass 2: Advisory Integration
Edward receives his own Pass 1 output PLUS all three advisories. He now synthesizes everything into final consensus probabilities and the Edward Score:

```
Pass 2 Input:
  - His own Pass 1 output (chem_p1/p2/p3, structural_assessment)
  - Salah Advisory: verdict, rationale, bio_p1, bio_p2, bio_p3 + rationales
  - Toxi Advisory:  verdict, rationale, tox_p1, tox_p2, tox_p3 + rationales
  - Pharma Advisory: verdict, rationale, pk_p1, pk_p2, pk_p3 + rationales

Pass 2 Output:
  - final_p1, final_p2, final_p3 + consensus rationales
  - edward_score (derived from TCSP, see mapping below)
  - final_rationale (synthesis acknowledging each advisor's key concern)
```

### Edward's Final Output (V25)
```json
{
    "edward_score": 1-100,
    "rational": "Synthesis of structural assessment + all three advisories. Explicit acknowledgment of each advisor's key concern and how it affected the final score.",
    "metabolic_stability_estimate": "High/Medium/Low",
    "potential_toxic_fragments": "List specific moieties",
    "structural_assessment": "Pass 1 blind MedChem critique (no advisory influence)",
    "chem_p1": float, "chem_p1_rationale": "Edward's own structural P1 (from Pass 1, blind)",
    "chem_p2": float, "chem_p2_rationale": "Edward's own structural P2 (from Pass 1, blind)",
    "chem_p3": float, "chem_p3_rationale": "Edward's own structural P3 (from Pass 1, blind)",
    "final_p1": float, "final_p1_rationale": "Consensus P1 integrating bio_p1, tox_p1, pk_p1, chem_p1",
    "final_p2": float, "final_p2_rationale": "Consensus P2 integrating bio_p2, tox_p2, pk_p2, chem_p2",
    "final_p3": float, "final_p3_rationale": "Consensus P3 integrating bio_p3, tox_p3, pk_p3, chem_p3",
    "tcsp": float
}
```

The **TCSP** (Total Clinical Success Probability) = final_p1 × final_p2 × final_p3, recalculated server-side for arithmetic accuracy.

### Edward Score ↔ TCSP Mapping

The Edward Score is **deterministically derived** from the TCSP. This eliminates the problem of the LLM's "gut feel" score diverging from the mathematically grounded probability:

```
edward_score = round(100 × (1 - TCSP / TCSP_max))
```

Where **TCSP_max** = base_p1 × base_p2 × base_p3 = 0.65 × 0.30 × 0.58 = **0.113 (11.3%)**. This is the industry-average TCSP for a molecule entering Phase 1.

| TCSP | Edward Score | Interpretation |
|---|---|---|
| ≥0.113 (≥11.3%) | 1–10 | Better than industry average — elite candidate |
| 0.08–0.113 | 10–30 | Good prospects, above average |
| 0.04–0.08 | 30–50 | Average to slightly below — real concerns present |
| 0.02–0.04 | 50–70 | Below average — significant liabilities |
| 0.005–0.02 | 70–85 | Poor prospects — multiple serious concerns |
| <0.005 | 85–100 | Near-certain failure — graveyard territory |

**The mapping is computed server-side**, not by the LLM. Edward's Pass 2 output includes final_p1/p2/p3 and a rationale, but the Edward Score integer is calculated from TCSP by the pipeline. This prevents arithmetic errors and ensures score-probability consistency.

**Edward still provides his qualitative assessment** in the rationale — the score is just no longer a separate judgment call.

### Integration Principles for Edward (Pass 2)
1. **Read the rationales, not just the numbers.** A tox_p2 of 0.3 with rationale "DDR target causes myelosuppression in all dividing cells" carries different weight than tox_p2 of 0.3 with rationale "mild GI irritation expected."
2. **Do not double-count.** If Toxi and Pharma both flag "high dose → liver burden," this is one concern, not two. If Salah flags "novel target" and Toxi flags "unknown on-target tox," these ARE distinct (biological feasibility ≠ safety).
3. **The most pessimistic advisor gets the floor.** If three advisors say P2 = 0.6 and one says P2 = 0.15 with a compelling mechanistic rationale, Edward should not average to 0.49 — he should understand why one advisor is deeply concerned and decide if that concern is valid. If the rationale is mechanistically sound, weight heavily toward that advisor.
4. **Edward can override advisors with explicit justification.** If Pharma says pk_p1 = 0.3 because "MW >500 means poor oral absorption" but the indication is dermatology (topical), Edward can recognize that oral PK is irrelevant and set final_p1 higher. The rationale MUST explain the override: "Overriding Pharma pk_p1=0.3 because [specific reason]."
5. **Acknowledge correlated optimism.** If all three advisors and Edward himself are optimistic, explicitly ask: "Is there a failure mode none of us are modeling?" Common blind spots include: manufacturing/formulation difficulty, biomarker-to-clinical-outcome disconnect, regulatory hurdles, and patient population heterogeneity. If Edward identifies a correlated blind spot, he should note it in the rationale and moderate the final probabilities accordingly. This does not require domain expertise — it is a metacognitive check.

---

## Expected Impact on Known Failure Cases

### Gartisertib (ATR kinase, oncology) — the case that motivated V25
| Agent | P1 | P2 | P3 | Reasoning |
|---|---|---|---|---|
| Salah (bio) | 0.85 | 0.60 | 0.40 | Kinases in oncology are validated. Mechanism is sound. |
| Toxi (tox) | 0.50 | 0.25 | 0.15 | DDR target → on-target myelosuppression in all dividing cells. Therapeutic window is NARROW. P2 low because finding a dose that kills tumor but spares marrow is extremely hard. |
| Pharma (pk) | 0.80 | 0.50 | 0.40 | Moderate dose, reasonable oral PK, standard kinase DDI profile. |
| Edward (chem) | 0.85 | 0.60 | 0.50 | Clean structure for a kinase inhibitor. |
| **V25 consensus** | ~0.65 | ~0.30 | ~0.20 | Toxi's P2 concern dominates — myelosuppression makes dose-finding treacherous. |

**V25 TCSP** ≈ 0.65 × 0.30 × 0.20 = **0.039 (3.9%)** → Edward Score ~55-65
**V24 TCSP** was 18.7% → Edward Score 12. The Toxi advisory alone would have corrected this.

### Other molecules
| Molecule | V24 Score | V25 Expected | Key V25 Change |
|---|---|---|---|
| Monlunabant (CB1 inverse) | 92 | ~90-95 | Salah: bio_p1=0.2 (graveyard). Toxi: tox_p1=0.3 (neuropsych). Both flag independently → stays very high. |
| Simufilam (scaffold PPI) | 82 | ~80-85 | Salah: bio_p2=0.1 (undruggable PPI). Pharma: pk_p2=0.3 (high dose needed). Edward keeps it high. |
| Elamipretide (peptide, rare) | 65 | ~50-55 | Pharma: pk_p1=0.5 (parenteral, poor oral). But Toxi: tox_p2=0.7 (low systemic tox for peptide). Rare disease severity weighting helps. |
| Mirdametinib (MEK, oncology) | 18 | ~15-25 | All three advisors supportive. Salah ELITE, Toxi MANAGEABLE, Pharma ADEQUATE. Stays low. |

---

## Implementation Notes

### Parallelism & Execution Flow
```
Step 1 (parallel):  Salah + Toxi + Pharma  (3 concurrent LLM calls)
Step 2 (sequential): Edward Pass 1          (blind structural assessment, 1 LLM call)
Step 3 (sequential): Edward Pass 2          (advisory integration, 1 LLM call)
```

Steps 1 and 2 can run in parallel (Edward Pass 1 doesn't need advisory data). Step 3 requires both Step 1 and Step 2 to complete.

Total latency = max(Step 1, Step 2) + Step 3 ≈ 1 advisory call + 1 Edward call ≈ same as V24.

### Cost
3 advisory calls + 2 Edward calls = 5 LLM calls per molecule (vs 2 in V24). Cost ~2.5× but latency stays similar due to parallelism.

### Agent Prompt Files
```
Agents/
├── edward-medchem-rationalist/INSTRUCTIONS.md     (update for V25 integration)
├── salah-biological-rationalist/INSTRUCTIONS.md   (slim down, remove tox/PK)
├── toxi-predictive-toxicologist/INSTRUCTIONS.md   (NEW)
└── pharma-clinical-pharmacologist/INSTRUCTIONS.md (NEW)
```

### Run Script Changes
```python
# V25: parallel advisory calls
salah_future = executor.submit(run_salah, smiles, target, indication)
toxi_future = executor.submit(run_toxi, smiles, target, indication)
pharma_future = executor.submit(run_pharma, smiles, target, indication)

salah_data = salah_future.result()
toxi_data = toxi_future.result()
pharma_data = pharma_future.result()

# Edward integrates all three
edward_data = run_edward(smiles, target, indication, salah_data, toxi_data, pharma_data)
```

### Validation Strategy

#### Phase A: Individual Agent Calibration (before full pipeline testing)
Run each advisory agent **solo** on the 2025 dataset (N=29) and test whether their probabilities independently correlate with outcomes:

1. **Salah solo calibration**: For each molecule, compute bio_TCSP = bio_p1 × bio_p2 × bio_p3. Check if bio_TCSP discriminates approved vs failed (AUC > 0.55 means Salah adds signal). If Salah gives ELITE to >80% of molecules, the ELITE criteria are too loose. If ELITE <5%, too strict. Target: 20-40% ELITE on a balanced dataset.
2. **Toxi solo calibration**: Compute tox_TCSP. Check if NARROW/TOXIC verdicts are enriched in failures. If Toxi gives NARROW to >60% of molecules, it is systematically pessimistic — tighten the NARROW criteria. Target: NARROW/TOXIC on <30% of molecules.
3. **Pharma solo calibration**: Compute pk_TCSP. Check if CHALLENGING/IMPRACTICAL verdicts correlate with actual failures. If Pharma flags every MW>400 molecule, the dose prediction rules are too aggressive.

**Recalibrate individual agents before combining.** If an agent's solo AUC is <0.52 (below random noise), its reasoning framework needs revision — do not just tune thresholds.

#### Phase B: Full Pipeline Testing
4. Run V25 on the 2025 dataset (N=29) — verify Gartisertib moves to 40-60 range while approved drugs stay low
5. Run V25 on Modern (N=219) — verify AUC does not regress from V24
6. Run V25 on Legacy (N=175) — verify no catastrophic regression
7. **Score-TCSP consistency check**: Since Edward Score is now derived from TCSP server-side, verify the mapping produces sensible distributions. If >50% of molecules score 1-10 or >50% score 85-100, the TCSP_max or mapping function needs adjustment.
8. **Advisory disagreement analysis**: For each molecule, compute the variance across bio_pX, tox_pX, pk_pX, chem_pX for each phase. High-variance molecules (agents strongly disagree) are the most interesting — manually review whether Edward's consensus rationale correctly resolves the disagreement.

#### Phase C: Regression & Robustness
9. **Run V25 on molecules where V24 was correct** — verify the new agents don't break what already works. If V24 scored a drug correctly at 18, V25 should not inflate it to 50 just because Toxi adds a mild concern.
10. **Sensitivity test**: For 5-10 molecules, perturb the indication (e.g., change "Oncology" to "Metabolic") and verify that Pharma and Toxi probabilities shift appropriately (compartment-aware reasoning should change, structural assessment should not).

---

## Resolved Design Decisions

1. **All agents see SMILES + target + indication.** Toxi needs SMILES for off-target structural alert prediction (reactive metabolites, hERG pharmacophore). Pharma needs SMILES for MW/cLogP/TPSA-based dose and DDI prediction. Target-only reasoning is insufficient for both.

2. **Over-penalization is handled by Edward's integration principles** (do not double-count, read rationales not just numbers). The two-pass architecture further protects against contamination — Edward's own structural assessment is independent.

3. **Domain boundaries are clear:**
   - **Salah**: Is the target druggable? Is the mechanism biologically validated for this indication? Will the biology sustain a durable response? (NO toxicology, NO PK)
   - **Toxi**: What damage will hitting this target cause to healthy tissue? What off-target toxicity does the structure predict? What is the therapeutic window? (NO efficacy assessment, NO PK)
   - **Pharma**: Can the molecule reach the target compartment? At what dose? With what DDI/compliance profile? (NO efficacy assessment, NO toxicology)
   - **Edward**: Structural chemistry critique + synthesis of all three advisory perspectives into final consensus.

4. **Verdicts and probabilities coexist** — verdicts are summary signals, probabilities are granular. Consistency is validated server-side.

---

## Known Limitations & Blind Spots

Even with four agents, some failure modes remain outside the pipeline's scope:

1. **Manufacturing & formulation risk**: Polymorphism, crystallization difficulty, API stability, scale-up challenges. No agent models this. Impact: a molecule with perfect biology/tox/PK/chemistry can still fail if it can't be manufactured reproducibly. This is a rare failure mode in clinical development but common in CMC.

2. **Biomarker-to-clinical-outcome disconnect**: Salah assesses whether modulating the target will produce a biological signal, but not whether that signal translates to a clinically meaningful endpoint. A biomarker responder in Phase 2 can still fail Phase 3 if the biomarker doesn't predict outcomes (e.g., LDL reduction without cardiovascular event reduction).

3. **Trial design & regulatory risk**: The pipeline assumes a well-designed trial. Poorly chosen endpoints, wrong patient population, underpowered studies, or regulatory disagreements can kill a good drug. No agent models this.

4. **Commercial & competitive risk**: A molecule can succeed clinically but fail commercially if a competitor reaches market first or the price point is unsustainable. Outside scope.

5. **Correlated agent optimism**: When all three advisors agree a molecule is excellent, the pipeline has no independent check. Edward's Pass 2 includes a metacognitive prompt ("Is there a failure mode none of us are modeling?") but this relies on the LLM's self-awareness, which is imperfect. The advisory disagreement analysis in validation (Phase B, step 8) helps detect molecules where unanimous optimism may be overconfident.
