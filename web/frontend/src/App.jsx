import React, { useState, useRef, useEffect } from 'react'
import Header from './components/Header'
import InputForm from './components/InputForm'
import ScoreCards from './components/ScoreCards'
import PhaseCards from './components/PhaseCards'
import AgentCard from './components/AgentCard'
import StructuralFlags from './components/StructuralFlags'
import LoadingCountdown from './components/LoadingCountdown'

export default function App() {
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const resultsRef = useRef(null)

  async function handleSubmit(formData) {
    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const res = await fetch('/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      })

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }))
        throw new Error(err.detail || 'Analysis failed')
      }

      const data = await res.json()
      setResult(data)

      setTimeout(() => {
        resultsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
      }, 100)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <Header />
      <div className="container">
        <InputForm onSubmit={handleSubmit} loading={loading} />

        {loading && <LoadingCountdown />}

        {error && <div className="error-msg">{error}</div>}

        {result && (
          <div ref={resultsRef}>
            <ScoreCards overview={result.overview} />
            <PhaseCards overview={result.overview} />

            <StructuralFlags overview={result.overview} />

            <div className="section-title">Agent Assessments</div>
            <div className="agents-grid">
              <AgentCard
                name="Biological-Rationalist"
                icon="🧬"
                iconBg="rgba(46, 204, 113, 0.15)"
                data={result.biology}
                probKeys={['bio_p1', 'bio_p2', 'bio_p3']}
                probRationaleKeys={['bio_p1_rationale', 'bio_p2_rationale', 'bio_p3_rationale']}
                sections={[
                  { title: 'Rationale', key: 'rationale' },
                  { title: 'Mechanism Validation', key: 'mechanism_validation' },
                  { title: 'Druggability Assessment', key: 'druggability' },
                ]}
              />
              <AgentCard
                name="Toxi-Predictive-Toxicologist"
                icon="☠️"
                iconBg="rgba(231, 76, 60, 0.15)"
                data={result.toxicology}
                probKeys={['tox_p1', 'tox_p2', 'tox_p3']}
                probRationaleKeys={['tox_p1_rationale', 'tox_p2_rationale', 'tox_p3_rationale']}
                sections={[
                  { title: 'Rationale', key: 'rationale' },
                ]}
                details={[
                  { label: 'Therapeutic Window', key: 'therapeutic_window' },
                  { label: 'Primary Concern', key: 'primary_concern' },
                  { label: 'On-Target Risk', key: 'on_target_risk' },
                  { label: 'Off-Target Risk', key: 'off_target_risk' },
                ]}
              />
              <AgentCard
                name="Pharma-Clinical-Pharmacologist"
                icon="💊"
                iconBg="rgba(74, 158, 255, 0.15)"
                data={result.pharmacology}
                probKeys={['pk_p1', 'pk_p2', 'pk_p3']}
                probRationaleKeys={['pk_p1_rationale', 'pk_p2_rationale', 'pk_p3_rationale']}
                sections={[
                  { title: 'Rationale', key: 'rationale' },
                ]}
                details={[
                  { label: 'Predicted Dose', key: 'predicted_dose' },
                  { label: 'Oral Feasibility', key: 'oral_feasibility' },
                  { label: 'DDI Risk', key: 'ddi_risk' },
                  { label: 'Half-Life', key: 'half_life' },
                ]}
              />
              <AgentCard
                name="MedChem-Rationalist"
                icon="🧪"
                iconBg="rgba(155, 89, 182, 0.15)"
                data={result.medchem}
                probKeys={['chem_p1', 'chem_p2', 'chem_p3']}
                probRationaleKeys={[]}
                sections={[]}
                isMedchem
              />
            </div>
          </div>
        )}
      </div>
    </>
  )
}
