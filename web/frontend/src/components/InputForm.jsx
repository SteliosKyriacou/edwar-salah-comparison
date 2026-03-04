import { useState } from "react";

export default function InputForm({ onSubmit, loading }) {
  const [smiles, setSmiles] = useState("");
  const [target, setTarget] = useState("");
  const [indication, setIndication] = useState("");
  const [auxiliary, setAuxiliary] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!smiles.trim() || !target.trim() || !indication.trim()) return;
    onSubmit({ smiles, target, indication, auxiliary });
  };

  return (
    <form className="input-form" onSubmit={handleSubmit}>
      <h3>Molecule Submission</h3>
      <div className="form-grid">
        <div className="form-group full-width">
          <label>SMILES *</label>
          <input
            type="text"
            value={smiles}
            onChange={(e) => setSmiles(e.target.value)}
            placeholder="e.g. CN(C)CCCC1(C2=C(CO1)C=C(C=C2)C#N)C3=CC=C(C=C3)F"
            required
          />
        </div>
        <div className="form-group">
          <label>Target Class *</label>
          <input
            type="text"
            value={target}
            onChange={(e) => setTarget(e.target.value)}
            placeholder="e.g. SSRI, BACE1, PD-1, EGFR"
            required
          />
        </div>
        <div className="form-group">
          <label>Indication / Therapeutic Area *</label>
          <input
            type="text"
            value={indication}
            onChange={(e) => setIndication(e.target.value)}
            placeholder="e.g. CNS, Oncology, Cardiovascular"
            required
          />
        </div>
        <div className="form-group full-width">
          <label>Auxiliary Notes (optional)</label>
          <textarea
            value={auxiliary}
            onChange={(e) => setAuxiliary(e.target.value)}
            placeholder="Any additional context: dose expectations, known liabilities, specific concerns..."
          />
        </div>
        <button className="submit-btn" type="submit" disabled={loading}>
          {loading ? "Analyzing..." : "Analyze Molecule"}
        </button>
      </div>
    </form>
  );
}
