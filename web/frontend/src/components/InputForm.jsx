import React, { useState } from 'react'

const EXAMPLES = [
  {
    label: 'Example: Success',
    smiles: 'CC(C)c1n(CC[C@@H](O)C[C@@H](O)CC(O)=O)c(-c2ccc(F)cc2)c(-c2ccccc2)c1C(=O)Nc1ccccc1',
    target: 'Enzyme',
    indication: 'Cardiovascular',
  },
  {
    label: 'Example: Failure',
    smiles: 'C1=CC(=CC=C1S(=O)(=O)N(CC2=C(C=C(C=C2)C3=NOC=N3)F)[C@H](CCC(F)(F)F)C(=O)N)Cl',
    target: 'g-Secretase inhibitor',
    indication: 'CNS',
  },
]

export default function InputForm({ onSubmit, loading }) {
  const [smiles, setSmiles] = useState('')
  const [target, setTarget] = useState('')
  const [indication, setIndication] = useState('')
  const [auxiliary, setAuxiliary] = useState('')

  function handleExample(ex) {
    setSmiles(ex.smiles)
    setTarget(ex.target)
    setIndication(ex.indication)
    setAuxiliary('')
  }

  function handleSubmit(e) {
    e.preventDefault()
    onSubmit({ smiles, target, indication, auxiliary })
  }

  return (
    <form className="input-form" onSubmit={handleSubmit}>
      <div style={{ marginBottom: 14, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', alignSelf: 'center' }}>
          Try:
        </span>
        {EXAMPLES.map((ex) => (
          <button
            key={ex.label}
            type="button"
            onClick={() => handleExample(ex)}
            style={{
              padding: '4px 10px',
              borderRadius: 6,
              border: '1px solid var(--border)',
              background: 'var(--bg-secondary)',
              color: 'var(--accent-blue)',
              fontSize: '0.73rem',
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            {ex.label}
          </button>
        ))}
      </div>

      <div className="form-grid">
        <div className="form-group full-width">
          <label>SMILES</label>
          <input
            type="text"
            value={smiles}
            onChange={(e) => setSmiles(e.target.value)}
            placeholder="e.g. CC(C)c1n(CC[C@@H](O)C[C@@H](O)CC(O)=O)c(-c2ccc(F)cc2)..."
            required
          />
        </div>

        <div className="form-group">
          <label>Target Class</label>
          <input
            type="text"
            value={target}
            onChange={(e) => setTarget(e.target.value)}
            placeholder="e.g. Kinase, GPCR, Enzyme, Ion Channel"
            required
          />
        </div>

        <div className="form-group">
          <label>Indication</label>
          <input
            type="text"
            value={indication}
            onChange={(e) => setIndication(e.target.value)}
            placeholder="e.g. Oncology, Cardiovascular, Neurology"
            required
          />
        </div>

        <div className="form-group full-width">
          <label>Auxiliary Context (optional)</label>
          <textarea
            value={auxiliary}
            onChange={(e) => setAuxiliary(e.target.value)}
            placeholder="Any additional context: known selectivity, intended route, development stage..."
          />
        </div>

        <button className="submit-btn" type="submit" disabled={loading}>
          {loading ? 'Analyzing...' : 'Analyze Molecule'}
        </button>
      </div>
    </form>
  )
}
