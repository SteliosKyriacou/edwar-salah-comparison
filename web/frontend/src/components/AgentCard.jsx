import React, { useState } from 'react'

function probColor(p) {
  if (p >= 0.65) return 'var(--accent-green)'
  if (p >= 0.40) return 'var(--accent-yellow)'
  if (p >= 0.20) return 'var(--accent-orange)'
  return 'var(--accent-red)'
}

export default function AgentCard({
  name, icon, iconBg, data, probKeys, probRationaleKeys,
  sections = [], details = [], isMedchem = false,
}) {
  const [open, setOpen] = useState(false)

  const verdict = data.verdict || ''
  const probLabels = ['P1', 'P2', 'P3']

  return (
    <div className="agent-card">
      <div className="agent-header" onClick={() => setOpen(!open)}>
        <div className="agent-info">
          <div className="agent-icon" style={{ background: iconBg }}>
            {icon}
          </div>
          <div>
            <div className="agent-name">{name}</div>
            <div className="agent-sub">
              {isMedchem
                ? 'Structural Assessment (Pass 1)'
                : `${probKeys[0]?.split('_')[0]?.toUpperCase()} P1-P3`}
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          {verdict && (
            <span className={`verdict-badge verdict-${verdict}`}>{verdict}</span>
          )}
          <span className={`chevron ${open ? 'open' : ''}`}>&#9660;</span>
        </div>
      </div>

      {open && (
        <div className="agent-body">
          <div className="agent-probs">
            {probKeys.map((key, i) => {
              const val = data[key]
              if (val == null) return null
              const pct = Math.round(val * 100)
              return (
                <div className="agent-prob-item" key={key}>
                  <div className="prob-label">{probLabels[i]}</div>
                  <div className="prob-value" style={{ color: probColor(val) }}>
                    {pct}%
                  </div>
                  <div className="prob-bar" style={{ margin: '6px 0' }}>
                    <div
                      className="prob-bar-fill"
                      style={{ width: `${pct}%`, background: probColor(val) }}
                    />
                  </div>
                  {probRationaleKeys[i] && data[probRationaleKeys[i]] && (
                    <div className="agent-prob-rationale">
                      {data[probRationaleKeys[i]]}
                    </div>
                  )}
                </div>
              )
            })}
          </div>

          {sections.map((sec) => {
            const text = data[sec.key]
            if (!text) return null
            return (
              <div className="agent-section" key={sec.key}>
                <div className="agent-section-title">{sec.title}</div>
                <div className="agent-section-text">{text}</div>
              </div>
            )
          })}

          {details.length > 0 && (
            <div className="agent-detail-row">
              {details.map((d) => {
                const val = data[d.key]
                if (!val) return null
                return (
                  <div className="detail-item" key={d.key}>
                    <div className="detail-label">{d.label}</div>
                    <div className="detail-value">{val}</div>
                  </div>
                )
              })}
            </div>
          )}

          {isMedchem && data.pass1 && (
            <div className="agent-section">
              <div className="agent-section-title">Structural Assessment</div>
              <div className="agent-section-text">
                {data.pass1.structural_assessment || JSON.stringify(data.pass1, null, 2)}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
