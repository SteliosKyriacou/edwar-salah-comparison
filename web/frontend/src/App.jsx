import React, { useState, useRef, useEffect } from 'react'
import Header from './components/Header'
import InputForm from './components/InputForm'
import ScoreCards from './components/ScoreCards'
import PhaseCards from './components/PhaseCards'
import AgentCard from './components/AgentCard'
import StructuralFlags from './components/StructuralFlags'
import LoadingCountdown from './components/LoadingCountdown'
import FdaResponse from './components/FdaResponse'
import WebSearchSummary from './components/WebSearchSummary'

export default function App() {
  const [apiKey, setApiKey] = useState(localStorage.getItem('v25_api_key') || '')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const resultsRef = useRef(null)

  // Router check
  if (window.location.pathname === '/usage') {
    return <UsagePage />
  }

  async function handleSubmit(formData) {
    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const res = await fetch('/api/analyze', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'X-API-Key': apiKey
        },
        body: JSON.stringify(formData),
      })

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }))
        throw new Error(err.detail || 'Analysis failed')
      }

      const data = await res.json()
      setResult(data)

      setTimeout(() => {
        resultsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
      }, 100)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <Header />
      <div className="container">
        <div className="api-key-config">
          <label htmlFor="api-key-input">🔑 API Key:</label>
          <input
            id="api-key-input"
            type="password"
            placeholder="Enter your V25 API Key to enable predictions..."
            value={apiKey}
            onChange={(e) => {
              const val = e.target.value
              setApiKey(val)
              localStorage.setItem('v25_api_key', val)
            }}
          />
          <a href="/usage" style={{ marginLeft: 12, fontSize: '0.85rem', color: 'var(--accent-blue)', textDecoration: 'none', fontWeight: 600 }}>
            View My Usage &rarr;
          </a>
        </div>

        <InputForm onSubmit={handleSubmit} loading={loading} />

        {loading && <LoadingCountdown />}

        {error && <div className="error-msg">{error}</div>}

        {result && (
          <div ref={resultsRef}>
            <ScoreCards overview={result.overview} />
            <PhaseCards overview={result.overview} />

            <FdaResponse fda={result.web_search?.fda} />
            <WebSearchSummary webSearch={result.web_search} />

            <StructuralFlags overview={result.overview} />

            <div className="section-title">Agent Assessments</div>
            <div className="agents-grid">
              <AgentCard
                name="Biological-Rationalist"
                icon="🧬"
                iconBg="rgba(46, 204, 113, 0.15)"
                data={result.biology}
                probKeys={['bio_p1', 'bio_p2', 'bio_p3']}
                probRationaleKeys={['bio_p1_rationale', 'bio_p2_rationale', 'bio_p3_rationale']}
                sections={[
                  { title: 'Rationale', key: 'rationale' },
                  { title: 'Mechanism Validation', key: 'mechanism_validation' },
                  { title: 'Druggability Assessment', key: 'druggability' },
                ]}
              />
              <AgentCard
                name="Toxi-Predictive-Toxicologist"
                icon="☠️"
                iconBg="rgba(231, 76, 60, 0.15)"
                data={result.toxicology}
                probKeys={['tox_p1', 'tox_p2', 'tox_p3']}
                probRationaleKeys={['tox_p1_rationale', 'tox_p2_rationale', 'tox_p3_rationale']}
                sections={[
                  { title: 'Rationale', key: 'rationale' },
                ]}
                details={[
                  { label: 'Therapeutic Window', key: 'therapeutic_window' },
                  { label: 'Primary Concern', key: 'primary_concern' },
                  { label: 'On-Target Risk', key: 'on_target_risk' },
                  { label: 'Off-Target Risk', key: 'off_target_risk' },
                ]}
              />
              <AgentCard
                name="Pharma-Clinical-Pharmacologist"
                icon="💊"
                iconBg="rgba(74, 158, 255, 0.15)"
                data={result.pharmacology}
                probKeys={['pk_p1', 'pk_p2', 'pk_p3']}
                probRationaleKeys={['pk_p1_rationale', 'pk_p2_rationale', 'pk_p3_rationale']}
                sections={[
                  { title: 'Rationale', key: 'rationale' },
                ]}
                details={[
                  { label: 'Predicted Dose', key: 'predicted_dose' },
                  { label: 'Oral Feasibility', key: 'oral_feasibility' },
                  { label: 'DDI Risk', key: 'ddi_risk' },
                  { label: 'Half-Life', key: 'half_life' },
                ]}
              />
              <AgentCard
                name="MedChem-Rationalist"
                icon="🧪"
                iconBg="rgba(155, 89, 182, 0.15)"
                data={result.medchem}
                probKeys={['chem_p1', 'chem_p2', 'chem_p3']}
                probRationaleKeys={[]}
                sections={[]}
                isMedchem
              />
            </div>
          </div>
        )}
      </div>

      <div className="calibration-section">
        <div className="section-title">Calibration from Historical Data (N=393)</div>
        <div className="calibration-subtitle">
          Developability Risk Score validated against 393 approved and failed drugs across all therapeutic areas
        </div>
        <img src="/calibration.png" alt="Developability Risk Score calibration from historical data" className="calibration-img" />
      </div>

      <div className="disclaimer">
        <p><strong>Disclaimer:</strong> This platform is provided for informational and research purposes only. The Clinical Developability Risk (CDR) score and all associated assessments are generated by AI models and should not be construed as professional pharmaceutical advice, regulatory guidance, or investment advice. No guarantee is made regarding the accuracy, completeness, or reliability of any prediction. Users should not make clinical development, licensing, investment, or any other business decisions based solely on the outputs of this tool. All results should be independently validated by qualified professionals. The developers assume no liability for any decisions or actions taken based on the information provided by this platform. Past performance of the model on historical data does not guarantee future predictive accuracy.</p>
      </div>

      <div className="contact-footer">
        <span className="contact-label">Contact</span>
        <a href="mailto:stelios@reneubio.com" className="contact-email">stelios@reneubio.com</a>
      </div>
    </>
  )
}

