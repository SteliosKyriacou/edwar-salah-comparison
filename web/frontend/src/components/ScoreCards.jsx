import React, { useState } from 'react'

function scoreColor(score) {
  if (score <= 20) return 'var(--accent-green)'
  if (score <= 40) return 'var(--accent-cyan)'
  if (score <= 60) return 'var(--accent-yellow)'
  if (score <= 80) return 'var(--accent-orange)'
  return 'var(--accent-red)'
}

function scoreLabel(score) {
  if (score <= 15) return 'Excellent'
  if (score <= 30) return 'Good'
  if (score <= 50) return 'Moderate'
  if (score <= 70) return 'Concerning'
  if (score <= 85) return 'Poor'
  return 'Critical'
}

export default function ScoreCards({ overview }) {
  const [rationaleOpen, setRationaleOpen] = useState(false)
  const score = overview.medchem_score
  const color = scoreColor(score)

  return (
    <div className="score-row">
      <div className="score-card" style={{ borderColor: color }}>
        <div className="label">CDR Score</div>
        <div className="value" style={{ color }}>{score}</div>
        <div className="sub">{scoreLabel(score)} — lower is better</div>
      </div>

      <div className="score-card">
        <div className="label">Consensus</div>
        <div className="value" style={{
          color: score <= 30 ? 'var(--accent-green)' :
                 score <= 60 ? 'var(--accent-yellow)' : 'var(--accent-red)',
          fontSize: '1.4rem',
        }}>
          {score <= 30 ? 'PROCEED' : score <= 60 ? 'OPTIMIZE' : 'RECONSIDER'}
        </div>
        <div className="sub">
          {score <= 30
            ? 'Strong clinical candidate'
            : score <= 60
            ? 'Addressable liabilities identified'
            : 'Significant structural concerns'}
        </div>
      </div>

      <div className="score-card rationale-card" onClick={() => setRationaleOpen(!rationaleOpen)} style={{ cursor: 'pointer' }}>
        <div className="label">Consensus Rationale <span style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>(click to {rationaleOpen ? 'collapse' : 'expand'})</span></div>
        <div className={`rationale-text ${rationaleOpen ? 'expanded' : ''}`}>{overview.rationale}</div>
      </div>
    </div>
  )
}
