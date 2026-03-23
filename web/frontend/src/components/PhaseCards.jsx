import React from 'react'

function probColor(p) {
  if (p >= 0.65) return 'var(--accent-green)'
  if (p >= 0.40) return 'var(--accent-yellow)'
  if (p >= 0.20) return 'var(--accent-orange)'
  return 'var(--accent-red)'
}

export default function PhaseCards({ overview }) {
  const phases = [
    { name: 'Probability of Success at Phase 1', prob: overview.final_p1, rationale: overview.final_p1_rationale },
    { name: 'Probability of Success at Phase 2', prob: overview.final_p2, rationale: overview.final_p2_rationale },
    { name: 'Probability of Success at Phase 3', prob: overview.final_p3, rationale: overview.final_p3_rationale },
  ]

  return (
    <div className="phase-row">
      {phases.map((ph) => {
        const pct = Math.round(ph.prob * 100)
        const color = probColor(ph.prob)
        return (
          <div className="phase-card" key={ph.name}>
            <div className="phase-header">
              <span className="phase-name">{ph.name}</span>
              <span className="phase-prob" style={{ color }}>{pct}%</span>
            </div>
            <div className="prob-bar">
              <div
                className="prob-bar-fill"
                style={{ width: `${pct}%`, background: color }}
              />
            </div>
            <div className="phase-rationale">{ph.rationale}</div>
          </div>
        )
      })}
    </div>
  )
}
