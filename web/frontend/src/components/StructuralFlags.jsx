import React from 'react'

export default function StructuralFlags({ overview }) {
  return (
    <div className="flags-row">
      <div className="flag-card">
        <div className="flag-label">Metabolic Stability</div>
        <div className="flag-value">
          {overview.metabolic_stability || 'Not assessed'}
        </div>
      </div>
      <div className="flag-card">
        <div className="flag-label">Toxic Fragments</div>
        <div className="flag-value">
          {overview.toxic_fragments || 'None identified'}
        </div>
      </div>
    </div>
  )
}
