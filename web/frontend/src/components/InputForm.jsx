import React, { useEffect, useState } from 'react'

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
]

const MODEL_STORAGE_KEY = 'alphaforge_model'

function money(v) {
  return `$${v.toFixed(2)}`
}

// One line per option: whether you could self-host it, what it costs, how much
// it can read, and how stale it is.
function optionLabel(m) {
  const licence = m.open_source ? 'open weights' : 'closed source'
  return `${m.label} — ${licence} · ${money(m.price_in)} in / ${money(m.price_out)} out per 1M · ${m.context_label} ctx · data freeze ${m.data_freeze} | ~${m.cost_label} per evaluation`
}

export default function InputForm({ onSubmit, loading }) {
  const [smiles, setSmiles] = useState('')
  const [target, setTarget] = useState('')
  const [indication, setIndication] = useState('')
  const [auxiliary, setAuxiliary] = useState('')
  const [webSearch, setWebSearch] = useState(false)
  const [models, setModels] = useState([])
  const [modelsError, setModelsError] = useState(null)
  const [modelsReload, setModelsReload] = useState(0)
  const [model, setModel] = useState(localStorage.getItem(MODEL_STORAGE_KEY) || '')

  // Fetched once per mount, but a page left open across a backend restart would
  // otherwise strand the picker on "Loading models…" forever, so failures retry
  // with backoff and then surface a Retry control.
  useEffect(() => {
    let cancelled = false
    let timer = null
    let attempt = 0

    async function loadModels() {
      try {
        // no-store + explicit Accept so a stale HTML response for this URL
        // (cached from before the endpoint existed) can never be replayed.
        const res = await fetch('/api/models', {
          cache: 'no-store',
          headers: { Accept: 'application/json' },
        })
        if (!res.ok) throw new Error(`server returned ${res.status}`)
        const contentType = res.headers.get('content-type') || ''
        if (!contentType.includes('application/json')) {
          throw new Error('server did not return JSON — try a hard reload')
        }
        const data = await res.json()
        if (cancelled) return
        setModels(data.models || [])
        setModelsError(null)
        // Keep a previously chosen model only if the server still offers it.
        setModel((current) =>
          (data.models || []).some((m) => m.id === current) ? current : data.default
        )
      } catch (e) {
        if (cancelled) return
        attempt += 1
        if (attempt <= 3) {
          timer = setTimeout(loadModels, 1000 * attempt)
          return
        }
        setModelsError(e.message || 'could not reach the server')
      }
    }

    setModelsError(null)
    loadModels()
    return () => {
      cancelled = true
      if (timer) clearTimeout(timer)
    }
  }, [modelsReload])

  const selected = models.find((m) => m.id === model)

  function handleExample(ex) {
    setSmiles(ex.smiles)
    setTarget(ex.target)
    setIndication(ex.indication)
    setAuxiliary('')
  }

  function handleSubmit(e) {
    e.preventDefault()
    onSubmit({ smiles, target, indication, auxiliary, model, web_search: webSearch })
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
          <label>Evaluation Model</label>
          <select
            value={model}
            onChange={(e) => {
              setModel(e.target.value)
              localStorage.setItem(MODEL_STORAGE_KEY, e.target.value)
            }}
            disabled={loading || models.length === 0}
          >
            {models.length === 0 && (
              <option value="">
                {modelsError ? 'Models unavailable' : 'Loading models…'}
              </option>
            )}
            {models.map((m) => (
              <option key={m.id} value={m.id}>
                {optionLabel(m)}
              </option>
            ))}
          </select>
          {modelsError && (
            <div style={{ fontSize: '0.73rem', color: 'var(--accent-red, #ff6b6b)', marginTop: 5 }}>
              Could not load the model list ({modelsError}).{' '}
              <button
                type="button"
                onClick={() => setModelsReload((n) => n + 1)}
                style={{
                  background: 'none',
                  border: 'none',
                  padding: 0,
                  color: 'var(--accent-blue)',
                  font: 'inherit',
                  fontWeight: 600,
                  cursor: 'pointer',
                  textDecoration: 'underline',
                }}
              >
                Retry
              </button>
              . The analysis will run on the server default until then.
            </div>
          )}
          {selected && (
            <div style={{ fontSize: '0.73rem', color: 'var(--text-muted)', marginTop: 5 }}>
              {selected.family}
              {selected.open_source
                ? ' · Open weights — self-hostable on your own cluster.'
                : ' · Closed source — API access only.'}
              {` · ~${selected.cost_label} per evaluation (estimated from a ~13.3k in / ~22.8k out token run)`}
              {selected.note ? ` · ${selected.note}` : ''}
              {webSearch && !selected.grounding
                ? ' · Web search will be grounded by Gemini 3.1 Pro (this model cannot search).'
                : ''}
            </div>
          )}
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

        <button className="submit-btn" type="submit" disabled={loading}>
          {loading ? 'Analyzing...' : 'Analyze Molecule'}
        </button>
      </div>
    </form>
  )
}
