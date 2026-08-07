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

export default function InputForm({ onSubmit, onDeepSubmit, loading, deepLoading, deepSimulations = 100 }) {
  const [smiles, setSmiles] = useState('')
  const [target, setTarget] = useState('')
  const [indication, setIndication] = useState('')
  const [auxiliary, setAuxiliary] = useState('')
  const [webSearch, setWebSearch] = useState(false)

  const busy = loading || deepLoading

  function handleExample(ex) {
    setSmiles(ex.smiles)
    setTarget(ex.target)
    setIndication(ex.indication)
    setAuxiliary('')
  }

  function fields() {
    return { smiles, target, indication, auxiliary, web_search: webSearch }
  }

  function handleSubmit(e) {
    e.preventDefault()
    onSubmit(fields())
  }

  function handleDeep() {
    if (!smiles.trim() || !target.trim() || !indication.trim()) {
      window.alert('SMILES, Target Class and Indication are all required for deep analysis.')
      return
    }
    const msg =
      `Run ${deepSimulations} independent simulations of this molecule?\n\n` +
      `• Each simulation is a full 5-agent pipeline run, individually ` +
      `timestamped and recorded in the registry.\n` +
      `• That is roughly ${deepSimulations * 5} model calls, so this takes ` +
      `several minutes and consumes real quota.\n\n` +
      `Continue?`
    if (window.confirm(msg)) {
      onDeepSubmit(fields())
    }
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
          className="full-width"
          style={{ display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'stretch' }}
        >
          <button
            className="submit-btn"
            type="submit"
            disabled={busy}
            style={{ flex: '1 1 260px', margin: 0 }}
          >
            {loading ? 'Analyzing...' : 'Analyze Molecule'}
          </button>

          <button
            className="submit-btn deep-btn"
            type="button"
            onClick={handleDeep}
            disabled={busy}
            title={`Run ${deepSimulations} simulations and report the distribution of outcomes`}
            style={{
              flex: '1 1 260px',
              margin: 0,
              background: 'transparent',
              color: 'var(--accent-purple)',
              border: '1px solid var(--accent-purple)',
            }}
          >
            {deepLoading ? 'Running Deep Analysis...' : `🔬 Deep Analysis (${deepSimulations}×)`}
          </button>
        </div>

        <div
          className="full-width"
          style={{ fontSize: '0.73rem', color: 'var(--text-muted)', marginTop: -4 }}
        >
          Deep Analysis repeats the same molecule, target and indication{' '}
          {deepSimulations} times and reports the distribution of CDR scores, per-phase
          probabilities and how often each risk appears. Every simulation is timestamped and
          tracked individually, so all {deepSimulations} appear in monitoring and are verifiable.
        </div>
      </div>
    </form>
  )
}
