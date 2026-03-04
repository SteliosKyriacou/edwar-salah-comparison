const PHASES = [
  { key: "p1", label: "Phase 1 (Safety)", sub: "First-in-Human Safety", ratKey: "p1_rationale" },
  { key: "p2", label: "Phase 2 (Efficacy)", sub: "Target Engagement & ADME", ratKey: "p2_rationale" },
  { key: "p3", label: "Phase 3 (Commercial)", sub: "Large-Scale & Chronic Safety", ratKey: "p3_rationale" },
];

export default function PhaseCards({ edward }) {
  return (
    <div className="phase-section">
      <h2 className="section-title">Clinical Phase Probabilities</h2>
      <div className="phase-row">
        {PHASES.map(({ key, label, sub, ratKey }) => {
          const raw = edward[`${key}_prob`] ?? 0;
          const pct = raw <= 1 ? raw * 100 : raw;
          const color = pct >= 60 ? "#2ECC71" : pct >= 30 ? "#F1C40F" : "#E74C3C";
          const rationale = edward[ratKey] ?? "";

          return (
            <div className="phase-card" key={key}>
              <div className="phase-label">{label}</div>
              <div className="phase-value" style={{ color }}>
                {pct.toFixed(0)}%
              </div>
              <div className="phase-sub">{sub}</div>
              {rationale && <div className="phase-rationale">{rationale}</div>}
            </div>
          );
        })}
      </div>
    </div>
  );
}
