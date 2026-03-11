import React, { useState, useEffect } from 'react'

const ESTIMATE_SECONDS = 45
const STAGES = [
  { at: 0, label: 'Initializing agents...' },
  { at: 3, label: 'Pass 1: 4 agents evaluating in parallel...' },
  { at: 10, label: 'Biological-Rationalist analyzing target biology...' },
  { at: 16, label: 'Toxi-Toxicologist assessing safety liabilities...' },
  { at: 22, label: 'Pharma-Pharmacologist evaluating PK/PD...' },
  { at: 28, label: 'MedChem-Rationalist structural critique...' },
  { at: 34, label: 'Pass 2: Integrating all advisory data...' },
  { at: 40, label: 'Computing consensus probabilities...' },
  { at: 45, label: 'Almost there...' },
]

export default function LoadingCountdown() {
  const [elapsed, setElapsed] = useState(0)

  useEffect(() => {
    const interval = setInterval(() => {
      setElapsed((prev) => prev + 1)
    }, 1000)
    return () => clearInterval(interval)
  }, [])

  const remaining = Math.max(0, ESTIMATE_SECONDS - elapsed)
  const progress = Math.min(100, (elapsed / ESTIMATE_SECONDS) * 100)

  // Find current stage
  let currentStage = STAGES[0].label
  for (const stage of STAGES) {
    if (elapsed >= stage.at) currentStage = stage.label
  }

  const mins = Math.floor(remaining / 60)
  const secs = remaining % 60
  const timeStr = remaining > 0
    ? `~${mins > 0 ? `${mins}m ` : ''}${secs}s remaining`
    : 'Finishing up...'

  return (
    <div className="loading-overlay">
      <div className="countdown-ring">
        <svg width="100" height="100" viewBox="0 0 100 100">
          <circle
            cx="50" cy="50" r="42"
            fill="none"
            stroke="var(--border)"
            strokeWidth="5"
          />
          <circle
            cx="50" cy="50" r="42"
            fill="none"
            stroke="var(--accent-blue)"
            strokeWidth="5"
            strokeLinecap="round"
            strokeDasharray={`${2 * Math.PI * 42}`}
            strokeDashoffset={`${2 * Math.PI * 42 * (1 - progress / 100)}`}
            transform="rotate(-90 50 50)"
            style={{ transition: 'stroke-dashoffset 1s linear' }}
          />
        </svg>
        <div className="countdown-number">
          {remaining > 0 ? remaining : '...'}
        </div>
      </div>

      <div className="loading-text">{currentStage}</div>
      <div className="loading-subtext">{timeStr}</div>

      <div className="loading-progress-bar">
        <div
          className="loading-progress-fill"
          style={{ width: `${progress}%` }}
        />
      </div>

      <div className="loading-agents-row">
        {['Biology', 'Toxicology', 'Pharmacology', 'MedChem'].map((name, i) => {
          const agentDone = elapsed > 8 + i * 6
          return (
            <div key={name} className={`loading-agent-chip ${agentDone ? 'done' : ''}`}>
              <span className="loading-agent-dot" />
              {name}
            </div>
          )
        })}
      </div>
    </div>
  )
}
