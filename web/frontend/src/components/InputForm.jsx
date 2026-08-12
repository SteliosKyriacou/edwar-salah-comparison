import React, { useState } from 'react'

const EXAMPLES = [
  {
    label: 'Example: Success',
    smiles: 'CCOC(=O)[C@H](CCC1=CC=CC=C1)N[C@@H](C)C(=O)N2[C@H]3CCC[C@H]3C[C@H]2C(=O)O',
    target: 'ACE inhibitor',
    indication: 'Cardiovascular',
  },
  {
    label: 'Example: Failure',
    smiles: 'C1=CC(=CC=C1S(=O)(=O)N(CC2=C(C=C(C=C2)C3=NOC=N3)F)[C@H](CCC(F)(F)F)C(=O)N)Cl',
    target: 'g-Secretase inhibitor',
    indication: 'CNS',
  },
  {
    label: 'Antibody Success (Trastuzumab)',
    smiles: '[Monoclonal Antibody: Trastuzumab (Anti-HER2 IgG1)] Heavy chain: EVQLVESGGGLVQPGGSLRLSCAASGFNIKDTYIHWVRQAPGKGLEWVARIYPTNGYTRYADSVKGRFTISADTSKNTAYLQMNSLRAEDTAVYYCSRWGGDGFYAMDYWGQGTLVTVSS... Light chain: DIQMTQSPSSLSASVGDRVTITCRASQDVNTAVAWYQQKPGKAPKLLIYSASFLYSGVPSRFSGSRSGTDFTLTISSLQPEDFATYYCQQHYTTPPTFGQGTKVEIKR...',
    target: 'HER2 Receptor',
    indication: 'Oncology (Breast Cancer)',
  },
  {
    label: 'Antibody Failure (Bapineuzumab)',
    smiles: '[Monoclonal Antibody: Bapineuzumab (Anti-Amyloid-beta IgG1)] Heavy chain: EVQLVESGGGLVQPGGSLRLSCAASGFTFSDHYMSWVRQAPGKGLEWVAYISSGGGSTYYPDTVKGRFTISRDNAKNSLYLQMNSLRAEDTAVYYCARYGNYVWYFDVWGQGTLVTVSS... Light chain: DIQMTQSPSSLSASVGDRVTITCRASQSISSYLNWYQQKPGKAPKLLIYAASSLQSGVPSRFSGSGSGTDFTLTISSLQPEDFATYYCQQSYSTPYTFGQGTKVEIKR...',
    target: 'Amyloid-beta',
    indication: 'Neurology (Alzheimer\'s Disease)',
  },
]

export default function InputForm({ onSubmit, loading }) {
  const [smiles, setSmiles] = useState('')
  const [target, setTarget] = useState('')
  const [indication, setIndication] = useState('')
  const [auxiliary, setAuxiliary] = useState('')
  const [webSearch, setWebSearch] = useState(false)
  const [oldTox, setOldTox] = useState(false)

  function handleExample(ex) {
    setSmiles(ex.smiles)
    setTarget(ex.target)
    setIndication(ex.indication)
    setAuxiliary('')
  }

  function handleSubmit(e) {
    e.preventDefault()
    onSubmit({ smiles, target, indication, auxiliary, web_search: webSearch, old_tox: oldTox })
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
              borderRadius: 0,
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

        <div
          className="form-group full-width"
          style={{
            display: 'flex',
            alignItems: 'flex-start',
            gap: 12,
            padding: '12px 14px',
            borderRadius: 0,
            border: '1px solid var(--border)',
            background: 'var(--bg-secondary)',
          }}
        >
          <button
            type="button"
            role="switch"
            aria-checked={webSearch}
            onClick={() => setWebSearch((v) => !v)}
            title="Toggle web search"
            style={{
              flexShrink: 0,
              width: 44,
              height: 24,
              borderRadius: 0,
              border: 'none',
              cursor: 'pointer',
              padding: 2,
              background: webSearch ? 'var(--accent-blue)' : 'var(--border)',
              transition: 'background 0.2s',
              display: 'flex',
              justifyContent: webSearch ? 'flex-end' : 'flex-start',
              alignItems: 'center',
            }}
          >
            <span
              style={{
                display: 'block',
                width: 20,
                height: 20,
                borderRadius: '50%',
                background: '#fff',
              }}
            />
          </button>
          <div>
            <div style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text)' }}>
              🌐 Web Search {webSearch ? 'On' : 'Off'}
            </div>
            <div style={{ fontSize: '0.73rem', color: 'var(--text-muted)', marginTop: 3 }}>
              When on, the system searches recent publications and clinical data, validates a
              referenced summary, and feeds it to the agents. Adds ~20–30s. Off by default.
            </div>
          </div>
        </div>

        <div
          className="form-group full-width"
          style={{
            display: 'flex',
            alignItems: 'flex-start',
            gap: 12,
            padding: '12px 14px',
            borderRadius: 0,
            border: '1px solid var(--border)',
            background: 'var(--bg-secondary)',
          }}
        >
          <button
            type="button"
            role="switch"
            aria-checked={oldTox}
            aria-label="old-tox"
            onClick={() => setOldTox((v) => !v)}
            title="Toggle old-tox (free-form toxicology reporting)"
            style={{
              flexShrink: 0,
              width: 44,
              height: 24,
              borderRadius: 0,
              border: 'none',
              cursor: 'pointer',
              padding: 2,
              background: oldTox ? 'var(--accent-blue)' : 'var(--border)',
              transition: 'background 0.2s',
              display: 'flex',
              justifyContent: oldTox ? 'flex-end' : 'flex-start',
              alignItems: 'center',
            }}
          >
            <span
              style={{
                display: 'block',
                width: 20,
                height: 20,
                borderRadius: '50%',
                background: '#fff',
              }}
            />
          </button>
          <div>
            <div style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text)' }}>
              🧪 old-tox {oldTox ? 'On' : 'Off'}
            </div>
            <div style={{ fontSize: '0.73rem', color: 'var(--text-muted)', marginTop: 3 }}>
              Off by default: the toxicologist must return an explicit PASS/FAIL for all ten
              organ-system toxicity categories. Turn on to restore the previous free-form
              toxicology reporting without the mandatory panel.
            </div>
          </div>
        </div>

        <button className="submit-btn" type="submit" disabled={loading}>
          {loading ? 'Analyzing...' : 'Analyze Molecule'}
        </button>
      </div>
    </form>
  )
}
