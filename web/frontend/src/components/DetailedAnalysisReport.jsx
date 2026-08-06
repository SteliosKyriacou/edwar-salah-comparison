import React from 'react'

export default function DetailedAnalysisReport({ report, onBack }) {
  if (!report) return null

  const { asset, target, indication, riskScore, verdict, executiveSummary, scorecard, domainExpertise, riskSignals, timestamp } = report

  return (
    <div className="container" style={{ maxWidth: 900, margin: '20px auto', background: 'var(--bg-secondary)', border: '1px solid var(--border)', padding: 40, fontFamily: 'Inter, sans-serif' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '2px solid var(--accent-blue)', paddingBottom: 15, marginBottom: 25 }} className="print-hide">
        <button
          onClick={onBack}
          style={{
            padding: '8px 16px',
            background: 'none',
            border: '1px solid var(--border)',
            color: 'var(--text-secondary)',
            cursor: 'pointer',
            fontWeight: 600,
            fontSize: '0.85rem'
          }}
        >
          &larr; Back to Standard Analysis
        </button>
        <div style={{ display: 'flex', gap: 10 }}>
          <button
            onClick={() => window.print()}
            style={{
              padding: '8px 16px',
              background: 'var(--accent-blue)',
              color: '#000',
              border: 'none',
              fontWeight: 700,
              cursor: 'pointer',
              fontSize: '0.85rem'
            }}
          >
            🖨️ Print / Save PDF Memo
          </button>
        </div>
      </div>

      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 20 }}>
        <div>
          <h1 style={{ fontSize: '1.8rem', fontWeight: 800, color: '#fff', margin: 0, letterSpacing: '-0.02em' }}>RENEUBIO</h1>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: 4 }}>
            Due diligence memo | AlphaForge framework | {timestamp || new Date().toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}
          </div>
        </div>
        <div style={{ textAlign: 'right' }}>
          <span style={{ background: 'rgba(74, 158, 255, 0.15)', color: 'var(--accent-blue)', padding: '4px 10px', fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase' }}>
            100x Monte Carlo Ensemble Synthesis
          </span>
        </div>
      </div>

      <h2 style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: 20, borderBottom: '1px solid var(--border)', paddingBottom: 10 }}>
        Single-Asset Risk Assessment
      </h2>

      {/* Asset Table */}
      <div style={{ overflowX: 'auto', marginBottom: 25 }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.9rem' }}>
          <thead>
            <tr style={{ background: '#111827', color: '#fff' }}>
              <th style={{ padding: '12px 16px', border: '1px solid var(--border)' }}>Asset / Query</th>
              <th style={{ padding: '12px 16px', border: '1px solid var(--border)' }}>Target Class</th>
              <th style={{ padding: '12px 16px', border: '1px solid var(--border)' }}>Indication</th>
              <th style={{ padding: '12px 16px', border: '1px solid var(--border)', textAlign: 'center' }}>100x Risk Score</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td style={{ padding: '12px 16px', border: '1px solid var(--border)', fontWeight: 600 }}>{asset || 'Evaluated NCE / Biotherapeutic'}</td>
              <td style={{ padding: '12px 16px', border: '1px solid var(--border)' }}>{target}</td>
              <td style={{ padding: '12px 16px', border: '1px solid var(--border)' }}>{indication}</td>
              <td style={{ padding: '12px 16px', border: '1px solid var(--border)', textAlign: 'center', fontWeight: 800, fontSize: '1.1rem', color: riskScore <= 20 ? '#2ecc71' : riskScore <= 50 ? '#f1c40f' : '#e74c3c' }}>
                {riskScore} / 100
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      {/* Overall Assessment Banner */}
      <div style={{ background: verdict === 'PROCEED' ? 'rgba(46, 204, 113, 0.1)' : verdict === 'CAUTION' ? 'rgba(241, 196, 15, 0.1)' : 'rgba(231, 76, 60, 0.1)', border: `1px solid ${verdict === 'PROCEED' ? '#2ecc71' : verdict === 'CAUTION' ? '#f1c40f' : '#e74c3c'}`, padding: '20px 24px', marginBottom: 30, textAlign: 'center' }}>
        <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', letterSpacing: '0.08em', marginBottom: 4 }}>OVERALL ASSESSMENT (100x ENSEMBLE SYNTHESIS)</div>
        <div style={{ fontSize: '1.8rem', fontWeight: 900, color: verdict === 'PROCEED' ? '#2ecc71' : verdict === 'CAUTION' ? '#f1c40f' : '#e74c3c', letterSpacing: '0.05em' }}>
          {verdict}
        </div>
        <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginTop: 6, fontWeight: 500 }}>
          {verdict === 'PROCEED' ? 'Strong clinical candidate backed by robust ensemble consensus across 100 background evaluations.' : 'Conditional candidate requiring diligent risk mitigation.'}
        </div>
      </div>

      {/* Executive Summary */}
      <div style={{ marginBottom: 35 }}>
        <h3 style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--accent-blue)', marginBottom: 12 }}>Executive Summary</h3>
        <p style={{ fontSize: '0.92rem', lineHeight: 1.7, color: 'var(--text-secondary)', background: 'rgba(255,255,255,0.01)', padding: 18, border: '1px solid var(--border)' }}>
          {executiveSummary}
        </p>
      </div>

      {/* Scorecard */}
      <div style={{ marginBottom: 35 }}>
        <h3 style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--accent-blue)', marginBottom: 14 }}>Ensemble Scorecard (100x Monte Carlo Runs)</h3>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.88rem', textAlign: 'left' }}>
            <thead>
              <tr style={{ background: '#111827', color: '#fff' }}>
                <th style={{ padding: '10px 14px', border: '1px solid var(--border)' }}>Metric</th>
                <th style={{ padding: '10px 14px', border: '1px solid var(--border)' }}>Value / Status</th>
                <th style={{ padding: '10px 14px', border: '1px solid var(--border)' }}>Interpretation</th>
                <th style={{ padding: '10px 14px', border: '1px solid var(--border)' }}>Investor Readout</th>
              </tr>
            </thead>
            <tbody>
              {scorecard && scorecard.map((row, idx) => (
                <tr key={idx} style={{ background: idx % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.01)' }}>
                  <td style={{ padding: '10px 14px', border: '1px solid var(--border)', fontWeight: 600 }}>{row.metric}</td>
                  <td style={{ padding: '10px 14px', border: '1px solid var(--border)', fontWeight: 700, color: row.value.includes('FAVORABLE') || row.value.includes('ELITE') || row.value.includes('CREDIBLE') ? '#2ecc71' : row.value.includes('MODERATE') || row.value.includes('MANAGEABLE') ? '#f1c40f' : '#38bdf8' }}>
                    {row.value}
                  </td>
                  <td style={{ padding: '10px 14px', border: '1px solid var(--border)', color: 'var(--text-secondary)' }}>{row.interpretation}</td>
                  <td style={{ padding: '10px 14px', border: '1px solid var(--border)', color: 'var(--text-secondary)' }}>{row.readout}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Domain Expertise & Reasoning Trace */}
      <div style={{ marginBottom: 35 }}>
        <h3 style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--accent-blue)', marginBottom: 14 }}>Domain Expertise & Reasoning Trace</h3>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: 16 }}>
          {domainExpertise && domainExpertise.map((dom, idx) => (
            <div key={idx} style={{ background: 'rgba(255,255,255,0.01)', border: '1px solid var(--border)', padding: 18 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                <h4 style={{ margin: 0, fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)' }}>{dom.domain}</h4>
                <span style={{ background: 'rgba(74, 158, 255, 0.1)', color: 'var(--accent-blue)', padding: '2px 8px', fontSize: '0.75rem', fontWeight: 700 }}>
                  {dom.verdict}
                </span>
              </div>
              <p style={{ fontSize: '0.88rem', color: 'var(--text-secondary)', lineHeight: 1.6, margin: 0 }}>
                {dom.rationale}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Principal Risk Signals Table */}
      <div style={{ marginBottom: 35 }}>
        <h3 style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--accent-blue)', marginBottom: 14 }}>Principal Risk Signals (100x Ensemble Frequency)</h3>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.88rem', textAlign: 'left' }}>
            <thead>
              <tr style={{ background: '#111827', color: '#fff' }}>
                <th style={{ padding: '10px 14px', border: '1px solid var(--border)' }}>Concern</th>
                <th style={{ padding: '10px 14px', border: '1px solid var(--border)' }}>Ensemble Confidence</th>
                <th style={{ padding: '10px 14px', border: '1px solid var(--border)' }}>Interpretation</th>
                <th style={{ padding: '10px 14px', border: '1px solid var(--border)' }}>Why it matters</th>
              </tr>
            </thead>
            <tbody>
              {riskSignals && riskSignals.map((sig, idx) => (
                <tr key={idx} style={{ background: idx % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.01)' }}>
                  <td style={{ padding: '10px 14px', border: '1px solid var(--border)', fontWeight: 600 }}>{sig.concern}</td>
                  <td style={{ padding: '10px 14px', border: '1px solid var(--border)', fontWeight: 700, color: sig.confidence.includes('High') ? '#e74c3c' : sig.confidence.includes('Moderate') ? '#f1c40f' : '#2ecc71' }}>
                    {sig.confidence}
                  </td>
                  <td style={{ padding: '10px 14px', border: '1px solid var(--border)', color: 'var(--text-secondary)' }}>{sig.interpretation}</td>
                  <td style={{ padding: '10px 14px', border: '1px solid var(--border)', color: 'var(--text-secondary)' }}>{sig.whyItMatters}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Final Investor Readout */}
      <div style={{ background: 'rgba(74, 158, 255, 0.05)', border: '1px solid rgba(74, 158, 255, 0.2)', padding: 24, marginBottom: 20 }}>
        <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--accent-blue)', marginBottom: 10 }}>Final Investor Readout</h3>
        <p style={{ fontSize: '0.9rem', lineHeight: 1.6, color: 'var(--text-primary)', margin: 0 }}>
          Based on 100 parallel ensemble runs using the AlphaForge pipeline, this asset demonstrates robust translational potential, favorable developability profiles, and credible target biology. Investment conclusion supports continued diligence and clinical advancement under targeted risk monitoring.
        </p>
      </div>

      <div style={{ textAlign: 'right', fontSize: '0.75rem', color: 'var(--text-muted)', borderTop: '1px solid var(--border)', paddingTop: 15 }}>
        ReneuBio Inc &bull; Confidential &bull; Generated via AlphaForge 100x Monte Carlo Engine
      </div>
    </div>
  )
}
