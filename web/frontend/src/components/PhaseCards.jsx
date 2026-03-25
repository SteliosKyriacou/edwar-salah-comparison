import React from 'react'

export default function PhaseCards({ overview }) {
  const phases = [
    { name: 'Phase 1 Rationale', rationale: overview.final_p1_rationale },
    { name: 'Phase 2 Rationale', rationale: overview.final_p2_rationale },
    { name: 'Phase 3 Rationale', rationale: overview.final_p3_rationale },
  ]

  return (
    <div className="phase-row">
      {phases.map((ph) => (
        <div className="phase-card" key={ph.name}>
          <div className="phase-header">
            <span className="phase-name">{ph.name}</span>
          </div>
          <div className="phase-rationale">{ph.rationale}</div>
        </div>
      ))}
    </div>
  )
}
