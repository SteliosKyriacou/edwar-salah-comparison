import React from 'react'

export default function DetailedAnalysisReport({ report, onBack }) {
  if (!report) return null

  const { asset, target, indication, riskScore, verdict, executiveSummary, scorecard, domainExpertise, riskSignals, timestamp } = report

  const verdictColor = verdict === 'PROCEED' ? '#2ecc71' : verdict === 'CAUTION' ? '#f1c40f' : '#e74c3c'

  return (
    <div className="container" style={{ maxWidth: 950, margin: '20px auto', background: '#0d1117', border: '1px solid var(--border)', padding: 50, fontFamily: 'Inter, sans-serif', color: '#e0e6ed' }}>
      <style>{`
        @media print {
          body { background: #fff !important; color: #000 !important; }
          .print-hide { display: none !important; }
          .memo-page { page-break-after: always; background: #fff !important; color: #000 !important; border: none !important; padding: 0 !important; }
          table { width: 100% !important; border-collapse: collapse !important; }
          th, td { border: 1px solid #ccc !important; color: #000 !important; }
          th { background: #f1f5f9 !important; }
        }
      `}</style>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '2px solid var(--accent-blue)', paddingBottom: 15, marginBottom: 30 }} className="print-hide">
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
            🖨️ Print / Save PDF Memo (7-Page Report)
          </button>
        </div>
      </div>

      {/* PAGE 1: Title, Asset Table, Overall Assessment, Executive Summary, Bottom Line */}
      <div className="memo-page" style={{ marginBottom: 50 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 25, borderBottom: '1px solid #334155', paddingBottom: 15 }}>
          <div>
            <h1 style={{ fontSize: '2rem', fontWeight: 900, color: '#fff', margin: 0, letterSpacing: '-0.03em' }}>RENEUBIO</h1>
            <div style={{ fontSize: '0.8rem', color: '#94a3b8', marginTop: 4 }}>
              Due diligence memo | AlphaForge framework | {timestamp || 'July 31, 2026'}
            </div>
          </div>
          <div style={{ textAlign: 'right' }}>
            <span style={{ background: 'rgba(74, 158, 255, 0.15)', color: '#60a5fa', padding: '4px 12px', fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase' }}>
              Confidential Diligence
            </span>
          </div>
        </div>

        <h2 style={{ fontSize: '1.6rem', fontWeight: 800, color: '#f8fafc', marginBottom: 20, letterSpacing: '-0.01em' }}>
          Single-Asset Risk Assessment
        </h2>

        {/* Asset Table */}
        <div style={{ overflowX: 'auto', marginBottom: 25 }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.9rem' }}>
            <thead>
              <tr style={{ background: '#1e293b', color: '#fff' }}>
                <th style={{ padding: '12px 16px', border: '1px solid #334155' }}>Asset</th>
                <th style={{ padding: '12px 16px', border: '1px solid #334155' }}>Target</th>
                <th style={{ padding: '12px 16px', border: '1px solid #334155' }}>Indication</th>
                <th style={{ padding: '12px 16px', border: '1px solid #334155', textAlign: 'center' }}>Risk score</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td style={{ padding: '12px 16px', border: '1px solid #334155', fontWeight: 600, wordBreak: 'break-all' }}>{asset || 'Evaluated NCE'}</td>
                <td style={{ padding: '12px 16px', border: '1px solid #334155' }}>{target}</td>
                <td style={{ padding: '12px 16px', border: '1px solid #334155' }}>{indication}</td>
                <td style={{ padding: '12px 16px', border: '1px solid #334155', textAlign: 'center', fontWeight: 800, fontSize: '1.1rem', color: riskScore <= 40 ? '#22c55e' : riskScore <= 75 ? '#eab308' : '#ef4444' }}>
                  {riskScore} / 100
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        {/* Overall Assessment Banner */}
        <div style={{ background: verdict === 'PROCEED' ? 'rgba(34, 197, 94, 0.1)' : verdict === 'CAUTION' ? 'rgba(234, 179, 8, 0.1)' : 'rgba(239, 68, 68, 0.1)', border: `1px solid ${verdictColor}`, padding: '20px 24px', marginBottom: 30, textAlign: 'center' }}>
          <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#94a3b8', letterSpacing: '0.08em', marginBottom: 4 }}>OVERALL ASSESSMENT</div>
          <div style={{ fontSize: '1.8rem', fontWeight: 900, color: verdictColor, letterSpacing: '0.05em' }}>
            {verdict}
          </div>
          <div style={{ fontSize: '0.9rem', color: '#cbd5e1', marginTop: 6, fontWeight: 500 }}>
            {verdict === 'PROCEED' ? 'Strong clinical candidate with favorable profile' : verdict === 'CAUTION' ? 'Conditional candidate requiring risk mitigation' : 'High attrition risk candidate'}
          </div>
        </div>

        {/* Bottom Line Callout */}
        <div style={{ background: 'rgba(51, 65, 85, 0.4)', borderLeft: '4px solid #60a5fa', padding: '14px 18px', marginBottom: 25, fontSize: '0.92rem', fontStyle: 'italic', color: '#f1f5f9' }}>
          <strong>Bottom line:</strong> {executiveSummary}
        </div>

        {/* Executive Summary */}
        <div style={{ marginBottom: 30 }}>
          <h3 style={{ fontSize: '1.2rem', fontWeight: 700, color: '#60a5fa', marginBottom: 12 }}>Executive Summary</h3>
          <p style={{ fontSize: '0.9rem', lineHeight: 1.7, color: '#cbd5e1', background: '#111827', padding: 18, border: '1px solid #334155', margin: 0 }}>
            The evaluated asset exhibits a risk score of {riskScore}/100 targeting {target} for {indication}. Intrinsic developability and structural profiles have been assessed across multi-parameter AI models. The principal pivotal uncertainty involves comparative efficacy against established standards of care, metabolic clearance stability, and maintenance of adequate therapeutic exposure across heterogeneous patient cohorts.
          </p>
        </div>

        <div style={{ textAlign: 'right', fontSize: '0.75rem', color: '#64748b', borderTop: '1px solid #334155', paddingTop: 10 }}>
          ReneuBio Inc - Confidential &bull; 1
        </div>
      </div>

      {/* PAGE 2: Scorecard Table */}
      <div className="memo-page" style={{ marginBottom: 50 }}>
        <div style={{ fontSize: '0.8rem', color: '#94a3b8', marginBottom: 15, borderBottom: '1px solid #334155', paddingBottom: 10 }}>
          Due diligence memo | AlphaForge framework | {timestamp || 'July 31, 2026'}
        </div>

        <h3 style={{ fontSize: '1.4rem', fontWeight: 800, color: '#f8fafc', marginBottom: 12 }}>Scorecard</h3>
        <p style={{ fontSize: '0.85rem', color: '#94a3b8', marginBottom: 20, lineHeight: 1.5 }}>
          The probabilities and metrics below should be interpreted as directional and relative, not as precise forecasts. Early clinical estimates are viewed as diagnostic measures of developability, safety, and translational strength.
        </p>

        <div style={{ overflowX: 'auto', marginBottom: 30 }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.88rem', textAlign: 'left' }}>
            <thead>
              <tr style={{ background: '#1e293b', color: '#fff' }}>
                <th style={{ padding: '10px 14px', border: '1px solid #334155' }}>Metric</th>
                <th style={{ padding: '10px 14px', border: '1px solid #334155' }}>Value</th>
                <th style={{ padding: '10px 14px', border: '1px solid #334155' }}>Interpretation</th>
                <th style={{ padding: '10px 14px', border: '1px solid #334155' }}>Investor readout</th>
              </tr>
            </thead>
            <tbody>
              {scorecard && scorecard.map((row, idx) => (
                <tr key={idx} style={{ background: idx % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.01)' }}>
                  <td style={{ padding: '10px 14px', border: '1px solid #334155', fontWeight: 600 }}>{row.metric}</td>
                  <td style={{ padding: '10px 14px', border: '1px solid #334155', fontWeight: 700, color: row.value.includes('FAVORABLE') || row.value.includes('ELITE') || row.value.includes('CREDIBLE') || row.value.includes('CLEAN') || row.value.includes('WORKABLE') ? '#22c55e' : row.value.includes('MODERATE') || row.value.includes('MANAGEABLE') || row.value.includes('CONDITIONAL') ? '#eab308' : '#ef4444' }}>
                    {row.value}
                  </td>
                  <td style={{ padding: '10px 14px', border: '1px solid #334155', color: '#cbd5e1' }}>{row.interpretation}</td>
                  <td style={{ padding: '10px 14px', border: '1px solid #334155', color: '#cbd5e1' }}>{row.readout}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div style={{ textAlign: 'right', fontSize: '0.75rem', color: '#64748b', borderTop: '1px solid #334155', paddingTop: 10 }}>
          ReneuBio Inc - Confidential &bull; 2
        </div>
      </div>

      {/* PAGE 3: Reasoning Trace */}
      <div className="memo-page" style={{ marginBottom: 50 }}>
        <div style={{ fontSize: '0.8rem', color: '#94a3b8', marginBottom: 15, borderBottom: '1px solid #334155', paddingBottom: 10 }}>
          Due diligence memo | AlphaForge framework | {timestamp || 'July 31, 2026'}
        </div>

        <h3 style={{ fontSize: '1.4rem', fontWeight: 800, color: '#f8fafc', marginBottom: 15 }}>Reasoning Trace</h3>
        
        <div style={{ marginBottom: 25 }}>
          <h4 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#60a5fa', marginBottom: 8 }}>Probability Path</h4>
          <p style={{ fontSize: '0.88rem', lineHeight: 1.6, color: '#cbd5e1', marginBottom: 10 }}>
            <strong>Phase 1:</strong> Demonstrates evaluated oral/parenteral feasibility, relevant systemic exposure, and consistent safety parameters. Early developability is substantially de-risked.
          </p>
          <p style={{ fontSize: '0.88rem', lineHeight: 1.6, color: '#cbd5e1', marginBottom: 10 }}>
            <strong>Phase 2:</strong> Translational proof of concept is supported by target engagement and disease-relevant pathway modulation. Subgroup and dose optimization remain key focal points.
          </p>
          <p style={{ fontSize: '0.88rem', lineHeight: 1.6, color: '#cbd5e1', marginBottom: 10 }}>
            <strong>Phase 3:</strong> Pivotal success depends on demonstrating robust comparative efficacy against standard-of-care agents across heterogeneous patient populations while maintaining chronic tolerability.
          </p>
        </div>

        <div style={{ marginBottom: 25 }}>
          <h4 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#60a5fa', marginBottom: 8 }}>Domain Expertise: Biology Verdict</h4>
          {domainExpertise && domainExpertise[0] && (
            <div style={{ background: '#111827', border: '1px solid #334155', padding: 16 }}>
              <div style={{ fontWeight: 700, color: '#22c55e', marginBottom: 6 }}>Verdict: {domainExpertise[0].verdict}</div>
              <p style={{ fontSize: '0.88rem', color: '#cbd5e1', lineHeight: 1.6, margin: 0 }}>
                {domainExpertise[0].rationale}
              </p>
            </div>
          )}
        </div>

        <div style={{ textAlign: 'right', fontSize: '0.75rem', color: '#64748b', borderTop: '1px solid #334155', paddingTop: 10 }}>
          ReneuBio Inc - Confidential &bull; 3
        </div>
      </div>

      {/* PAGE 4: Toxicology, Pharmacology & MedChem */}
      <div className="memo-page" style={{ marginBottom: 50 }}>
        <div style={{ fontSize: '0.8rem', color: '#94a3b8', marginBottom: 15, borderBottom: '1px solid #334155', paddingBottom: 10 }}>
          Due diligence memo | AlphaForge framework | {timestamp || 'July 31, 2026'}
        </div>

        <div style={{ marginBottom: 22 }}>
          <h4 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#60a5fa', marginBottom: 6 }}>Toxicology Verdict</h4>
          {domainExpertise && domainExpertise[1] && (
            <p style={{ fontSize: '0.88rem', lineHeight: 1.6, color: '#cbd5e1', background: '#111827', padding: 14, border: '1px solid #334155', margin: 0 }}>
              <strong>{domainExpertise[1].verdict}:</strong> {domainExpertise[1].rationale}
            </p>
          )}
        </div>

        <div style={{ marginBottom: 22 }}>
          <h4 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#60a5fa', marginBottom: 6 }}>Pharmacology Verdict</h4>
          {domainExpertise && domainExpertise[2] && (
            <p style={{ fontSize: '0.88rem', lineHeight: 1.6, color: '#cbd5e1', background: '#111827', padding: 14, border: '1px solid #334155', margin: 0 }}>
              <strong>{domainExpertise[2].verdict}:</strong> {domainExpertise[2].rationale}
            </p>
          )}
        </div>

        <div style={{ marginBottom: 22 }}>
          <h4 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#60a5fa', marginBottom: 6 }}>MedChem / Structural Assessment</h4>
          {domainExpertise && domainExpertise[3] && (
            <p style={{ fontSize: '0.88rem', lineHeight: 1.6, color: '#cbd5e1', background: '#111827', padding: 14, border: '1px solid #334155', margin: 0 }}>
              <strong>{domainExpertise[3].verdict}:</strong> {domainExpertise[3].rationale}
            </p>
          )}
        </div>

        <div style={{ textAlign: 'right', fontSize: '0.75rem', color: '#64748b', borderTop: '1px solid #334155', paddingTop: 10 }}>
          ReneuBio Inc - Confidential &bull; 4
        </div>
      </div>

      {/* PAGE 5: Principal Risk Signals */}
      <div className="memo-page" style={{ marginBottom: 50 }}>
        <div style={{ fontSize: '0.8rem', color: '#94a3b8', marginBottom: 15, borderBottom: '1px solid #334155', paddingBottom: 10 }}>
          Due diligence memo | AlphaForge framework | {timestamp || 'July 31, 2026'}
        </div>

        <h3 style={{ fontSize: '1.4rem', fontWeight: 800, color: '#f8fafc', marginBottom: 15 }}>Principal Risk Signals</h3>
        <p style={{ fontSize: '0.85rem', color: '#94a3b8', marginBottom: 20, lineHeight: 1.5 }}>
          AlphaForge confidence indicates how strongly the model supports each liability as a credible risk for the asset in this indication.
        </p>

        <div style={{ overflowX: 'auto', marginBottom: 30 }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.88rem', textAlign: 'left' }}>
            <thead>
              <tr style={{ background: '#1e293b', color: '#fff' }}>
                <th style={{ padding: '10px 14px', border: '1px solid #334155' }}>Concern</th>
                <th style={{ padding: '10px 14px', border: '1px solid #334155' }}>Confidence</th>
                <th style={{ padding: '10px 14px', border: '1px solid #334155' }}>Interpretation</th>
                <th style={{ padding: '10px 14px', border: '1px solid #334155' }}>Why it matters</th>
              </tr>
            </thead>
            <tbody>
              {riskSignals && riskSignals.map((sig, idx) => (
                <tr key={idx} style={{ background: idx % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.01)' }}>
                  <td style={{ padding: '10px 14px', border: '1px solid #334155', fontWeight: 600 }}>{sig.concern}</td>
                  <td style={{ padding: '10px 14px', border: '1px solid #334155', fontWeight: 700, color: sig.confidence.includes('High') ? '#ef4444' : sig.confidence.includes('Moderate') ? '#eab308' : '#22c55e' }}>
                    {sig.confidence}
                  </td>
                  <td style={{ padding: '10px 14px', border: '1px solid #334155', color: '#cbd5e1' }}>{sig.interpretation}</td>
                  <td style={{ padding: '10px 14px', border: '1px solid #334155', color: '#cbd5e1' }}>{sig.whyItMatters}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div style={{ textAlign: 'right', fontSize: '0.75rem', color: '#64748b', borderTop: '1px solid #334155', paddingTop: 10 }}>
          ReneuBio Inc - Confidential &bull; 5
        </div>
      </div>

      {/* PAGE 6: Current Clinical and Regulatory Context */}
      <div className="memo-page" style={{ marginBottom: 50 }}>
        <div style={{ fontSize: '0.8rem', color: '#94a3b8', marginBottom: 15, borderBottom: '1px solid #334155', paddingBottom: 10 }}>
          Due diligence memo | AlphaForge framework | {timestamp || 'July 31, 2026'}
        </div>

        <h3 style={{ fontSize: '1.4rem', fontWeight: 800, color: '#f8fafc', marginBottom: 15 }}>Current Clinical and Regulatory Context</h3>
        <p style={{ fontSize: '0.88rem', lineHeight: 1.6, color: '#cbd5e1', marginBottom: 15 }}>
          Clinical development strategies require rigorous validation against standard active comparators. Primary endpoints focus on objective response rate (ORR) and progression-free survival (PFS) in prospectively defined patient populations.
        </p>
        <p style={{ fontSize: '0.88rem', lineHeight: 1.6, color: '#cbd5e1', marginBottom: 20 }}>
          Active-comparator trial designs are clinically demanding but establish clear differentiation pathways. Safety monitoring protocols remain critical across dose-escalation and maintenance schedules.
        </p>

        <div style={{ textAlign: 'right', fontSize: '0.75rem', color: '#64748b', borderTop: '1px solid #334155', paddingTop: 10 }}>
          ReneuBio Inc - Confidential &bull; 6
        </div>
      </div>

      {/* PAGE 7: Final Investor Readout */}
      <div className="memo-page" style={{ marginBottom: 20 }}>
        <div style={{ fontSize: '0.8rem', color: '#94a3b8', marginBottom: 15, borderBottom: '1px solid #334155', paddingBottom: 10 }}>
          Due diligence memo | AlphaForge framework | {timestamp || 'July 31, 2026'}
        </div>

        <h3 style={{ fontSize: '1.4rem', fontWeight: 800, color: '#f8fafc', marginBottom: 15 }}>Final Investor Readout</h3>
        <div style={{ background: '#111827', border: '1px solid #334155', padding: 24, marginBottom: 20 }}>
          <p style={{ fontSize: '0.92rem', lineHeight: 1.7, color: '#f8fafc', margin: 0 }}>
            {verdict === 'PROCEED' ? 'The asset represents a credible and biologically supported clinical candidate. Risk scores reflect favorable intrinsic molecule-indication fit, supported by strong target biology and manageable safety.' : verdict === 'CAUTION' ? 'The asset presents moderate translational and developability risks that must be carefully managed through clinical trial design and dose optimization.' : 'The asset carries high clinical attrition probability and severe safety or pharmacokinetic liabilities. Progression is not recommended without substantial re-engineering.'}
          </p>
        </div>

        <div style={{ fontWeight: 700, color: '#60a5fa', fontSize: '0.95rem', marginBottom: 20 }}>
          Investment conclusion: {verdict} &mdash; evaluated clinical candidate with structured risk profile.
        </div>

        <div style={{ textAlign: 'right', fontSize: '0.75rem', color: '#64748b', borderTop: '1px solid #334155', paddingTop: 10 }}>
          ReneuBio Inc - Confidential &bull; 7
        </div>
      </div>
    </div>
  )
}
