import React from 'react'

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

function tcspLabel(tcsp) {
  if (tcsp >= 0.25) return 'High'
  if (tcsp >= 0.10) return 'Moderate'
  if (tcsp >= 0.04) return 'Low'
  return 'Very Low'
}

export default function ScoreCards({ overview }) {
  const score = overview.medchem_score
  const tcsp = overview.tcsp
  const color = scoreColor(score)

  return (
    <div className="score-row">
      <div className="score-card" style={{ borderColor: color }}>
        <div className="label">MedChem Score</div>
        <div className="value" style={{ color }}>{score}</div>
        <div className="sub">{scoreLabel(score)} — lower is better</div>
      </div>

      <div className="score-card">
        <div className="label">TCSP</div>
        <div className="value" style={{ color: 'var(--accent-orange)' }}>
          {overview.tcsp_pct}%
        </div>
        <div className="sub">{tcspLabel(tcsp)} probability — P1 x P2 x P3</div>
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
    </div>
  )
}
