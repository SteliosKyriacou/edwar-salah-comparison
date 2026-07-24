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
  const [isQueued, setIsQueued] = useState(false)
  const [isPrinting, setIsPrinting] = useState(false)
  const [error, setError] = useState(null)
  const resultsRef = useRef(null)

  function handlePrint() {
    setIsPrinting(true)
    setTimeout(() => {
      window.print()
      setIsPrinting(false)
    }, 200)
  }

  // Polling for queue state while loading
  useEffect(() => {
    if (!loading) {
      setIsQueued(false)
      return
    }

    async function pollStatus() {
      try {
        const res = await fetch(`/api/usage?api_key=${encodeURIComponent(apiKey)}`)
        if (res.ok) {
          const data = await res.json()
          // If queued_now is greater than 0, it means our request is still in the queue!
          setIsQueued(data.queued_now > 0)
        }
      } catch (e) {
        // ignore errors during background polling
      }
    }

    pollStatus()
    const interval = setInterval(pollStatus, 1500)
    return () => clearInterval(interval)
  }, [loading, apiKey])

  // Router check
  if (window.location.pathname === '/usage') {
    return <UsagePage />
  }
  if (window.location.pathname === '/verify') {
    return <VerifyPage />
  }

  async function handleSubmit(formData) {
    setLoading(true)
    setIsQueued(true) // assume starting in queue state if server has any load
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

        {loading && <LoadingCountdown isQueued={isQueued} />}

        {error && <div className="error-msg">{error}</div>}

        {result && (
          <div ref={resultsRef}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24, borderBottom: '1px solid var(--border)', paddingBottom: 16 }} className="print-hide">
              <h2 style={{ margin: 0, fontSize: '1.4rem', color: 'var(--text-primary)' }}>📊 Clinical Attrition Assessment Results</h2>
              <div style={{ display: 'flex', gap: 10 }}>
                {result.tsa_manifest && (
                  <button 
                    onClick={() => {
                      const blob = new Blob([result.tsa_manifest], { type: 'text/plain' });
                      const url = URL.createObjectURL(blob);
                      const a = document.createElement('a');
                      a.href = url;
                      a.download = `V25_Prediction_Manifest_${result.tsa_timestamp ? result.tsa_timestamp.slice(0,10) : 'verification'}.txt`;
                      a.click();
                    }}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 8,
                      padding: '10px 20px',
                      background: 'rgba(74, 158, 255, 0.15)',
                      color: 'var(--accent-blue)',
                      border: '1px solid rgba(74, 158, 255, 0.3)',
                      borderRadius: 8,
                      fontWeight: 700,
                      cursor: 'pointer',
                      fontSize: '0.9rem'
                    }}
                  >
                    📄 Download Manifest
                  </button>
                )}
                {result.tsa_signature_b64 && (
                  <button 
                    onClick={() => {
                      const bin = atob(result.tsa_signature_b64);
                      const arr = new Uint8Array(bin.length);
                      for (let i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i);
                      const blob = new Blob([arr], { type: 'application/timestamp-reply' });
                      const url = URL.createObjectURL(blob);
                      const a = document.createElement('a');
                      a.href = url;
                      a.download = `V25_TSA_Certificate_${result.tsa_timestamp ? result.tsa_timestamp.slice(0,10) : 'verification'}.tsr`;
                      a.click();
                    }}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 8,
                      padding: '10px 20px',
                      background: 'rgba(46, 204, 113, 0.15)',
                      color: 'var(--accent-green)',
                      border: '1px solid rgba(46, 204, 113, 0.3)',
                      borderRadius: 8,
                      fontWeight: 700,
                      cursor: 'pointer',
                      fontSize: '0.9rem'
                    }}
                  >
                    🛡️ Download TSR
                  </button>
                )}
                <button 
                  onClick={handlePrint}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                    padding: '10px 20px',
                    background: 'var(--accent-blue)',
                    color: '#000',
                    border: 'none',
                    borderRadius: 8,
                    fontWeight: 700,
                    cursor: 'pointer',
                    fontSize: '0.9rem',
                    boxShadow: '0 4px 12px rgba(74, 158, 255, 0.25)'
                  }}
                >
                  📄 Save as PDF
                </button>
              </div>
            </div>

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
                isPrinting={isPrinting}
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
                isPrinting={isPrinting}
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
                isPrinting={isPrinting}
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
                isPrinting={isPrinting}
              />
            </div>

            {/* Cryptographic Verification Certificate */}
            <div className="usage-card" style={{ marginTop: 32, border: '1px solid rgba(46, 204, 113, 0.3)', background: 'rgba(46, 204, 113, 0.02)', pageBreakInside: 'avoid', textAlign: 'left' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', borderBottom: '1px solid rgba(46, 204, 113, 0.15)', paddingBottom: 12, marginBottom: 16, flexWrap: 'wrap', gap: 10 }}>
                <div>
                  <h3 style={{ fontSize: '1.1rem', margin: 0, color: 'var(--accent-green)', display: 'flex', alignItems: 'center', gap: 6 }}>
                    🛡️ DigiCert Cryptographic Verification Certificate
                  </h3>
                  <div style={{ fontSize: '0.73rem', color: 'var(--text-muted)', marginTop: 4 }}>
                    RFC 3161 Trusted Time-Stamp Authority (TSA) Signed Token
                  </div>
                </div>
                <div style={{ display: 'flex', gap: 10 }} className="print-hide">
                  {result.tsa_manifest && (
                    <button
                      onClick={() => {
                        const blob = new Blob([result.tsa_manifest], { type: 'text/plain' });
                        const url = URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = `V25_Prediction_Manifest_${result.tsa_timestamp ? result.tsa_timestamp.slice(0,10) : 'verification'}.txt`;
                        a.click();
                      }}
                      style={{
                        background: 'rgba(74, 158, 255, 0.15)',
                        color: 'var(--accent-blue)',
                        border: '1px solid rgba(74, 158, 255, 0.3)',
                        borderRadius: 6,
                        padding: '6px 12px',
                        fontSize: '0.75rem',
                        fontWeight: 700,
                        cursor: 'pointer'
                      }}
                    >
                      📄 Download Manifest
                    </button>
                  )}
                  {result.tsa_signature_b64 && (
                    <button
                      onClick={() => {
                        const bin = atob(result.tsa_signature_b64);
                        const arr = new Uint8Array(bin.length);
                        for (let i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i);
                        const blob = new Blob([arr], { type: 'application/timestamp-reply' });
                        const url = URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = `V25_TSA_Certificate_${result.tsa_timestamp ? result.tsa_timestamp.slice(0,10) : 'verification'}.tsr`;
                        a.click();
                      }}
                      style={{
                        background: 'rgba(46, 204, 113, 0.15)',
                        color: 'var(--accent-green)',
                        border: '1px solid rgba(46, 204, 113, 0.3)',
                        borderRadius: 6,
                        padding: '6px 12px',
                        fontSize: '0.75rem',
                        fontWeight: 700,
                        cursor: 'pointer'
                      }}
                    >
                      📥 Download TSR Signature
                    </button>
                  )}
                </div>
              </div>

              <div className="usage-item" style={{ borderBottom: '1px solid rgba(255,255,255,0.05)', padding: '8px 0', display: 'flex', justifyContent: 'space-between' }}>
                <span className="usage-label" style={{ color: 'var(--text-secondary)' }}>Verified Timestamp:</span>
                <span className="usage-value active" style={{ color: 'var(--accent-green)', fontWeight: 700 }}>
                  {result.tsa_timestamp ? new Date(result.tsa_timestamp).toUTCString() : 'Verifying...'}
                </span>
              </div>
              <div className="usage-item" style={{ borderBottom: '1px solid rgba(255,255,255,0.05)', padding: '8px 0', display: 'flex', flexDirection: 'column', alignItems: 'flex-start', gap: 4 }}>
                <span className="usage-label" style={{ color: 'var(--text-secondary)' }}>Verification Fingerprint (SHA-256 Hash):</span>
                <span className="usage-value" style={{ fontFamily: 'monospace', fontSize: '0.75rem', color: 'var(--text-secondary)', wordBreak: 'break-all', display: 'block', marginTop: 4 }}>
                  {result.tsa_fingerprint || 'Not available'}
                </span>
              </div>

              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', lineHeight: 1.5, marginTop: 16 }}>
                <strong>3rd-Party Verification Instructions:</strong> This evaluation carries an unforgeable digital certificate signed by DigiCert's Trusted Time-Stamp Authority (TSA) in compliance with the RFC 3161 standard. To verify that this assessment is authentic, has not been modified, and was certified on this exact date:
                <ol style={{ paddingLeft: 16, marginTop: 6, display: 'flex', flexDirection: 'column', gap: 4 }}>
                  <li>Visit the public V25 Verification Portal at: <strong style={{ color: 'var(--accent-blue)' }}>http://136.119.133.178:4003/verify</strong> and enter the SHA-256 fingerprint shown above. This will instantly query the immutable server logs to verify all assessment details.</li>
                  <li>Alternatively, click <strong>Download TSR Signature</strong> to download the binary <code>.tsr</code> file and verify it directly via OpenSSL:
                    <code style={{ display: 'block', margin: '4px 0', background: 'rgba(0,0,0,0.2)', padding: '4px 8px', borderRadius: 4, fontFamily: 'monospace', fontSize: '0.73rem', wordBreak: 'break-all' }}>
                      openssl ts -reply -in V25_TSA_Certificate.tsr -text
                    </code>
                  </li>
                  <li>This command uses standard public key cryptography to prove that this exact fingerprint was officially registered by DigiCert's root servers at this precise atomic time.</li>
                </ol>
              </div>
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

  // Admin form state
  const [formKey, setFormKey] = useState('')
  const [formOwner, setFormOwner] = useState('')
  const [formLimit, setFormLimit] = useState(-1)
  const [formAdmin, setFormAdmin] = useState(false)
  const [adminError, setAdminError] = useState(null)
  const [adminSuccess, setAdminSuccess] = useState(null)
  const [visibleKeys, setVisibleKeys] = useState({})

  // Admin global config state
  const [formConcurrency, setFormConcurrency] = useState('')
  const [concurrencySuccess, setConcurrencySuccess] = useState(null)
  const [concurrencyError, setConcurrencyError] = useState(null)

  // Admin backup state
  const [backupLoading, setBackupLoading] = useState(false)
  const [backupSuccess, setBackupSuccess] = useState(null)
  const [backupWarning, setBackupWarning] = useState(null)
  const [backupError, setBackupError] = useState(null)

  async function handleRunBackup() {
    setBackupLoading(true)
    setBackupSuccess(null)
    setBackupWarning(null)
    setBackupError(null)

    try {
      const res = await fetch(`/api/admin/backup?api_key=${encodeURIComponent(apiKey)}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': apiKey
        }
      })

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }))
        throw new Error(err.detail || 'Backup request failed.')
      }

      const data = await res.json()
      if (data.status === 'warning') {
        setBackupWarning(data.message)
      } else {
        setBackupSuccess(data.message)
      }
    } catch (e) {
      setBackupError(e.message)
    } finally {
      setBackupLoading(false)
    }
  }

  // Load config on admin load
  useEffect(() => {
    if (info && info.admin) {
      async function loadConfig() {
        try {
          const res = await fetch(`/api/admin/config?api_key=${encodeURIComponent(apiKey)}`)
          if (res.ok) {
            const data = await res.json()
            setFormConcurrency(data.concurrency_limit.toString())
          }
        } catch (e) {
          // ignore
        }
      }
      loadConfig()
    }
  }, [info])

  async function handleSaveConfig(e) {
    e.preventDefault()
    setConcurrencySuccess(null)
    setConcurrencyError(null)

    const parsedLimit = parseInt(formConcurrency)
    if (isNaN(parsedLimit) || parsedLimit < 1) {
      setConcurrencyError('Please enter a valid positive number for the concurrency limit.')
      return
    }

    try {
      const res = await fetch(`/api/admin/config?api_key=${encodeURIComponent(apiKey)}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': apiKey
        },
        body: JSON.stringify({
          concurrency_limit: parsedLimit
        })
      })

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }))
        throw new Error(err.detail || 'Failed to update concurrency limit.')
      }

      setConcurrencySuccess('Successfully updated global concurrency limit live!')
      checkUsage()
    } catch (e) {
      setConcurrencyError(e.message)
    }
  }

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

  function resetForm() {
    setFormKey('')
    setFormOwner('')
    setFormLimit(-1)
    setFormAdmin(false)
    setAdminError(null)
    setAdminSuccess(null)
  }

  async function handleSaveKey(e) {
    e.preventDefault()
    setAdminError(null)
    setAdminSuccess(null)

    if (!formOwner.trim()) {
      setAdminError('Owner Name is required.')
      return
    }

    try {
      const res = await fetch(`/api/admin/keys?api_key=${encodeURIComponent(apiKey)}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': apiKey
        },
        body: JSON.stringify({
          key: formKey,
          owner: formOwner,
          rate_limit: formLimit,
          rate_window: 3600,
          admin: formAdmin
        })
      })

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }))
        throw new Error(err.detail || 'Failed to save key.')
      }

      const result = await res.json()
      setAdminSuccess(`Successfully saved key for ${result.owner}!`)
      resetForm()
      checkUsage()
    } catch (e) {
      setAdminError(e.message)
    }
  }

  async function handleDeleteKey(targetKey) {
    if (!window.confirm('Are you absolutely sure you want to permanently delete this API Key?')) {
      return
    }
    setAdminError(null)
    setAdminSuccess(null)

    try {
      const res = await fetch(`/api/admin/keys/delete?api_key=${encodeURIComponent(apiKey)}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': apiKey
        },
        body: JSON.stringify({
          key: targetKey
        })
      })

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }))
        throw new Error(err.detail || 'Failed to delete key.')
      }

      setAdminSuccess('Successfully deleted API Key.')
      checkUsage()
    } catch (e) {
      setAdminError(e.message)
    }
  }

  function handleEditKey(k) {
    setFormKey(k.key)
    setFormOwner(k.owner)
    setFormLimit(k.rate_limit)
    setFormAdmin(k.admin)
    setAdminError(null)
    setAdminSuccess(null)
  }

  function toggleKeyVisibility(k) {
    setVisibleKeys((prev) => ({
      ...prev,
      [k]: !prev[k]
    }))
  }

  useEffect(() => {
    if (apiKey) {
      checkUsage()
    }
  }, [])

  return (
    <div className="usage-container" style={{ maxWidth: info && info.admin ? '1000px' : '600px' }}>
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

          {info.admin && (
            <div className="usage-card" style={{ marginTop: 32 }}>
              <h3 style={{ fontSize: '1.2rem', marginBottom: 16, borderBottom: '1px solid var(--border)', paddingBottom: 10, color: 'var(--accent-orange)' }}>👑 Admin Control Panel</h3>
              
              {/* Database GCS Backup Control */}
              <div style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border)', borderRadius: 10, padding: 20, marginBottom: 24, textAlign: 'left' }}>
                <h4 style={{ fontSize: '0.95rem', marginBottom: 10, color: 'var(--accent-green)' }}>
                  💾 GCS Cloud Backup Manager
                </h4>
                <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: 14 }}>
                  Trigger an on-demand full database snapshot. This backs up your API Keys, global configurations, and verification logs, copy-mirroring the archive directly to Google Cloud Storage (GCS) at <code>reneu001/timestamps-database-backup</code>.
                </p>

                {backupError && <div className="error-msg" style={{ marginBottom: 14, padding: '8px 12px', fontSize: '0.8rem' }}>{backupError}</div>}
                {backupWarning && <div style={{ color: 'var(--accent-orange)', background: 'rgba(255, 140, 0, 0.1)', border: '1px solid rgba(255, 140, 0, 0.25)', borderRadius: 6, padding: '8px 12px', fontSize: '0.8rem', marginBottom: 14 }}>{backupWarning}</div>}
                {backupSuccess && <div style={{ color: 'var(--accent-green)', background: 'rgba(46, 204, 113, 0.1)', border: '1px solid rgba(46, 204, 113, 0.25)', borderRadius: 6, padding: '8px 12px', fontSize: '0.8rem', marginBottom: 14 }}>{backupSuccess}</div>}

                <button 
                  onClick={handleRunBackup}
                  disabled={backupLoading}
                  style={{ 
                    padding: '10px 20px', 
                    background: 'var(--accent-green)', 
                    color: '#000', 
                    border: 'none', 
                    borderRadius: 6, 
                    fontWeight: 700, 
                    cursor: 'pointer', 
                    fontSize: '0.85rem',
                    opacity: backupLoading ? 0.7 : 1
                  }}
                >
                  {backupLoading ? 'Backing up & Uploading...' : 'Run Database GCS Backup'}
                </button>
              </div>

              {/* Dynamic Concurrency Control */}
              <div style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border)', borderRadius: 10, padding: 20, marginBottom: 24 }}>
                <h4 style={{ fontSize: '0.95rem', marginBottom: 10, color: 'var(--accent-cyan)' }}>
                  ⚙️ Dynamic Concurrency Control
                </h4>
                <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: 14 }}>
                  Adjust the maximum number of concurrent pipeline evaluations permitted globally across all API keys. This takes effect instantly in-memory without interrupting active predictions!
                </p>

                {concurrencyError && <div className="error-msg" style={{ marginBottom: 14, padding: '8px 12px', fontSize: '0.8rem' }}>{concurrencyError}</div>}
                {concurrencySuccess && <div style={{ color: 'var(--accent-green)', background: 'rgba(46, 204, 113, 0.1)', border: '1px solid rgba(46, 204, 113, 0.25)', borderRadius: 6, padding: '8px 12px', fontSize: '0.8rem', marginBottom: 14 }}>{concurrencySuccess}</div>}

                <form onSubmit={handleSaveConfig} style={{ display: 'flex', gap: 14, alignItems: 'flex-end', flexWrap: 'wrap' }}>
                  <div className="form-group" style={{ flex: 1, minWidth: 200 }}>
                    <label style={{ display: 'block', fontSize: '0.78rem', marginBottom: 4, color: 'var(--text-secondary)' }}>Max Global Concurrent Runs</label>
                    <input
                      type="number"
                      required
                      min="1"
                      max="5000"
                      value={formConcurrency}
                      onChange={(e) => setFormConcurrency(e.target.value)}
                      style={{ width: '100%', padding: '8px 12px', background: 'var(--bg-primary)', border: '1px solid var(--border)', borderRadius: 6, color: '#fff', fontSize: '0.85rem' }}
                    />
                  </div>
                  <button type="submit" style={{ padding: '9px 20px', background: 'var(--accent-blue)', color: '#000', border: 'none', borderRadius: 6, fontWeight: 700, cursor: 'pointer', fontSize: '0.85rem' }}>
                    Apply Limit Live
                  </button>
                </form>
              </div>

              {/* Key Management Form */}
              <div style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border)', borderRadius: 10, padding: 20, marginBottom: 24 }}>
                <h4 style={{ fontSize: '0.95rem', marginBottom: 14, color: 'var(--text-primary)' }}>
                  {formKey ? '✏️ Edit API Key' : '➕ Register New API Key'}
                </h4>
                
                {adminError && <div className="error-msg" style={{ marginBottom: 14, padding: '8px 12px', fontSize: '0.8rem' }}>{adminError}</div>}
                {adminSuccess && <div style={{ color: 'var(--accent-green)', background: 'rgba(46, 204, 113, 0.1)', border: '1px solid rgba(46, 204, 113, 0.25)', borderRadius: 6, padding: '8px 12px', fontSize: '0.8rem', marginBottom: 14 }}>{adminSuccess}</div>}

                <form onSubmit={handleSaveKey} style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
                  <div className="form-group" style={{ gridColumn: 'span 2' }}>
                    <label style={{ display: 'block', fontSize: '0.78rem', marginBottom: 4, color: 'var(--text-secondary)' }}>Owner Name</label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. New User"
                      value={formOwner}
                      onChange={(e) => setFormOwner(e.target.value)}
                      style={{ width: '100%', padding: '8px 12px', background: 'var(--bg-primary)', border: '1px solid var(--border)', borderRadius: 6, color: '#fff', fontSize: '0.85rem' }}
                    />
                  </div>

                  <div className="form-group" style={{ gridColumn: 'span 2' }}>
                    <label style={{ display: 'block', fontSize: '0.78rem', marginBottom: 4, color: 'var(--text-secondary)' }}>
                      {formKey ? 'API Key (Protected)' : 'API Key (Optional - leave blank to auto-generate)'}
                    </label>
                    <input
                      type="text"
                      disabled={!!formKey}
                      placeholder={formKey ? '' : "e.g. custom_key_string..."}
                      value={formKey}
                      onChange={(e) => setFormKey(e.target.value)}
                      style={{ width: '100%', padding: '8px 12px', background: formKey ? 'var(--bg-card)' : 'var(--bg-primary)', border: '1px solid var(--border)', borderRadius: 6, color: '#fff', fontSize: '0.85rem', opacity: formKey ? 0.6 : 1 }}
                    />
                  </div>

                  <div className="form-group">
                    <label style={{ display: 'block', fontSize: '0.78rem', marginBottom: 4, color: 'var(--text-secondary)' }}>Hourly Limit</label>
                    <input
                      type="number"
                      required
                      placeholder="Use -1 for unlimited"
                      value={formLimit}
                      onChange={(e) => setFormLimit(parseInt(e.target.value) || -1)}
                      style={{ width: '100%', padding: '8px 12px', background: 'var(--bg-primary)', border: '1px solid var(--border)', borderRadius: 6, color: '#fff', fontSize: '0.85rem' }}
                    />
                  </div>

                  <div className="form-group" style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 20 }}>
                    <input
                      type="checkbox"
                      id="formAdmin"
                      checked={formAdmin}
                      onChange={(e) => setFormAdmin(e.target.checked)}
                      style={{ cursor: 'pointer', width: 16, height: 16 }}
                    />
                    <label htmlFor="formAdmin" style={{ fontSize: '0.85rem', color: 'var(--text-primary)', cursor: 'pointer', fontWeight: 600 }}>Grant Admin Power</label>
                  </div>

                  <div style={{ gridColumn: 'span 2', display: 'flex', gap: 10, marginTop: 10 }}>
                    <button type="submit" style={{ padding: '8px 16px', background: 'var(--accent-orange)', color: '#000', border: 'none', borderRadius: 6, fontWeight: 700, cursor: 'pointer', fontSize: '0.85rem' }}>
                      {formKey ? 'Save Changes' : 'Register Key'}
                    </button>
                    {formKey && (
                      <button type="button" onClick={resetForm} style={{ padding: '8px 16px', background: 'var(--bg-primary)', border: '1px solid var(--border)', color: 'var(--text-primary)', borderRadius: 6, cursor: 'pointer', fontSize: '0.85rem' }}>
                        Cancel Edit
                      </button>
                    )}
                  </div>
                </form>
              </div>

              {/* Keys Table */}
              <h4 style={{ fontSize: '1rem', marginBottom: 12, color: 'var(--text-primary)' }}>🔑 All Active API Keys</h4>
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid var(--border)', color: 'var(--text-muted)' }}>
                      <th style={{ textAlign: 'left', padding: '10px 8px' }}>Owner</th>
                      <th style={{ textAlign: 'left', padding: '10px 8px' }}>API Key</th>
                      <th style={{ textAlign: 'center', padding: '10px 8px' }}>Limit</th>
                      <th style={{ textAlign: 'center', padding: '10px 8px' }}>Predictions</th>
                      <th style={{ textAlign: 'center', padding: '10px 8px' }}>Role</th>
                      <th style={{ textAlign: 'right', padding: '10px 8px' }}>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {info.all_keys && info.all_keys.map((k) => {
                      const isVisible = visibleKeys[k.key];
                      return (
                        <tr key={k.key} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                          <td style={{ padding: '10px 8px', fontWeight: 600, color: 'var(--text-primary)' }}>{k.owner}</td>
                          <td style={{ padding: '10px 8px', fontFamily: 'monospace', color: 'var(--text-secondary)' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                              <span>{isVisible ? k.key : '••••••••••••••••••••••••'}</span>
                              <button
                                onClick={() => toggleKeyVisibility(k.key)}
                                style={{ background: 'none', border: 'none', color: 'var(--accent-blue)', cursor: 'pointer', fontSize: '0.75rem', padding: 2 }}
                                title={isVisible ? "Hide API Key" : "Show API Key"}
                              >
                                {isVisible ? '🙈' : '👁️'}
                              </button>
                            </div>
                          </td>
                          <td style={{ padding: '10px 8px', textAlign: 'center', color: k.rate_limit < 0 ? 'var(--accent-green)' : 'var(--text-primary)' }}>
                            {k.rate_limit < 0 ? 'Unlimited' : k.rate_limit}
                          </td>
                          <td style={{ padding: '10px 8px', textAlign: 'center', fontWeight: 700 }}>
                            {k.stats?.total_predictions || 0}
                          </td>
                          <td style={{ padding: '10px 8px', textAlign: 'center' }}>
                            {k.admin ? '👑 Admin' : 'User'}
                          </td>
                          <td style={{ padding: '10px 8px', textAlign: 'right' }}>
                            <button
                              onClick={() => handleEditKey(k)}
                              style={{ background: 'none', border: 'none', color: 'var(--accent-blue)', cursor: 'pointer', marginRight: 10, fontSize: '0.8rem', fontWeight: 600 }}
                            >
                              Edit
                            </button>
                            <button
                              disabled={k.key === 'v25_stelios_unlimited_a28b6d39c04f5e71'}
                              onClick={() => handleDeleteKey(k.key)}
                              style={{ background: 'none', border: 'none', color: k.key === 'v25_stelios_unlimited_a28b6d39c04f5e71' ? 'var(--text-muted)' : 'var(--accent-red)', cursor: k.key === 'v25_stelios_unlimited_a28b6d39c04f5e71' ? 'default' : 'pointer', fontSize: '0.8rem', fontWeight: 600 }}
                            >
                              Delete
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}

      <a href="/" className="usage-btn" style={{ marginTop: 12 }}>&larr; Back to Predictor App</a>
    </div>
  )
}

function VerifyPage() {
  const [hash, setHash] = useState('')
  const [record, setRecord] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)

  async function handleVerify(e) {
    if (e) e.preventDefault()
    if (!hash.trim()) {
      setError('Please enter a SHA-256 fingerprint.')
      return
    }
    setLoading(true)
    setError(null)
    setRecord(null)
    try {
      const res = await fetch(`/api/verify?hash=${encodeURIComponent(hash.trim())}`)
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }))
        throw new Error(err.detail || 'Failed to verify fingerprint.')
      }
      const data = await res.json()
      setRecord(data)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  // Auto-load if hash is in URL query parameters!
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const h = params.get('hash')
    if (h) {
      setHash(h)
      // We can trigger it using setTimeout to let state settle
      setTimeout(() => {
        const btn = document.getElementById('verify-submit-btn')
        if (btn) btn.click()
      }, 100)
    }
  }, [])

  return (
    <div className="usage-container" style={{ maxWidth: '800px' }}>
      <h2 className="usage-title">🛡️ V25 Prediction Verification Portal</h2>
      <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', textAlign: 'center', marginBottom: 24 }}>
        Input any V25 SHA-256 evaluation fingerprint to retrieve its certified immutable details and DigiCert Trusted TSR Certificate.
      </p>

      <form onSubmit={handleVerify} style={{ marginBottom: 24 }}>
        <div className="form-group">
          <label style={{ display: 'block', marginBottom: 8, fontWeight: 600 }}>SHA-256 Fingerprint</label>
          <div style={{ display: 'flex', gap: 10 }}>
            <input
              type="text"
              placeholder="Paste SHA-256 fingerprint (e.g. d68abf040...)"
              value={hash}
              onChange={(e) => setHash(e.target.value)}
              style={{
                flex: 1,
                background: 'var(--bg-secondary)',
                border: '1px solid var(--border)',
                borderRadius: 8,
                padding: '10px 14px',
                color: 'var(--text-primary)',
                fontFamily: 'monospace',
                fontSize: '0.85rem'
              }}
            />
            <button
              id="verify-submit-btn"
              type="submit"
              disabled={loading}
              style={{
                background: 'var(--accent-blue)',
                color: '#000',
                border: 'none',
                borderRadius: 8,
                padding: '10px 24px',
                fontWeight: 700,
                cursor: 'pointer'
              }}
            >
              {loading ? 'Verifying...' : 'Verify'}
            </button>
          </div>
        </div>
      </form>

      {error && <div className="error-msg" style={{ marginBottom: 24 }}>{error}</div>}

      {record && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          <div className="usage-card" style={{ border: '1px solid var(--accent-blue)', background: 'rgba(74, 158, 255, 0.02)', textAlign: 'left' }}>
            <h3 style={{ fontSize: '1.1rem', marginBottom: 16, borderBottom: '1px solid var(--border)', paddingBottom: 10, color: 'var(--accent-blue)' }}>🔬 Verified Prediction Record</h3>
            <div className="usage-item">
              <span className="usage-label">Authorized Owner:</span>
              <span className="usage-value active">{record.owner || 'Registered User'}</span>
            </div>
            <div className="usage-item" style={{ borderBottom: '1px solid rgba(255,255,255,0.05)', padding: '8px 0', display: 'flex', justifyContent: 'space-between' }}>
              <span className="usage-label">SMILES String:</span>
              <span className="usage-value" style={{ fontFamily: 'monospace', fontSize: '0.75rem', wordBreak: 'break-all', textAlign: 'right', maxWidth: '60%' }}>{record.smiles}</span>
            </div>
            <div className="usage-item">
              <span className="usage-label">Target Class:</span>
              <span className="usage-value">{record.target}</span>
            </div>
            <div className="usage-item">
              <span className="usage-label">Therapeutic Indication:</span>
              <span className="usage-value">{record.indication}</span>
            </div>
          </div>

          <div className="usage-card" style={{ border: '1px solid var(--accent-green)', background: 'rgba(46, 204, 113, 0.02)', textAlign: 'left' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid rgba(46, 204, 113, 0.15)', paddingBottom: 12, marginBottom: 16, flexWrap: 'wrap', gap: 10 }}>
              <div>
                <h3 style={{ fontSize: '1.1rem', margin: 0, color: 'var(--accent-green)' }}>🛡️ DigiCert Time-Stamp Certificate</h3>
                <div style={{ fontSize: '0.73rem', color: 'var(--text-muted)', marginTop: 4 }}>RFC 3161 Globally Trusted Digital Signature</div>
              </div>
              <div style={{ display: 'flex', gap: 10 }}>
                {record.tsa_manifest && (
                  <button
                    onClick={() => {
                      const blob = new Blob([record.tsa_manifest], { type: 'text/plain' });
                      const url = URL.createObjectURL(blob);
                      const a = document.createElement('a');
                      a.href = url;
                      a.download = `V25_Prediction_Manifest_${record.tsa_timestamp ? record.tsa_timestamp.slice(0,10) : 'verification'}.txt`;
                      a.click();
                    }}
                    style={{
                      background: 'rgba(74, 158, 255, 0.15)',
                      color: 'var(--accent-blue)',
                      border: '1px solid rgba(74, 158, 255, 0.3)',
                      borderRadius: 6,
                      padding: '8px 14px',
                      fontSize: '0.8rem',
                      fontWeight: 700,
                      cursor: 'pointer'
                    }}
                  >
                    📄 Download Manifest
                  </button>
                )}
                {record.tsa_signature_b64 && (
                  <button
                    onClick={() => {
                      const bin = atob(record.tsa_signature_b64);
                      const arr = new Uint8Array(bin.length);
                      for (let i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i);
                      const blob = new Blob([arr], { type: 'application/timestamp-reply' });
                      const url = URL.createObjectURL(blob);
                      const a = document.createElement('a');
                      a.href = url;
                      a.download = `V25_TSA_Certificate_${record.tsa_timestamp ? record.tsa_timestamp.slice(0,10) : 'verification'}.tsr`;
                      a.click();
                    }}
                    style={{
                      background: 'rgba(46, 204, 113, 0.15)',
                      color: 'var(--accent-green)',
                      border: '1px solid rgba(46, 204, 113, 0.3)',
                      borderRadius: 6,
                      padding: '8px 14px',
                      fontSize: '0.8rem',
                      fontWeight: 700,
                      cursor: 'pointer'
                    }}
                  >
                    📥 Download TSR Signature
                  </button>
                )}
              </div>
            </div>

            <div className="usage-item">
              <span className="usage-label">Certified Timestamp:</span>
              <span className="usage-value active" style={{ color: 'var(--accent-green)', fontWeight: 700 }}>
                {record.tsa_timestamp ? new Date(record.tsa_timestamp).toUTCString() : 'N/A'}
              </span>
            </div>
            <div className="usage-item" style={{ flexDirection: 'column', alignItems: 'flex-start', gap: 4 }}>
              <span className="usage-label">Verified Fingerprint (SHA-256 Hash):</span>
              <span className="usage-value" style={{ fontFamily: 'monospace', fontSize: '0.75rem', color: 'var(--text-secondary)', wordBreak: 'break-all' }}>{record.tsa_fingerprint}</span>
            </div>

            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', lineHeight: 1.5, marginTop: 16, borderTop: '1px solid rgba(255,255,255,0.05)', paddingTop: 14 }}>
              <strong>How to Audit this Signature:</strong>
              <ol style={{ paddingLeft: 16, marginTop: 6, display: 'flex', flexDirection: 'column', gap: 4 }}>
                <li>Click <strong>Download Manifest</strong> to download the plain-text <code>V25_Prediction_Manifest.txt</code> file.</li>
                <li>Click <strong>Download TSR Signature</strong> to download the binary <code>V25_TSA_Certificate.tsr</code> signature token.</li>
                <li>Audit both files together to prove mathematical authenticity using OpenSSL:
                  <code style={{ display: 'block', margin: '4px 0', background: 'rgba(0,0,0,0.2)', padding: '4px 8px', borderRadius: 4, fontFamily: 'monospace', fontSize: '0.73rem', wordBreak: 'break-all' }}>
                    openssl ts -verify -data V25_Prediction_Manifest.txt -in V25_TSA_Certificate.tsr -token_in
                  </code>
                </li>
                <li>A successful output prints <code>Verification: OK</code>, certifying that this exact prediction manifest was officially signed by DigiCert on this specific date.</li>
              </ol>
            </div>
          </div>
        </div>
      )}

      <a href="/" className="usage-btn" style={{ marginTop: 24 }}>&larr; Back to Predictor App</a>
    </div>
  )
}
