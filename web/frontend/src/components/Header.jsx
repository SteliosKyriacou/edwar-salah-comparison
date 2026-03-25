import React from 'react'

export default function Header() {
  return (
    <div className="header">
      <h1>Will Your Drug Succeed in the Clinic?</h1>
      <div className="subtitle">
        ReneuBio's platform computes a Developability Risk Score — a quantitative estimate of clinical attrition risk. It starts with chemical structure, adds biological context from target and indication, and outputs a score from 1 (lowest risk) to 100 (highest risk).
      </div>
      <div className="subtitle-secondary">
        The score integrates analysis across key developability domains, including biology, toxicology, pharmacology, and medicinal chemistry.
      </div>
      <div className="privacy-banner">
        No molecules stored — predictions are logged without SMILES or targets
      </div>
    </div>
  )
}
