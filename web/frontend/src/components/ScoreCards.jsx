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

function calProbColor(p) {
  if (p >= 0.65) return 'var(--accent-green)'
  if (p >= 0.40) return 'var(--accent-cyan)'
  if (p >= 0.20) return 'var(--accent-yellow)'
  if (p >= 0.10) return 'var(--accent-orange)'
  return 'var(--accent-red)'
}

export default function ScoreCards({ overview }) {
  const score = overview.medchem_score
  const calProb = overview.tcsp_calibrated
  const color = scoreColor(score)
  const calColor = calProbColor(calProb)

  return (
    <div className="score-row">
      <div className="score-card" style={{ borderColor: calColor }}>
        <div className="label">Approval Probability</div>
        <div className="value" style={{ color: calColor }}>
          {overview.tcsp_calibrated_pct}%
        </div>
        <div className="sub">Calibrated estimate of clinical success</div>
      </div>

      <div className="score-card" style={{ borderColor: color }}>
        <div className="label">MedChem Score</div>
        <div className="value" style={{ color }}>{score}</div>
        <div className="sub">{scoreLabel(score)} — lower is better</div>
      </div>

      <div className="score-card">
        <div className="label">Raw TCSP</div>
        <div className="value" style={{ color: 'var(--text-secondary)', fontSize: '1.8rem' }}>
          {overview.tcsp_raw_pct}%
        </div>
        <div className="sub">P1 x P2 x P3 (before calibration)</div>
      </div>
    </div>
  )
}
