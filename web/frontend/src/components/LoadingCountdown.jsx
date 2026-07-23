import React, { useState, useEffect } from 'react'

const ESTIMATE_SECONDS = 79
const STAGES = [
  { at: 0, label: 'Initializing agents...' },
  { at: 5, label: 'Pass 1: 4 agents evaluating in parallel...' },
  { at: 15, label: 'Biological-Rationalist analyzing target biology...' },
  { at: 25, label: 'Toxi-Toxicologist assessing safety liabilities...' },
  { at: 35, label: 'Pharma-Pharmacologist evaluating PK/PD...' },
  { at: 45, label: 'MedChem-Rationalist structural critique...' },
  { at: 55, label: 'Pass 2: Integrating all advisory data...' },
  { at: 65, label: 'Computing consensus probabilities...' },
  { at: 74, label: 'Almost there...' },
]

export default function LoadingCountdown({ isQueued }) {
  const [elapsed, setElapsed] = useState(0)

  useEffect(() => {
    if (isQueued) return

    const interval = setInterval(() => {
      setElapsed((prev) => prev + 1)
    }, 1000)
    return () => clearInterval(interval)
  }, [isQueued])

  if (isQueued) {
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
              stroke="var(--accent-orange)"
              strokeWidth="5"
              strokeLinecap="round"
              strokeDasharray={`${2 * Math.PI * 42}`}
              strokeDashoffset={`${2 * Math.PI * 42 * 0.75}`}
              transform="rotate(-90 50 50)"
              style={{ 
                transformOrigin: '50% 50%',
                animation: 'spin 1.5s linear infinite' 
              }}
            />
          </svg>
          <div className="countdown-number" style={{ color: 'var(--accent-orange)' }}>
            Q
          </div>
        </div>

        <div className="loading-text" style={{ color: 'var(--accent-orange)' }}>👥 Request Queued...</div>
        <div className="loading-subtext">Waiting for an available evaluation slot (limit is 100 concurrent)</div>

        <div className="loading-progress-bar" style={{ background: 'rgba(255, 140, 0, 0.1)' }}>
          <div
            className="loading-progress-fill"
            style={{ width: '100%', background: 'var(--accent-orange)', animation: 'pulse 1.5s infinite' }}
          />
        </div>

        <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: 20 }}>
          The timer and multi-agent pipeline will automatically start as soon as your slot opens.
        </div>
      </div>
    )
  }

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
          const agentDone = elapsed > 15 + i * 10
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
