import { useState, useRef } from "react";
import Header from "./components/Header";
import InputForm from "./components/InputForm";
import ScoreCards from "./components/ScoreCards";
import PhaseCards from "./components/PhaseCards";
import Rationales from "./components/Rationales";
import StructuralFlags from "./components/StructuralFlags";
import MoleculeViewer from "./components/MoleculeViewer";
import RawJson from "./components/RawJson";
import BenchmarkGallery from "./components/BenchmarkGallery";

export default function App() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const resultsRef = useRef(null);

  const handleSubmit = async (formData) => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const resp = await fetch("/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });

      if (!resp.ok) {
        const data = await resp.json().catch(() => ({}));
        throw new Error(data.detail || `Server error (${resp.status})`);
      }

      const data = await resp.json();
      setResult(data);

      // Smooth scroll to results
      setTimeout(() => {
        resultsRef.current?.scrollIntoView({ behavior: "smooth" });
      }, 100);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Header />
      <InputForm onSubmit={handleSubmit} loading={loading} />

      {loading && (
        <div className="loading-overlay">
          <div className="spinner" />
          <p>Running coordinated analysis &mdash; Salah + Edward...</p>
        </div>
      )}

      {error && <div className="error-msg">{error}</div>}

      {result && (
        <div ref={resultsRef}>
          <hr />
          <ScoreCards edward={result.edward} salah={result.salah} />
          <PhaseCards edward={result.edward} />
          <Rationales edward={result.edward} salah={result.salah} />
          <StructuralFlags edward={result.edward} />
          <MoleculeViewer
            image={result.molecule_image}
            fragmentMatches={result.fragment_matches}
          />
          <RawJson edward={result.edward} salah={result.salah} />
        </div>
      )}

      {!loading && !result && !error && <Landing />}
    </>
  );
}

function Landing() {
  return (
    <div className="landing">
      <div className="landing-grid">
        <div className="landing-card">
          <h4>Edward</h4>
          <div className="icon">&#129514;</div>
          <p>
            Senior Medicinal Chemist
            <br />
            Structural critique, hERG, MBI, LipE, MPO analysis
          </p>
        </div>
        <div className="landing-card">
          <h4>Salah</h4>
          <div className="icon">&#129516;</div>
          <p>
            Clinical Pharmacologist
            <br />
            Target validation, dose-toxicity, biological graveyard detection
          </p>
        </div>
        <div className="landing-card">
          <h4>Combined</h4>
          <div className="icon">&#127919;</div>
          <p>
            AUC 0.93 on 219-molecule benchmark
            <br />
            From structural filter to clinical success predictor
          </p>
        </div>
      </div>
      <div className="landing-hint">
        <p>
          Submit a molecule using the form above to receive a coordinated
          MedChem + Biology critique.
        </p>
        <p>Enter SMILES, Target Class, and Indication to get started.</p>
      </div>

      <BenchmarkGallery />
    </div>
  );
}
