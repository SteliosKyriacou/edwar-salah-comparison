const STAB_ICON = { High: "\u{1F7E2}", Medium: "\u{1F7E1}", Low: "\u{1F534}" };

export default function StructuralFlags({ edward }) {
  const stability = edward.metabolic_stability_estimate ?? "N/A";
  const rawFragments = edward.potential_toxic_fragments ?? "None identified";
  const fragmentsText = Array.isArray(rawFragments)
    ? rawFragments.join(", ")
    : String(rawFragments);

  return (
    <>
      <h2 className="section-title">Structural Flags</h2>
      <div className="flags-row">
        <div className="info-card">
          <h4>Metabolic Stability</h4>
          <div className="info-value">
            {STAB_ICON[stability] ?? "\u26AA"} {stability}
          </div>
        </div>
        <div className="info-card">
          <h4>Potential Toxic Fragments</h4>
          <div className="info-value">{fragmentsText}</div>
        </div>
      </div>
    </>
  );
}
