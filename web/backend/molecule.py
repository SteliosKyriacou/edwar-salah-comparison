"""Molecule drawing with RDKit — 2D depiction + toxic fragment highlighting."""

import base64
import io
from rdkit import Chem
from rdkit.Chem import Draw, AllChem
from rdkit.Chem.Draw import rdMolDraw2D


FRAGMENT_COLORS = {
    "Nitroaromatic": ("[N+](=O)[O-]c", (1.0, 0.2, 0.2)),
    "Aniline": ("c1ccc(N)cc1", (1.0, 0.5, 0.0)),
    "Hydrazine": ("NN", (0.8, 0.0, 0.8)),
    "Epoxide": ("C1OC1", (1.0, 0.0, 0.0)),
    "Michael acceptor": ("C=CC(=O)", (0.9, 0.3, 0.0)),
    "Acyl halide": ("C(=O)Cl", (1.0, 0.1, 0.1)),
    "Thiophene": ("c1ccsc1", (0.6, 0.6, 0.0)),
    "Furan": ("c1ccoc1", (0.7, 0.5, 0.0)),
    "Halogenated aromatic": ("c1cc(F)ccc1", (0.0, 0.6, 0.8)),
}


def draw_molecule(smiles, width=500, height=400):
    """Draw a molecule and return base64 PNG + fragment match info."""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None, [], "Invalid SMILES"

    AllChem.Compute2DCoords(mol)

    # Find toxic fragments
    highlights = {}
    fragment_matches = []
    color_idx = 0

    for name, (smarts, color) in FRAGMENT_COLORS.items():
        pattern = Chem.MolFromSmarts(smarts)
        if pattern is None:
            continue
        matches = mol.GetSubstructMatches(pattern)
        if matches:
            fragment_matches.append({
                "name": name,
                "smarts": smarts,
                "count": len(matches),
                "color": f"rgb({int(color[0]*255)},{int(color[1]*255)},{int(color[2]*255)})",
            })
            for match in matches:
                for atom_idx in match:
                    highlights[atom_idx] = color

    # Draw
    drawer = rdMolDraw2D.MolDraw2DCairo(width, height)
    opts = drawer.drawOptions()
    opts.setBackgroundColour((0.08, 0.08, 0.12, 1.0))
    opts.bondLineWidth = 2.0

    if highlights:
        atom_colors = {idx: col for idx, col in highlights.items()}
        atom_radii = {idx: 0.3 for idx in highlights}
        drawer.DrawMolecule(
            mol,
            highlightAtoms=list(highlights.keys()),
            highlightAtomColors=atom_colors,
            highlightAtomRadii=atom_radii,
        )
    else:
        drawer.DrawMolecule(mol)

    drawer.FinishDrawing()
    png_data = drawer.GetDrawingText()

    b64 = base64.b64encode(png_data).decode("utf-8")
    return b64, fragment_matches, None
