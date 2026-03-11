import React from 'react'

export default function MoleculeViewer({ molecule }) {
  if (!molecule?.image) return null

  return (
    <div className="molecule-section">
      <h3>Molecule Structure</h3>
      <img
        className="molecule-img"
        src={`data:image/png;base64,${molecule.image}`}
        alt="Molecule structure"
      />
      {molecule.fragments?.length > 0 && (
        <>
          <div style={{ marginTop: 14, fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600 }}>
            STRUCTURAL ALERTS DETECTED
          </div>
          <div className="fragment-list">
            {molecule.fragments.map((f) => (
              <span
                key={f.name}
                className="fragment-tag"
                style={{
                  color: f.color,
                  borderColor: f.color,
                  background: `${f.color}15`,
                }}
              >
                {f.name} ({f.count}x)
              </span>
            ))}
          </div>
        </>
      )}
      {molecule.fragments?.length === 0 && (
        <div style={{ marginTop: 10, fontSize: '0.78rem', color: 'var(--accent-green)' }}>
          No common structural alerts detected
        </div>
      )}
    </div>
  )
}
