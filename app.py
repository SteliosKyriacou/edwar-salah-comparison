import streamlit as st
import json
import os
import io
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from rdkit import Chem
from rdkit.Chem import Draw, AllChem
from rdkit.Chem.Draw import rdMolDraw2D
from PIL import Image

# ── Config ──────────────────────────────────────────────────────────────────
BASE = os.path.dirname(__file__)
load_dotenv(os.path.join(BASE, ".env"))

st.set_page_config(
    page_title="Will Your Drug Succeed in the Clinic?",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .main-header {
        text-align: center;
        padding: 1.5rem 0 0.5rem 0;
    }
    .main-header h1 {
        font-size: 2.4rem;
        font-weight: 700;
        background: linear-gradient(135deg, #4A90E2, #7B68EE, #E74C3C);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .main-header p {
        font-size: 1.05rem;
        color: #888;
        margin-top: 0;
    }

    .privacy-banner {
        background: linear-gradient(90deg, #1a1a2e, #16213e);
        border: 1px solid #2a2a4a;
        border-radius: 8px;
        padding: 0.7rem 1.2rem;
        text-align: center;
        margin-bottom: 1.5rem;
    }
    .privacy-banner span {
        color: #7B68EE;
        font-weight: 600;
    }
    .privacy-banner p {
        color: #aaa;
        font-size: 0.85rem;
        margin: 0;
    }

    .score-card {
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        border: 1px solid #333;
    }
    .score-card h2 {
        font-size: 3.5rem;
        font-weight: 700;
        margin: 0;
    }
    .score-card p {
        font-size: 0.9rem;
        color: #aaa;
        margin-top: 0.3rem;
    }

    .score-elite { background: linear-gradient(135deg, #0d3b0d, #1a5c1a); border-color: #27AE60; }
    .score-elite h2 { color: #2ECC71; }
    .score-caution { background: linear-gradient(135deg, #3b3b0d, #5c5c1a); border-color: #F1C40F; }
    .score-caution h2 { color: #F1C40F; }
    .score-danger { background: linear-gradient(135deg, #3b0d0d, #5c1a1a); border-color: #E74C3C; }
    .score-danger h2 { color: #E74C3C; }

    .verdict-badge {
        display: inline-block;
        padding: 0.5rem 1.5rem;
        border-radius: 20px;
        font-weight: 700;
        font-size: 1.1rem;
        letter-spacing: 0.05em;
    }
    .verdict-elite { background: #27AE60; color: white; }
    .verdict-caution { background: #F39C12; color: white; }
    .verdict-terminate { background: #E74C3C; color: white; }

    .phase-container {
        background: #1a1a2e;
        border: 1px solid #2a2a4a;
        border-radius: 10px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.5rem;
    }
    .phase-label {
        font-weight: 600;
        font-size: 0.9rem;
        color: #ccc;
    }
    .phase-value {
        font-weight: 700;
        font-size: 1.4rem;
    }

    .info-card {
        background: #1a1a2e;
        border: 1px solid #2a2a4a;
        border-radius: 10px;
        padding: 1rem 1.2rem;
    }
    .info-card h4 {
        color: #7B68EE;
        margin-bottom: 0.5rem;
    }

    .stExpander {
        border: 1px solid #2a2a4a !important;
        border-radius: 10px !important;
    }

    div[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f0f23, #1a1a2e);
    }

    .sidebar-header {
        text-align: center;
        padding: 1rem 0;
    }
    .sidebar-header h3 {
        color: #7B68EE;
        font-weight: 600;
    }

    div[data-testid="stForm"] {
        border: 1px solid #2a2a4a;
        border-radius: 12px;
        padding: 1rem;
    }
</style>
""", unsafe_allow_html=True)


# ── Load Agent Prompts ──────────────────────────────────────────────────────
@st.cache_resource
def load_prompts():
    with open(os.path.join(BASE, "Agents/edward-medchem-rationalist/INSTRUCTIONS.md")) as f:
        edward = f.read()
    with open(os.path.join(BASE, "Agents/salah-biological-rationalist/INSTRUCTIONS.md")) as f:
        salah = f.read()
    return edward, salah


@st.cache_resource
def get_llm():
    return ChatGoogleGenerativeAI(model="gemini-3-pro-preview", temperature=0.0)


EDWARD_PROMPT, SALAH_PROMPT = load_prompts()
llm = get_llm()


# ── Audit Functions ─────────────────────────────────────────────────────────
def parse_json_response(content):
    if isinstance(content, list):
        content = "".join(
            [str(c.get('text', '')) if isinstance(c, dict) else str(c) for c in content]
        )
    clean = content.replace("```json", "").replace("```", "").strip()
    start = clean.find('{')
    end = clean.rfind('}') + 1
    return json.loads(clean[start:end])


def get_fragment_smarts(fragment_text, smiles):
    """Ask the LLM to convert toxic fragment descriptions into SMARTS that match the molecule."""
    prompt = f"""Given this molecule SMILES: {smiles}

And these toxic fragment descriptions: {fragment_text}

Return a JSON array of objects, one per fragment. Each object must have:
- "name": the fragment name (short label)
- "smarts": a valid SMARTS pattern that matches the toxic substructure in this specific molecule

Rules:
- The SMARTS MUST match a substructure in the given SMILES. Test mentally before returning.
- Use simple, robust SMARTS (prefer atom-by-atom patterns over complex recursive ones).
- If a fragment is vague (e.g., "lipophilic core"), skip it and do not include it.
- Return ONLY the JSON array, nothing else.

Example output:
[{{"name": "Thiophene", "smarts": "c1ccsc1"}}, {{"name": "Dimethylamine", "smarts": "CN(C)"}}]"""

    try:
        resp = llm.invoke([HumanMessage(content=prompt)])
        content = resp.content
        if isinstance(content, list):
            content = "".join(
                [str(c.get('text', '')) if isinstance(c, dict) else str(c) for c in content]
            )
        clean = content.replace("```json", "").replace("```", "").strip()
        start = clean.find('[')
        end = clean.rfind(']') + 1
        return json.loads(clean[start:end])
    except Exception:
        return []


def draw_molecule_with_highlights(smiles, fragment_smarts_list):
    """Draw the molecule with toxic fragments highlighted in red/orange."""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None, []

    AllChem.Compute2DCoords(mol)

    highlight_atoms = set()
    highlight_bonds = set()
    fragment_matches = []

    colors_atoms = {}
    colors_bonds = {}

    palette = [
        (0.91, 0.30, 0.24, 0.45),  # red
        (0.95, 0.61, 0.07, 0.45),  # orange
        (0.56, 0.27, 0.68, 0.45),  # purple
        (0.20, 0.60, 0.86, 0.45),  # blue
    ]

    for idx, frag in enumerate(fragment_smarts_list):
        smarts = frag.get("smarts", "")
        name = frag.get("name", "Unknown")
        if not smarts:
            continue

        pattern = Chem.MolFromSmarts(smarts)
        if pattern is None:
            continue

        matches = mol.GetSubstructMatches(pattern)
        if not matches:
            continue

        color = palette[idx % len(palette)]
        matched_atoms = set()
        for match in matches:
            for atom_idx in match:
                highlight_atoms.add(atom_idx)
                colors_atoms[atom_idx] = color
                matched_atoms.add(atom_idx)

            # Highlight bonds between matched atoms
            for i, ai in enumerate(match):
                for j, aj in enumerate(match):
                    if i < j:
                        bond = mol.GetBondBetweenAtoms(ai, aj)
                        if bond:
                            bond_idx = bond.GetIdx()
                            highlight_bonds.add(bond_idx)
                            colors_bonds[bond_idx] = color

        fragment_matches.append({"name": name, "atom_count": len(matched_atoms), "color": color})

    # Draw
    drawer = rdMolDraw2D.MolDraw2DCairo(700, 450)
    opts = drawer.drawOptions()
    opts.bondLineWidth = 2.0
    opts.padding = 0.15
    opts.backgroundColour = (0.06, 0.06, 0.14, 1.0)  # dark background
    opts.setAtomColour((-1, (0.85, 0.85, 0.85)))  # default atom color light gray

    if highlight_atoms:
        drawer.DrawMolecule(
            mol,
            highlightAtoms=list(highlight_atoms),
            highlightBonds=list(highlight_bonds),
            highlightAtomColors=colors_atoms,
            highlightBondColors=colors_bonds,
        )
    else:
        drawer.DrawMolecule(mol)

    drawer.FinishDrawing()
    png_data = drawer.GetDrawingText()
    img = Image.open(io.BytesIO(png_data))

    return img, fragment_matches


def run_salah(smiles, target, indication, auxiliary=""):
    prompt = f"Evaluate the biological risk: Target {target}, Indication {indication} for molecule {smiles}."
    if auxiliary:
        prompt += f"\n\nAdditional context from the user: {auxiliary}"
    resp = llm.invoke([SystemMessage(content=SALAH_PROMPT), HumanMessage(content=prompt)])
    return parse_json_response(resp.content)


def run_edward(smiles, target, indication, salah_data, auxiliary=""):
    prompt = f"""
Molecule SMILES: {smiles}
Target Class: {target}
Indication: {indication}

BIO-ADVISORY FROM SALAH (Biological/Clinical Expert):
Verdict: {salah_data['salah_verdict']}
Biological Rationale: {salah_data['biological_rationale']}
Penalty for Historical Target Stigma: {salah_data['target_stigma_penalty']} points

TASK: Provide your final MedChem audit as Edward. Integrate the Biological Advisory above into your rationale and final Edward Score.
"""
    if auxiliary:
        prompt += f"\n\nAdditional context from the user: {auxiliary}"
    resp = llm.invoke([SystemMessage(content=EDWARD_PROMPT), HumanMessage(content=prompt)])
    return parse_json_response(resp.content)


# ── Header ──────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>Will Your Drug Succeed in the Clinic?</h1>
    <p>Dual-Agent AI Critique: Medicinal Chemistry + Clinical Biology</p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="privacy-banner">
    <p><span>Privacy First</span> &mdash; Your molecular data is never stored on our servers. We process your query in real-time and immediately discard all inputs and outputs. Zero data retention.</p>
</div>
""", unsafe_allow_html=True)


# ── Sidebar: Input Form ────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sidebar-header">
        <h3>Molecule Submission</h3>
    </div>
    """, unsafe_allow_html=True)

    with st.form("molecule_form"):
        smiles = st.text_input(
            "SMILES *",
            placeholder="e.g. CN(C)CCCC1(C2=C(CO1)C=C(C=C2)C#N)C3=CC=C(C=C3)F",
            help="Enter the SMILES string of your molecule."
        )
        target = st.text_input(
            "Target Class *",
            placeholder="e.g. SSRI, BACE1, PD-1, EGFR",
            help="The pharmacological target class."
        )
        indication = st.text_input(
            "Indication / Therapeutic Area *",
            placeholder="e.g. CNS, Oncology, Cardiovascular",
            help="The broad therapeutic area or indication."
        )
        auxiliary = st.text_area(
            "Auxiliary Notes (optional)",
            placeholder="Any additional context: dose expectations, known liabilities, specific concerns...",
            help="Optional free-text that both agents will consider.",
            height=100,
        )

        submitted = st.form_submit_button("Analyze Molecule", type="primary", use_container_width=True)

    st.markdown("---")
    st.markdown("""
    **Powered by**
    - **Edward** — MedChem Rationalist
    - **Salah** — Biological Rationalist
    - Gemini 3 Pro via Google AI

    *Edward x Salah v22 Coordinated Pipeline*
    """)


# ── Main Content ────────────────────────────────────────────────────────────
if submitted:
    if not smiles or not target or not indication:
        st.error("Please fill in all required fields (SMILES, Target, Indication).")
        st.stop()

    # Run the coordinated audit
    col_status = st.empty()

    with st.spinner(""):
        # Step 1: Salah
        col_status.info("Step 1/2 — Salah is evaluating biological & clinical risk...")
        try:
            salah_data = run_salah(smiles, target, indication, auxiliary)
        except Exception as e:
            st.error(f"Salah encountered an error: {e}")
            st.stop()

        # Step 2: Edward
        col_status.info("Step 2/2 — Edward is performing the structural MedChem critique...")
        try:
            edward_data = run_edward(smiles, target, indication, salah_data, auxiliary)
        except Exception as e:
            st.error(f"Edward encountered an error: {e}")
            st.stop()

        col_status.empty()

    # ── Results ─────────────────────────────────────────────────────────
    st.markdown("---")

    score = edward_data.get("edward_score", 50)
    verdict = salah_data.get("salah_verdict", "CAUTION")

    # Score class
    if score <= 30:
        score_class = "score-elite"
        score_label = "Elite Candidate"
    elif score <= 60:
        score_class = "score-caution"
        score_label = "Proceed with Caution"
    else:
        score_class = "score-danger"
        score_label = "High Risk"

    # Verdict class
    verdict_class = {
        "ELITE": "verdict-elite",
        "CAUTION": "verdict-caution",
        "TERMINATE": "verdict-terminate",
    }.get(verdict, "verdict-caution")

    # ── Score + Verdict Row ─────────────────────────────────────────────
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        st.markdown(f"""
        <div class="score-card {score_class}">
            <p>EDWARD SCORE</p>
            <h2>{score}</h2>
            <p>{score_label}</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="score-card" style="background: #1a1a2e; border-color: #2a2a4a;">
            <p>SALAH VERDICT</p>
            <div style="margin: 1rem 0;">
                <span class="verdict-badge {verdict_class}">{verdict}</span>
            </div>
            <p>{salah_data.get('clinical_attrition_risk', 'N/A')} Attrition Risk</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        tcsp = edward_data.get("tcsp", 0)
        tcsp_pct = tcsp * 100 if isinstance(tcsp, float) and tcsp <= 1 else tcsp
        tcsp_color = "#2ECC71" if tcsp_pct >= 50 else "#F1C40F" if tcsp_pct >= 20 else "#E74C3C"
        st.markdown(f"""
        <div class="score-card" style="background: #1a1a2e; border-color: #2a2a4a;">
            <p>TOTAL CLINICAL SUCCESS</p>
            <h2 style="color: {tcsp_color};">{tcsp_pct:.1f}%</h2>
            <p>Total Clinical Success Probability</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Phase Probabilities ─────────────────────────────────────────────
    st.subheader("Clinical Phase Probabilities")
    p1 = edward_data.get("p1_prob", 0)
    p2 = edward_data.get("p2_prob", 0)
    p3 = edward_data.get("p3_prob", 0)

    pc1, pc2, pc3 = st.columns(3)
    for col, phase, prob, rationale_key, label in [
        (pc1, "Phase 1 (Safety)", p1, "p1_rationale", "First-in-Human Safety"),
        (pc2, "Phase 2 (Efficacy)", p2, "p2_rationale", "Target Engagement & ADME"),
        (pc3, "Phase 3 (Commercial)", p3, "p3_rationale", "Large-Scale & Chronic Safety"),
    ]:
        prob_val = prob * 100 if isinstance(prob, float) and prob <= 1 else prob
        prob_color = "#2ECC71" if prob_val >= 60 else "#F1C40F" if prob_val >= 30 else "#E74C3C"
        with col:
            st.markdown(f"""
            <div class="phase-container">
                <div class="phase-label">{phase}</div>
                <div class="phase-value" style="color: {prob_color};">{prob_val:.0f}%</div>
                <div style="font-size: 0.8rem; color: #666;">{label}</div>
            </div>
            """, unsafe_allow_html=True)
            rationale = edward_data.get(rationale_key, "N/A")
            st.caption(rationale)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Detailed Rationales ─────────────────────────────────────────────
    st.subheader("Detailed Analysis")

    with st.expander("Edward's MedChem Rationale", expanded=True):
        rationale = edward_data.get("rational", edward_data.get("rationale", "N/A"))
        st.markdown(rationale)

    with st.expander("Salah's Biological & Clinical Rationale", expanded=True):
        st.markdown(salah_data.get("biological_rationale", "N/A"))
        if salah_data.get("p3_cap_reason"):
            st.markdown(f"**P3 Cap Reason:** {salah_data['p3_cap_reason']}")

    # ── Metabolic & Tox Info ────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("Structural Flags")

    fc1, fc2 = st.columns(2)
    with fc1:
        stability = edward_data.get("metabolic_stability_estimate", "N/A")
        stab_icon = {"High": "🟢", "Medium": "🟡", "Low": "🔴"}.get(stability, "⚪")
        st.markdown(f"""
        <div class="info-card">
            <h4>Metabolic Stability</h4>
            <p style="font-size: 1.2rem;">{stab_icon} {stability}</p>
        </div>
        """, unsafe_allow_html=True)

    with fc2:
        fragments = edward_data.get("potential_toxic_fragments", "None identified")
        if isinstance(fragments, list):
            fragments_text = ", ".join(fragments)
        else:
            fragments_text = str(fragments)
        st.markdown(f"""
        <div class="info-card">
            <h4>Potential Toxic Fragments</h4>
            <p>{fragments_text}</p>
        </div>
        """, unsafe_allow_html=True)

    # ── Molecule Visualization with Highlighted Toxic Fragments ─────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("Molecule Structure — Toxic Fragment Map")

    with st.spinner("Generating fragment highlights..."):
        smarts_list = get_fragment_smarts(fragments_text, smiles)
        mol_img, matched_frags = draw_molecule_with_highlights(smiles, smarts_list)

    if mol_img is not None:
        st.image(mol_img, use_container_width=True)

        if matched_frags:
            legend_html = '<div style="display: flex; flex-wrap: wrap; gap: 1rem; margin-top: 0.5rem;">'
            for frag in matched_frags:
                r, g, b, a = frag["color"]
                css_color = f"rgba({int(r*255)}, {int(g*255)}, {int(b*255)}, 0.9)"
                legend_html += f"""
                <div style="display: flex; align-items: center; gap: 0.4rem;">
                    <div style="width: 14px; height: 14px; border-radius: 3px; background: {css_color};"></div>
                    <span style="color: #ccc; font-size: 0.85rem;">{frag["name"]} ({frag["atom_count"]} atoms)</span>
                </div>"""
            legend_html += '</div>'
            st.markdown(legend_html, unsafe_allow_html=True)
        else:
            st.caption("No toxic fragments could be mapped onto the structure.")
    else:
        st.warning("Could not parse the SMILES string for visualization.")

    # ── Raw JSON (collapsed) ────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("Raw JSON Output"):
        tab1, tab2 = st.tabs(["Edward", "Salah"])
        with tab1:
            st.json(edward_data)
        with tab2:
            st.json(salah_data)

else:
    # ── Landing State ───────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class="info-card" style="text-align: center; padding: 2rem;">
            <h4>Edward</h4>
            <p style="font-size: 2rem;">🧪</p>
            <p style="color: #aaa;">Senior Medicinal Chemist<br>Structural critique, hERG, MBI, LipE, MPO analysis</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="info-card" style="text-align: center; padding: 2rem;">
            <h4>Salah</h4>
            <p style="font-size: 2rem;">🧬</p>
            <p style="color: #aaa;">Clinical Pharmacologist<br>Target validation, dose-toxicity, biological graveyard detection</p>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="info-card" style="text-align: center; padding: 2rem;">
            <h4>Combined</h4>
            <p style="font-size: 2rem;">🎯</p>
            <p style="color: #aaa;">AUC 0.93 on 219-molecule benchmark<br>From structural filter to clinical success predictor</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 2rem;">
        <p style="font-size: 1.1rem;">Submit a molecule using the sidebar to receive a coordinated MedChem + Biology critique.</p>
        <p style="font-size: 0.85rem;">Enter SMILES, Target Class, and Indication to get started.</p>
    </div>
    """, unsafe_allow_html=True)
