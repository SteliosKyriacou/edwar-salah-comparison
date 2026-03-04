const FIGURES = [
  {
    src: "/api/figures/sm_edward_vs_edward_salah_roc.png",
    title: "ROC Comparison — Global Set (N=394)",
    comment:
      "Adding Salah's biological advisory lifts the AUC from 0.74 (Edward alone) to 0.90 (coordinated). The coordinated pipeline dominates at every operating point, confirming that target-class risk and dose-toxicity signals are orthogonal to structural MedChem features.",
  },
  {
    src: "/api/figures/sm_edward_vs_edward_salah_calibration.png",
    title: 'Calibration — The "Salah Effect"',
    comment:
      "Edward alone shows poor calibration in the mid-range bins (40-70): many failed drugs receive moderate scores. With Salah's penalty, the coordinated system pushes liabilities into higher bins, producing a cleaner separation between approved and failed compounds across all score ranges.",
  },
  {
    src: "/api/figures/sm_edward_vs_edward_salah_score_drift.png",
    title: "Score Drift — Biological Penalty Map",
    comment:
      "Each dot is a molecule. Points above the diagonal were penalised by Salah's biological advisory. Market withdrawals (red) and clinical failures (orange) are systematically pushed upward, while approved drugs (green) cluster near or below the diagonal — exactly the behaviour we want.",
  },
  {
    src: "/api/figures/sm_edward_vs_edward_salah_factors.png",
    title: "Median Score Shift by Clinical Tag",
    comment:
      "The lollipop chart shows how much Salah's advisory shifts the median Edward Score for each failure category. Categories like hepatotoxicity (+20), cardiotoxicity (+18), and neurotoxicity (+17) receive the largest penalties — these are precisely the biological liabilities that pure structural analysis misses.",
  },
];

export default function BenchmarkGallery() {
  return (
    <div className="benchmark-gallery">
      <h2 className="section-title" style={{ textAlign: "center", marginTop: "2rem" }}>
        Benchmark — Global Set (N=394 Molecules)
      </h2>
      <p className="benchmark-intro">
        Validated on 394 small-molecule drugs spanning all therapeutic areas and
        eras. Below: head-to-head comparison of Edward alone vs. the
        coordinated Edward + Salah pipeline.
      </p>

      <div className="gallery-grid">
        {FIGURES.map(({ src, title, comment }, i) => (
          <div className="gallery-card" key={i}>
            <img src={src} alt={title} loading="lazy" />
            <h4>{title}</h4>
            <p>{comment}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
