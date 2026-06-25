import React from 'react'

function hostname(uri) {
  try {
    return new URL(uri).hostname.replace(/^www\./, '')
  } catch {
    return uri
  }
}

export default function WebSearchSummary({ webSearch }) {
  if (!webSearch) return null

  const { summary, references = [], validated, error } = webSearch

  // Search ran but produced nothing usable.
  if (!summary) {
    return (
      <div
        style={{
          margin: '24px 0',
          padding: '16px 20px',
          borderRadius: 10,
          border: '1px solid var(--border)',
          background: 'var(--bg-secondary)',
          fontSize: '0.85rem',
          color: 'var(--text-muted)',
        }}
      >
        🌐 Web search was enabled but no usable literature summary was produced
        {error ? ` (${error})` : ''}.
      </div>
    )
  }

  return (
    <div style={{ margin: '24px 0' }}>
      <div className="section-title">
        🌐 Web Search Evidence
        <span
          style={{
            marginLeft: 10,
            fontSize: '0.7rem',
            fontWeight: 600,
            padding: '2px 8px',
            borderRadius: 10,
            verticalAlign: 'middle',
            color: validated ? 'var(--accent-green, #2ecc71)' : 'var(--text-muted)',
            background: 'rgba(46, 204, 113, 0.12)',
          }}
        >
          {validated ? '✓ Validated' : 'Unvalidated'}
        </span>
      </div>

      <div
        style={{
          padding: '18px 22px',
          borderRadius: 10,
          border: '1px solid var(--border)',
          background: 'var(--bg-secondary)',
        }}
      >
        <p
          style={{
            fontSize: '0.9rem',
            lineHeight: 1.6,
            color: 'var(--text)',
            whiteSpace: 'pre-wrap',
            margin: 0,
          }}
        >
          {summary}
        </p>

        {references.length > 0 && (
          <div style={{ marginTop: 18 }}>
            <div
              style={{
                fontSize: '0.78rem',
                fontWeight: 700,
                color: 'var(--text-muted)',
                textTransform: 'uppercase',
                letterSpacing: '0.04em',
                marginBottom: 8,
              }}
            >
              References ({references.length})
            </div>
            <ol style={{ margin: 0, paddingLeft: 20 }}>
              {references.map((ref, i) => (
                <li key={i} style={{ marginBottom: 6, fontSize: '0.83rem', lineHeight: 1.4 }}>
                  <a
                    href={ref.uri}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{ color: 'var(--accent-blue)', textDecoration: 'none' }}
                  >
                    {ref.title || hostname(ref.uri)}
                  </a>
                  <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>
                    {' '}
                    — {hostname(ref.uri)}
                  </span>
                </li>
              ))}
            </ol>
          </div>
        )}

        <div
          style={{
            marginTop: 16,
            fontSize: '0.72rem',
            color: 'var(--text-muted)',
            fontStyle: 'italic',
          }}
        >
          This summary was generated from web search and fed to the assessment agents as
          additional context. Independently verify all sources before relying on them.
        </div>
      </div>
    </div>
  )
}
