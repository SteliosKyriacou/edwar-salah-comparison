import React from 'react'

// Color scheme per overall sentiment.
const THEMES = {
  positive: { border: '#2ecc71', bg: 'rgba(46, 204, 113, 0.10)', text: '#2ecc71', icon: '✓' },
  negative: { border: '#e74c3c', bg: 'rgba(231, 76, 60, 0.10)', text: '#e74c3c', icon: '✕' },
  mixed: { border: '#f1c40f', bg: 'rgba(241, 196, 15, 0.10)', text: '#f1c40f', icon: '~' },
  none: { border: 'var(--border)', bg: 'var(--bg-secondary)', text: 'var(--text-muted)', icon: 'ℹ' },
}

const EVENT_COLORS = {
  positive: '#2ecc71',
  negative: '#e74c3c',
  neutral: 'var(--text-muted)',
}

export default function FdaResponse({ fda }) {
  if (!fda) return null

  const overall = THEMES[fda.overall] || THEMES.none
  const events = fda.events || []
  const refs = fda.references || []

  return (
    <div style={{ margin: '24px 0' }}>
      <div className="section-title">🏛️ Current FDA Response</div>

      <div
        style={{
          padding: '18px 22px',
          borderRadius: 0,
          border: `1px solid ${overall.border}`,
          background: overall.bg,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
          <span
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: 24,
              height: 24,
              borderRadius: '50%',
              background: overall.text,
              color: '#0a0e17',
              fontWeight: 700,
              fontSize: '0.8rem',
              flexShrink: 0,
            }}
          >
            {overall.icon}
          </span>
          <span style={{ fontSize: '0.95rem', fontWeight: 700, color: overall.text }}>
            {fda.drug_name && fda.drug_name !== 'Unknown' ? fda.drug_name : 'Regulatory status'}
            {' · '}
            {fda.overall.charAt(0).toUpperCase() + fda.overall.slice(1)}
          </span>
        </div>

        {fda.headline && (
          <p style={{ margin: '12px 0 0', fontSize: '0.9rem', lineHeight: 1.55, color: 'var(--text)' }}>
            {fda.headline}
          </p>
        )}

        {events.length > 0 && (
          <div style={{ marginTop: 16, display: 'flex', flexDirection: 'column', gap: 8 }}>
            {events.map((ev, i) => (
              <div
                key={i}
                style={{
                  display: 'flex',
                  gap: 10,
                  padding: '10px 12px',
                  borderRadius: 0,
                  background: 'rgba(0,0,0,0.18)',
                  borderLeft: `3px solid ${EVENT_COLORS[ev.sentiment] || EVENT_COLORS.neutral}`,
                }}
              >
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: '0.84rem', fontWeight: 600, color: 'var(--text)' }}>
                    {ev.title}
                    {ev.date && (
                      <span style={{ color: 'var(--text-muted)', fontWeight: 400 }}> · {ev.date}</span>
                    )}
                  </div>
                  {ev.detail && (
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: 3, lineHeight: 1.45 }}>
                      {ev.detail}
                    </div>
                  )}
                </div>
                <span
                  style={{
                    flexShrink: 0,
                    alignSelf: 'flex-start',
                    fontSize: '0.68rem',
                    fontWeight: 700,
                    textTransform: 'uppercase',
                    color: EVENT_COLORS[ev.sentiment] || EVENT_COLORS.neutral,
                  }}
                >
                  {ev.sentiment}
                </span>
              </div>
            ))}
          </div>
        )}

        {refs.length > 0 && (
          <div style={{ marginTop: 14, fontSize: '0.78rem', color: 'var(--text-muted)' }}>
            Sources:{' '}
            {refs.map((r, i) => (
              <React.Fragment key={i}>
                {i > 0 && ', '}
                <a
                  href={r.uri}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{ color: 'var(--accent-blue)', textDecoration: 'none' }}
                >
                  {r.title || 'source'}
                </a>
              </React.Fragment>
            ))}
          </div>
        )}

        <div style={{ marginTop: 14, fontSize: '0.72rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>
          FDA status is retrieved via web search for context only and does not affect the score.
          Verify against official FDA sources before relying on it.
        </div>
      </div>
    </div>
  )
}
