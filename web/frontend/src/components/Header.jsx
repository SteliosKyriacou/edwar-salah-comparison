import React from 'react'

export default function Header() {
  return (
    <div className="header">
      <h1>Will Your Drug Succeed in the Clinic?</h1>
      <div className="subtitle">
        Multi-agent AI pipeline: 4 specialist agents critique your molecule in parallel
      </div>
      <div className="privacy-banner">
        No molecules stored — predictions are logged without SMILES or targets
      </div>
    </div>
  )
}
