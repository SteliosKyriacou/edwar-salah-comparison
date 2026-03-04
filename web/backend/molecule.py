"""RDKit molecule drawing with toxic fragment highlighting."""

import base64
import io

from rdkit import Chem
from rdkit.Chem import AllChem
from rdkit.Chem.Draw import rdMolDraw2D
from PIL import Image


PALETTE = [
    (0.91, 0.30, 0.24, 0.45),  # red
    (0.95, 0.61, 0.07, 0.45),  # orange
    (0.56, 0.27, 0.68, 0.45),  # purple
    (0.20, 0.60, 0.86, 0.45),  # blue
]


def draw_molecule_with_highlights(
    smiles: str, fragment_smarts_list: list[dict]
) -> tuple[str | None, list[dict]]:
    """Draw molecule with toxic fragments highlighted.

    Returns (base64_png, fragment_matches) or (None, []) on failure.
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None, []

    AllChem.Compute2DCoords(mol)

    highlight_atoms: set[int] = set()
    highlight_bonds: set[int] = set()
    fragment_matches: list[dict] = []
    colors_atoms: dict[int, tuple] = {}
    colors_bonds: dict[int, tuple] = {}

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

        color = PALETTE[idx % len(PALETTE)]
        matched_atoms: set[int] = set()

        for match in matches:
            for atom_idx in match:
                highlight_atoms.add(atom_idx)
                colors_atoms[atom_idx] = color
                matched_atoms.add(atom_idx)

            for i, ai in enumerate(match):
                for j, aj in enumerate(match):
                    if i < j:
                        bond = mol.GetBondBetweenAtoms(ai, aj)
                        if bond:
                            bond_idx = bond.GetIdx()
                            highlight_bonds.add(bond_idx)
                            colors_bonds[bond_idx] = color

        fragment_matches.append({
            "name": name,
            "atom_count": len(matched_atoms),
            "color": [color[0], color[1], color[2], color[3]],
        })

    # Draw
    drawer = rdMolDraw2D.MolDraw2DCairo(700, 450)
    opts = drawer.drawOptions()
    opts.bondLineWidth = 2.0
    opts.padding = 0.15
    opts.backgroundColour = (0.06, 0.06, 0.14, 1.0)
    opts.setSymbolColour((0.85, 0.85, 0.85, 1.0))

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

    b64 = base64.b64encode(png_data).decode("utf-8")
    return b64, fragment_matches