function UsagePage() {
  const [apiKey, setApiKey] = useState(localStorage.getItem('v25_api_key') || '')
  const [info, setInfo] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)

  async function checkUsage() {
    if (!apiKey.trim()) {
      setError('Please enter an API Key to check.')
      return
    }
    setLoading(true)
    setError(null)
    setInfo(null)
    try {
      const res = await fetch(`/api/usage?api_key=${encodeURIComponent(apiKey)}`)
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }))
        throw new Error(err.detail || 'Failed to fetch usage information.')
      }
      const data = await res.json()
      setInfo(data)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (apiKey) {
      checkUsage()
    }
  }, [])

  return (
    <div className="usage-container">
      <h2 className="usage-title">🔑 V25 API Key Usage</h2>
      
      <div className="form-group" style={{ marginBottom: 20 }}>
        <label style={{ display: 'block', marginBottom: 8, fontWeight: 600 }}>API Key</label>
        <div style={{ display: 'flex', gap: 10 }}>
          <input
            type="password"
            placeholder="Enter your V25 API Key..."
            value={apiKey}
            onChange={(e) => {
              setApiKey(e.target.value)
              localStorage.setItem('v25_api_key', e.target.value)
            }}
            style={{
              flex: 1,
              background: 'var(--bg-secondary)',
              border: '1px solid var(--border)',
              borderRadius: 8,
              padding: '10px 14px',
              color: 'var(--text-primary)'
            }}
          />
          <button
            onClick={checkUsage}
            disabled={loading}
            style={{
              background: 'var(--accent-blue)',
              color: '#000',
              border: 'none',
              borderRadius: 8,
              padding: '10px 20px',
              fontWeight: 700,
              cursor: 'pointer'
            }}
          >
            {loading ? 'Checking...' : 'Check'}
          </button>
        </div>
      </div>

      {error && <div className="error-msg" style={{ marginBottom: 20 }}>{error}</div>}

      {info && (
        <>
          <div className="usage-card">
            <h3 style={{ fontSize: '1.1rem', marginBottom: 16, borderBottom: '1px solid var(--border)', paddingBottom: 10, color: 'var(--accent-blue)' }}>📋 Key Profile & Quota</h3>
            <div className="usage-item">
              <span className="usage-label">Owner:</span>
              <span className="usage-value active" style={{ fontSize: '1.05rem' }}>{info.owner}</span>
            </div>
            <div className="usage-item">
              <span className="usage-label">Hourly Limit:</span>
              <span className={`usage-value ${info.rate_limit < 0 ? 'unlimited' : ''}`}>
                {info.rate_limit < 0 ? 'Unlimited' : info.rate_limit}
              </span>
            </div>
            <div className="usage-item">
              <span className="usage-label">Rolling Hour Usage:</span>
              <span className="usage-value">{info.usage} predictions</span>
            </div>
            <div className="usage-item">
              <span className="usage-label">Remaining Quota:</span>
              <span className={`usage-value ${info.remaining === 'unlimited' ? 'unlimited' : ''}`}>
                {info.remaining === 'unlimited' ? 'Unlimited' : `${info.remaining} predictions`}
              </span>
            </div>
            <div className="usage-item" style={{ borderTop: '1px dashed var(--border)', marginTop: 8, paddingTop: 12 }}>
              <span className="usage-label" style={{ color: 'var(--accent-cyan)' }}>⏳ Currently Evaluating:</span>
              <span className="usage-value" style={{ color: 'var(--accent-cyan)' }}>{info.evaluating_now ?? 0}</span>
            </div>
            <div className="usage-item">
              <span className="usage-label" style={{ color: 'var(--accent-orange)' }}>👥 In Queue:</span>
              <span className="usage-value" style={{ color: 'var(--accent-orange)' }}>{info.queued_now ?? 0}</span>
            </div>
          </div>

          <div className="usage-card">
            <h3 style={{ fontSize: '1.1rem', marginBottom: 16, borderBottom: '1px solid var(--border)', paddingBottom: 10, color: 'var(--accent-purple)' }}>📈 Cumulative Key Statistics</h3>
            <div className="usage-item">
              <span className="usage-label">Total Predictions:</span>
              <span className="usage-value">{info.stats?.total_predictions || 0}</span>
            </div>
            <div className="usage-item">
              <span className="usage-label">Unique Molecules Analyzed:</span>
              <span className="usage-value">{info.stats?.unique_molecules || 0}</span>
            </div>
            <div className="usage-item">
              <span className="usage-label">Unique Targets Analyzed:</span>
              <span className="usage-value">{info.stats?.unique_targets || 0}</span>
            </div>
            <div className="usage-item">
              <span className="usage-label">Unique Indications Analyzed:</span>
              <span className="usage-value">{info.stats?.unique_indications || 0}</span>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 24 }} className="usage-grid">
            <div className="usage-card" style={{ marginBottom: 0 }}>
              <h3 style={{ fontSize: '1rem', marginBottom: 12, borderBottom: '1px solid var(--border)', paddingBottom: 8, color: 'var(--accent-cyan)' }}>🧬 By Target</h3>
              {info.stats?.predictions_per_target && Object.keys(info.stats.predictions_per_target).length > 0 ? (
                <div style={{ maxHeight: 200, overflowY: 'auto' }}>
                  <table style={{ width: '100%', fontSize: '0.82rem', borderCollapse: 'collapse' }}>
                    <thead>
                      <tr style={{ borderBottom: '1px solid var(--border)', color: 'var(--text-muted)' }}>
                        <th style={{ textAlign: 'left', padding: '6px 4px' }}>Target</th>
                        <th style={{ textAlign: 'right', padding: '6px 4px' }}>Predictions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {Object.entries(info.stats.predictions_per_target)
                        .sort((a, b) => b[1] - a[1])
                        .map(([t, count]) => (
                          <tr key={t} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                            <td style={{ padding: '6px 4px', color: 'var(--text-primary)' }}>{t}</td>
                            <td style={{ padding: '6px 4px', textAlign: 'right', fontWeight: 700, color: 'var(--accent-blue)' }}>{count}</td>
                          </tr>
                        ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textAlign: 'center', padding: '10px 0' }}>No targets recorded yet.</div>
              )}
            </div>

            <div className="usage-card" style={{ marginBottom: 0 }}>
              <h3 style={{ fontSize: '1rem', marginBottom: 12, borderBottom: '1px solid var(--border)', paddingBottom: 8, color: 'var(--accent-green)' }}>🏥 By Indication</h3>
              {info.stats?.predictions_per_indication && Object.keys(info.stats.predictions_per_indication).length > 0 ? (
                <div style={{ maxHeight: 200, overflowY: 'auto' }}>
                  <table style={{ width: '100%', fontSize: '0.82rem', borderCollapse: 'collapse' }}>
                    <thead>
                      <tr style={{ borderBottom: '1px solid var(--border)', color: 'var(--text-muted)' }}>
                        <th style={{ textAlign: 'left', padding: '6px 4px' }}>Indication</th>
                        <th style={{ textAlign: 'right', padding: '6px 4px' }}>Predictions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {Object.entries(info.stats.predictions_per_indication)
                        .sort((a, b) => b[1] - a[1])
                        .map(([ind, count]) => (
                          <tr key={ind} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                            <td style={{ padding: '6px 4px', color: 'var(--text-primary)' }}>{ind}</td>
                            <td style={{ padding: '6px 4px', textAlign: 'right', fontWeight: 700, color: 'var(--accent-green)' }}>{count}</td>
                          </tr>
                        ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textAlign: 'center', padding: '10px 0' }}>No indications recorded yet.</div>
              )}
            </div>
          </div>
        </>
      )}

      <a href="/" className="usage-btn" style={{ marginTop: 12 }}>&larr; Back to Predictor App</a>
    </div>
  )
}
