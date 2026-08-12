import React, { useState } from 'react'

function probColor(p) {
  if (p >= 0.65) return 'var(--accent-green)'
  if (p >= 0.40) return 'var(--accent-yellow)'
  if (p >= 0.20) return 'var(--accent-orange)'
  return 'var(--accent-red)'
}

export default function AgentCard({
  name, icon, iconBg, data, probKeys, probRationaleKeys,
  sections = [], details = [], isMedchem = false, isPrinting = false,
}) {
  const [open, setOpen] = useState(false)

  const verdict = data.verdict || ''
  const probLabels = ['P1', 'P2', 'P3']
  const isBodyOpen = open || isPrinting

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
                : 'Phase Assessment'}
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          {verdict && (
            <span className={`verdict-badge verdict-${verdict}`}>{verdict}</span>
          )}
          <span className={`chevron ${isBodyOpen ? 'open' : ''}`}>&#9660;</span>
        </div>
      </div>

      {isBodyOpen && (
        <div className="agent-body">
          <div className="agent-probs">
            {probRationaleKeys.map((key, i) => {
              if (!key || !data[key]) return null
              return (
                <div className="agent-prob-item" key={key}>
                  <div className="prob-label">{probLabels[i]}</div>
                  <div className="agent-prob-rationale">
                    {data[key]}
                  </div>
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

          {Array.isArray(data.tox_panel) && data.tox_panel.length > 0 && (
            <div className="agent-section">
              <div className="agent-section-title">
                Toxicity Panel{' '}
                <span style={{ color: 'var(--text-muted)', fontWeight: 400 }}>
                  ({data.tox_panel.filter((t) => t.verdict === 'FAIL').length} FAIL /{' '}
                  {data.tox_panel.length})
                </span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginTop: 6 }}>
                {data.tox_panel.map((t) => {
                  const color =
                    t.verdict === 'FAIL'
                      ? 'var(--accent-red)'
                      : t.verdict === 'PASS'
                      ? 'var(--accent-green)'
                      : 'var(--accent-yellow)'
                  return (
                    <div
                      key={t.category}
                      style={{
                        display: 'flex',
                        alignItems: 'flex-start',
                        gap: 10,
                        padding: '6px 8px',
                        border: '1px solid var(--border)',
                        background: 'var(--bg-secondary)',
                      }}
                    >
                      <span
                        style={{
                          flexShrink: 0,
                          minWidth: 62,
                          textAlign: 'center',
                          fontSize: '0.7rem',
                          fontWeight: 700,
                          letterSpacing: '0.04em',
                          padding: '2px 6px',
                          color: '#fff',
                          background: color,
                        }}
                      >
                        {t.verdict}
                      </span>
                      <div style={{ minWidth: 0 }}>
                        <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text)' }}>
                          {t.label}
                        </div>
                        <div style={{ fontSize: '0.73rem', color: 'var(--text-muted)', marginTop: 2 }}>
                          {t.rationale || t.description}
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
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
