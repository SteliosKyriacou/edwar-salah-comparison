export default function ScoreCards({ edward, salah }) {
  const score = edward.edward_score ?? 50;
  const verdict = salah.salah_verdict ?? "CAUTION";
  const tcsp = edward.tcsp ?? 0;
  const tcspPct = tcsp <= 1 ? tcsp * 100 : tcsp;

  // Score class
  let scoreClass, scoreLabel;
  if (score <= 30) {
    scoreClass = "score-elite";
    scoreLabel = "Elite Candidate";
  } else if (score <= 60) {
    scoreClass = "score-caution";
    scoreLabel = "Proceed with Caution";
  } else {
    scoreClass = "score-danger";
    scoreLabel = "High Risk";
  }

  // Verdict class
  const verdictClass =
    { ELITE: "verdict-elite", CAUTION: "verdict-caution", TERMINATE: "verdict-terminate" }[
      verdict
    ] ?? "verdict-caution";

  // TCSP color
  const tcspColor = tcspPct >= 50 ? "#2ECC71" : tcspPct >= 20 ? "#F1C40F" : "#E74C3C";

  return (
    <div className="score-row">
      <div className={`score-card ${scoreClass}`}>
        <div className="label">Edward Score</div>
        <div className="value">{score}</div>
        <div className="sub">{scoreLabel}</div>
      </div>

      <div className="score-card score-neutral">
        <div className="label">Salah Verdict</div>
        <div style={{ margin: "0.8rem 0" }}>
          <span className={`verdict-badge ${verdictClass}`}>{verdict}</span>
        </div>
        <div className="sub">
          {salah.clinical_attrition_risk ?? "N/A"} Attrition Risk
        </div>
      </div>

      <div className="score-card score-neutral">
        <div className="label">Total Clinical Success</div>
        <div className="value" style={{ color: tcspColor }}>
          {tcspPct.toFixed(1)}%
        </div>
        <div className="sub">Total Clinical Success Probability</div>
      </div>
    </div>
  );
}
