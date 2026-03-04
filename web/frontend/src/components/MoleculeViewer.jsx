export default function MoleculeViewer({ image, fragmentMatches }) {
  if (!image) {
    return (
      <div className="molecule-viewer">
        <h2>Molecule Structure</h2>
        <p style={{ color: "#888" }}>
          Could not parse the SMILES string for visualization.
        </p>
      </div>
    );
  }

  return (
    <div className="molecule-viewer">
      <h2>Molecule Structure &mdash; Toxic Fragment Map</h2>
      <img
        src={`data:image/png;base64,${image}`}
        alt="Molecule with toxic fragment highlights"
      />
      {fragmentMatches && fragmentMatches.length > 0 ? (
        <div className="fragment-legend">
          {fragmentMatches.map((frag, i) => {
            const [r, g, b] = frag.color;
            const css = `rgba(${Math.round(r * 255)}, ${Math.round(g * 255)}, ${Math.round(b * 255)}, 0.9)`;
            return (
              <div className="fragment-legend-item" key={i}>
                <div className="swatch" style={{ background: css }} />
                <span>
                  {frag.name} ({frag.atom_count} atoms)
                </span>
              </div>
            );
          })}
        </div>
      ) : (
        <p style={{ color: "#888", textAlign: "center", marginTop: "0.5rem" }}>
          No toxic fragments could be mapped onto the structure.
        </p>
      )}
    </div>
  );
}
