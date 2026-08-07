import React, { useState } from 'react'

/*
 * Deep-analysis report: distributions over N repeated simulations.
 *
 * Charts are hand-rolled inline SVG — the frontend has no charting dependency
 * and this keeps it that way. Colour decisions (validated against the app's own
 * dark surface #1a1a2e):
 *   - A histogram is ONE series, so bars are a single flat hue. Encoding
 *     magnitude by bar length AND a colour ramp would be redundant.
 *   - The agent-max reference marker is the second element, so it takes the
 *     brand orange: CVD separation from the blue is ΔE 28.4, well clear.
 *   - Risk severity buckets are ordered status, not categories, so they use the
 *     reserved status palette and ALWAYS carry a text label + percentage, so
 *     colour never carries the meaning alone.
 * Print overrides live in App.css (@media print) where the surface is white.
 */

const BAR = 'var(--chart-bar, #4a9eff)'
const REF = 'var(--chart-ref, #ff8c00)'
const AXIS = 'var(--text-muted)'
const GRID = 'var(--border)'

const BUCKET_COLOR = {
  low: 'var(--chart-good, #0ca30c)',
  mid_low: 'var(--chart-warning, #fab219)',
  mid_high: 'var(--chart-serious, #ec835a)',
  high: 'var(--chart-critical, #d03b3b)',
}

// Icon pairs the colour so severity never rests on hue alone.
const BUCKET_ICON = {
  low: '●',
  mid_low: '◆',
  mid_high: '▲',
  high: '✖',
}

function fmtPct(v, digits = 1) {
  if (v === null || v === undefined) return '—'
  return `${(v * 100).toFixed(digits)}%`
}

function Card({ title, subtitle, children, actions }) {
  return (
    <div
      style={{
        background: 'var(--bg-card)',
        border: '1px solid var(--border)',
        padding: '18px 20px',
        marginBottom: 20,
      }}
      className="deep-card"
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 12 }}>
        <div>
          <h3 style={{ margin: 0, fontSize: '0.98rem', color: 'var(--text-primary)' }}>{title}</h3>
          {subtitle && (
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: 4, lineHeight: 1.45 }}>
              {subtitle}
            </div>
          )}
        </div>
        {actions}
      </div>
      <div style={{ marginTop: 14 }}>{children}</div>
    </div>
  )
}

/* ---------------------------------------------------------------- stat tiles */

function StatTiles({ stats, format = (v) => v }) {
  const items = [
    ['Mean', stats.mean],
    ['Median', stats.median],
    ['Std Dev', stats.sd],
    ['Min', stats.min],
    ['Max', stats.max],
    ['P25', stats.p25],
    ['P75', stats.p75],
    ['IQR', stats.iqr],
  ]
  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10 }}>
      {items.map(([label, value]) => (
        <div
          key={label}
          style={{
            border: '1px solid var(--border)',
            padding: '8px 14px',
            minWidth: 84,
            background: 'var(--bg-secondary)',
          }}
        >
          <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
            {label}
          </div>
          <div style={{ fontSize: '1.05rem', color: 'var(--text-primary)', fontWeight: 700, marginTop: 2 }}>
            {value === null || value === undefined ? '—' : format(value)}
          </div>
        </div>
      ))}
    </div>
  )
}

/* ----------------------------------------------------------------- histogram */

/**
 * Single-series histogram. `refLines` draws labelled reference marks (e.g. the
 * mean agent-max) on the same x scale.
 */
function Histogram({ bins, xLabel, xFormat, refLines = [], height = 190 }) {
  const [hover, setHover] = useState(null)
  if (!bins || !bins.length) return null

  const W = 720
  const H = height
  const M = { top: 14, right: 16, bottom: 42, left: 46 }
  const iw = W - M.left - M.right
  const ih = H - M.top - M.bottom

  const lo = bins[0].lo
  const hi = bins[bins.length - 1].hi
  const maxCount = Math.max(...bins.map((b) => b.count), 1)

  const x = (v) => M.left + ((v - lo) / (hi - lo)) * iw
  const y = (c) => M.top + ih - (c / maxCount) * ih

  // 2px surface gap between adjacent bars
  const slot = iw / bins.length
  const barW = Math.max(1, slot - 2)

  const yTicks = 4
  const tickVals = Array.from({ length: yTicks + 1 }, (_, i) => Math.round((maxCount / yTicks) * i))

  return (
    <div>
      <svg
        viewBox={`0 0 ${W} ${H}`}
        style={{ width: '100%', height: 'auto', display: 'block', overflow: 'visible' }}
        role="img"
        aria-label={`Histogram of ${xLabel}`}
      >
        {/* recessive gridlines */}
        {tickVals.map((t) => (
          <g key={t}>
            <line x1={M.left} x2={M.left + iw} y1={y(t)} y2={y(t)} stroke={GRID} strokeWidth="1" />
            <text x={M.left - 8} y={y(t) + 4} textAnchor="end" fontSize="10" fill={AXIS}>
              {t}
            </text>
          </g>
        ))}

        {/* bars — rounded data-end anchored to the baseline */}
        {bins.map((b, i) => {
          const bx = M.left + i * slot + 1
          const bh = Math.max(b.count > 0 ? 2 : 0, M.top + ih - y(b.count))
          const active = hover === i
          return (
            <g key={i}>
              <rect
                x={bx}
                y={M.top + ih - bh}
                width={barW}
                height={bh}
                rx={bh > 4 ? 3 : 0}
                fill={BAR}
                opacity={hover === null || active ? 1 : 0.55}
              />
              {/* hit target wider than the mark */}
              <rect
                x={bx - 1}
                y={M.top}
                width={slot}
                height={ih}
                fill="transparent"
                onMouseEnter={() => setHover(i)}
                onMouseLeave={() => setHover(null)}
              />
            </g>
          )
        })}

        {/* baseline */}
        <line x1={M.left} x2={M.left + iw} y1={M.top + ih} y2={M.top + ih} stroke={AXIS} strokeWidth="1" />

        {/* x ticks: first, middle, last edges */}
        {[0, Math.floor(bins.length / 2), bins.length - 1].map((i) => (
          <text
            key={i}
            x={M.left + i * slot + slot / 2}
            y={M.top + ih + 16}
            textAnchor="middle"
            fontSize="10"
            fill={AXIS}
          >
            {xFormat(bins[i].lo)}
          </text>
        ))}
        <text x={M.left + iw / 2} y={H - 6} textAnchor="middle" fontSize="10.5" fill={AXIS}>
          {xLabel}
        </text>
        <text
          x={12}
          y={M.top + ih / 2}
          textAnchor="middle"
          fontSize="10.5"
          fill={AXIS}
          transform={`rotate(-90 12 ${M.top + ih / 2})`}
        >
          simulations
        </text>

        {/* reference markers */}
        {refLines.map((r, i) => {
          const rx = x(r.value)
          if (!isFinite(rx)) return null
          return (
            <g key={i}>
              <line
                x1={rx}
                x2={rx}
                y1={M.top}
                y2={M.top + ih}
                stroke={REF}
                strokeWidth="2"
                strokeDasharray="5 3"
              />
              <text x={rx} y={M.top - 3} textAnchor="middle" fontSize="10" fill={REF} fontWeight="700">
                {r.label}
              </text>
            </g>
          )
        })}

        {/* tooltip */}
        {hover !== null && (
          <g pointerEvents="none">
            {(() => {
              const b = bins[hover]
              const cx = M.left + hover * slot + slot / 2
              const tw = 150
              const tx = Math.min(Math.max(cx - tw / 2, M.left), M.left + iw - tw)
              return (
                <>
                  <rect x={tx} y={M.top + 2} width={tw} height={38} fill="var(--bg-secondary)" stroke={GRID} />
                  <text x={tx + 8} y={M.top + 17} fontSize="10.5" fill="var(--text-primary)">
                    {xFormat(b.lo)} – {xFormat(b.hi)}
                  </text>
                  <text x={tx + 8} y={M.top + 32} fontSize="10.5" fill="var(--text-secondary)">
                    {b.count} sim{b.count === 1 ? '' : 's'} ({b.pct}%)
                  </text>
                </>
              )
            })()}
          </g>
        )}
      </svg>

      {refLines.length > 0 && (
        <div style={{ display: 'flex', gap: 18, flexWrap: 'wrap', marginTop: 6, fontSize: '0.73rem' }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: 6, color: 'var(--text-secondary)' }}>
            <span style={{ width: 14, height: 8, background: BAR, display: 'inline-block' }} />
            Consensus (this phase)
          </span>
          {refLines.map((r) => (
            <span key={r.label} style={{ display: 'flex', alignItems: 'center', gap: 6, color: 'var(--text-secondary)' }}>
              <span
                style={{
                  width: 14,
                  height: 0,
                  borderTop: `2px dashed ${REF}`,
                  display: 'inline-block',
                }}
              />
              {r.legend || r.label}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}

/* ------------------------------------------------------------- risk buckets */

function RiskBars({ risks }) {
  const [hover, setHover] = useState(null)
  if (!risks.length) {
    return (
      <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
        No named risks were detected in any simulation.
      </div>
    )
  }

  const rowH = 26
  const labelW = 300
  const trackW = 320

  return (
    <div>
      {risks.map((r, i) => (
        <div
          key={r.name}
          onMouseEnter={() => setHover(i)}
          onMouseLeave={() => setHover(null)}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            height: rowH,
            background: hover === i ? 'var(--bg-card-hover)' : 'transparent',
          }}
        >
          <div
            style={{
              width: labelW,
              flexShrink: 0,
              fontSize: '0.78rem',
              color: 'var(--text-secondary)',
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
            }}
            title={r.name}
          >
            {r.name}
          </div>

          <div style={{ width: trackW, flexShrink: 0, background: 'var(--bg-secondary)', height: 14, position: 'relative' }}>
            <div
              style={{
                width: `${r.pct}%`,
                height: '100%',
                background: BUCKET_COLOR[r.bucket],
                borderRadius: '0 3px 3px 0',
              }}
            />
          </div>

          {/* direct label: colour never carries the meaning alone */}
          <div style={{ fontSize: '0.78rem', color: 'var(--text-primary)', fontWeight: 700, width: 54, fontVariantNumeric: 'tabular-nums' }}>
            {r.pct}%
          </div>
          <div style={{ fontSize: '0.73rem', color: BUCKET_COLOR[r.bucket], whiteSpace: 'nowrap' }}>
            {BUCKET_ICON[r.bucket]} {r.bucket_label}
          </div>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
            {r.count} sim{r.count === 1 ? '' : 's'}
          </div>
        </div>
      ))}

      <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', marginTop: 14, paddingTop: 12, borderTop: `1px solid ${GRID}` }}>
        {[
          ['low', 'Low', '0–25%'],
          ['mid_low', 'Mid-Low', '25–50%'],
          ['mid_high', 'Mid-High', '50–75%'],
          ['high', 'High', '75–100%'],
        ].map(([key, label, range]) => (
          <span key={key} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.73rem', color: 'var(--text-secondary)' }}>
            <span style={{ color: BUCKET_COLOR[key] }}>{BUCKET_ICON[key]}</span>
            {label} <span style={{ color: 'var(--text-muted)' }}>({range} of sims)</span>
          </span>
        ))}
      </div>
    </div>
  )
}

/* --------------------------------------------------------------- table view */

function TableToggle({ open, onToggle }) {
  return (
    <button
      type="button"
      onClick={onToggle}
      className="print-hide"
      style={{
        background: 'transparent',
        border: '1px solid var(--border)',
        color: 'var(--accent-blue)',
        fontSize: '0.72rem',
        padding: '4px 10px',
        cursor: 'pointer',
        whiteSpace: 'nowrap',
      }}
    >
      {open ? 'Hide table' : 'Show table'}
    </button>
  )
}

function BinTable({ bins, xFormat, unit }) {
  return (
    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.75rem', marginTop: 12 }}>
      <thead>
        <tr style={{ color: 'var(--text-muted)' }}>
          <th style={{ textAlign: 'left', padding: '5px 8px', borderBottom: `1px solid ${GRID}` }}>{unit}</th>
          <th style={{ textAlign: 'right', padding: '5px 8px', borderBottom: `1px solid ${GRID}` }}>Simulations</th>
          <th style={{ textAlign: 'right', padding: '5px 8px', borderBottom: `1px solid ${GRID}` }}>Share</th>
        </tr>
      </thead>
      <tbody>
        {bins.filter((b) => b.count > 0).map((b, i) => (
          <tr key={i}>
            <td style={{ padding: '5px 8px', borderBottom: `1px solid ${GRID}`, color: 'var(--text-secondary)', fontVariantNumeric: 'tabular-nums' }}>
              {xFormat(b.lo)} – {xFormat(b.hi)}
            </td>
            <td style={{ padding: '5px 8px', borderBottom: `1px solid ${GRID}`, textAlign: 'right', color: 'var(--text-primary)', fontVariantNumeric: 'tabular-nums' }}>
              {b.count}
            </td>
            <td style={{ padding: '5px 8px', borderBottom: `1px solid ${GRID}`, textAlign: 'right', color: 'var(--text-secondary)', fontVariantNumeric: 'tabular-nums' }}>
              {b.pct}%
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}

/* -------------------------------------------------------------------- main */

export default function DeepAnalysisReport({ job }) {
  const [openTables, setOpenTables] = useState({})
  const toggle = (k) => setOpenTables((s) => ({ ...s, [k]: !s[k] }))

  if (!job) return null

  const report = job.report
  const running = job.status === 'running'
  const pct = job.requested ? Math.round((100 * (job.completed + job.failed)) / job.requested) : 0

  return (
    <div style={{ marginTop: 28 }}>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 18,
          borderBottom: '1px solid var(--border)',
          paddingBottom: 14,
          flexWrap: 'wrap',
          gap: 12,
        }}
      >
        <div>
          <h2 style={{ margin: 0, fontSize: '1.3rem', color: 'var(--text-primary)' }}>
            🔬 Deep Analysis — {job.requested} Simulations
          </h2>
          <div style={{ fontSize: '0.76rem', color: 'var(--text-muted)', marginTop: 5 }}>
            {job.target} · {job.indication} · every simulation individually timestamped and
            recorded in the registry
          </div>
        </div>
        <div style={{ textAlign: 'right', fontSize: '0.8rem' }}>
          <div style={{ color: running ? 'var(--accent-yellow)' : 'var(--accent-green)', fontWeight: 700 }}>
            {running ? `Running — ${pct}%` : job.status === 'done' ? 'Complete' : job.status}
          </div>
          <div style={{ color: 'var(--text-muted)', fontSize: '0.74rem', marginTop: 3 }}>
            {job.completed} succeeded · {job.failed} failed
          </div>
        </div>
      </div>

      {running && (
        <div style={{ marginBottom: 20 }}>
          <div style={{ height: 8, background: 'var(--bg-secondary)', border: '1px solid var(--border)' }}>
            <div style={{ width: `${pct}%`, height: '100%', background: BAR, transition: 'width 0.4s' }} />
          </div>
          <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)', marginTop: 6 }}>
            Statistics appear once the run finishes. Each simulation is a full 5-agent pipeline plus
            a DigiCert timestamp, so this takes several minutes.
          </div>
        </div>
      )}

      {job.errors && job.errors.length > 0 && (
        <div className="error-msg" style={{ marginBottom: 18 }}>
          {job.failed} simulation{job.failed === 1 ? '' : 's'} failed. First error: {job.errors[0]}
        </div>
      )}

      {report && report.n_completed > 0 && (
        <>
          {/* ---- CDR score ---- */}
          <Card
            title="CDR Score Distribution"
            subtitle={`Clinical Developability Risk across ${report.n_completed} simulations (1 = best, 100 = worst). Spread shows how stable the verdict is under repeated sampling.`}
            actions={<TableToggle open={openTables.cdr} onToggle={() => toggle('cdr')} />}
          >
            <StatTiles stats={report.cdr.stats} />
            <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', margin: '12px 0 4px' }}>
              95% CI of the mean: <strong>{report.cdr.stats.ci95_low} – {report.cdr.stats.ci95_high}</strong>
              {report.cdr.stats.cv_pct !== null && (
                <> · coefficient of variation <strong>{report.cdr.stats.cv_pct}%</strong></>
              )}
            </div>
            <Histogram
              bins={report.cdr.hist}
              xLabel="CDR score (lower is better)"
              xFormat={(v) => Math.round(v)}
            />
            {openTables.cdr && <BinTable bins={report.cdr.hist} xFormat={(v) => Math.round(v)} unit="CDR score range" />}
          </Card>

          {/* ---- per-phase ---- */}
          {['p1', 'p2', 'p3'].map((k) => {
            const ph = report.phases[k]
            if (!ph || !ph.consensus || !ph.consensus.n) return null
            return (
              <Card
                key={k}
                title={`${ph.label} — Probability of Success`}
                subtitle={
                  `Consensus probability across simulations, against the most optimistic ` +
                  `individual agent (the panel's ceiling) for the same phase.`
                }
                actions={<TableToggle open={openTables[k]} onToggle={() => toggle(k)} />}
              >
                <StatTiles stats={ph.consensus} format={(v) => fmtPct(v)} />

                <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', margin: '12px 0 4px', lineHeight: 1.6 }}>
                  Mean consensus <strong>{fmtPct(ph.consensus.mean)}</strong> · mean agent maximum{' '}
                  <strong style={{ color: REF }}>{fmtPct(ph.agent_max.mean)}</strong>
                  {ph.consensus_vs_agent_max_gap !== null && (
                    <> · consensus sits <strong>{fmtPct(ph.consensus_vs_agent_max_gap)}</strong> below the ceiling</>
                  )}
                  {ph.per_agent_mean && Object.keys(ph.per_agent_mean).length > 0 && (
                    <div style={{ marginTop: 6, color: 'var(--text-muted)' }}>
                      Per-agent means:{' '}
                      {Object.entries(ph.per_agent_mean)
                        .map(([a, v]) => `${a} ${fmtPct(v)}`)
                        .join(' · ')}
                    </div>
                  )}
                </div>

                <Histogram
                  bins={ph.consensus_hist}
                  xLabel={`${ph.label} consensus probability of success`}
                  xFormat={(v) => `${Math.round(v * 100)}%`}
                  refLines={
                    ph.agent_max.mean !== null && ph.agent_max.mean !== undefined
                      ? [{
                          value: ph.agent_max.mean,
                          label: `agent max ${fmtPct(ph.agent_max.mean, 0)}`,
                          legend: 'Mean agent maximum',
                        }]
                      : []
                  }
                />
                {openTables[k] && (
                  <BinTable bins={ph.consensus_hist} xFormat={(v) => `${Math.round(v * 100)}%`} unit={`${ph.label} probability range`} />
                )}
              </Card>
            )
          })}

          {/* ---- risks ---- */}
          <Card
            title="Risk Appearance Frequency"
            subtitle={
              `How often each named risk appeared across the ${report.n_completed} simulations. ` +
              `A risk appearing in most runs is a stable signal; one appearing rarely is model noise.`
            }
          >
            <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 16 }}>
              {report.risk_buckets.map((b) => (
                <div
                  key={b.bucket}
                  style={{
                    border: `1px solid ${BUCKET_COLOR[b.bucket]}`,
                    padding: '8px 14px',
                    minWidth: 120,
                    background: 'var(--bg-secondary)',
                  }}
                >
                  <div style={{ fontSize: '0.7rem', color: BUCKET_COLOR[b.bucket], fontWeight: 700 }}>
                    {BUCKET_ICON[b.bucket]} {b.label}
                  </div>
                  <div style={{ fontSize: '1.15rem', color: 'var(--text-primary)', fontWeight: 700, marginTop: 2 }}>
                    {b.n_risks}
                  </div>
                  <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>
                    risk{b.n_risks === 1 ? '' : 's'} at {b.range_label}
                  </div>
                </div>
              ))}
            </div>
            <RiskBars risks={report.risks} />
          </Card>

          {/* ---- verdicts + TCSP ---- */}
          <Card
            title="Verdict Stability & TCSP"
            subtitle="How consistently each agent returned the same categorical verdict, plus the total clinical success probability distribution."
          >
            <div style={{ display: 'flex', gap: 26, flexWrap: 'wrap' }}>
              {Object.entries(report.verdicts).map(([section, rows]) => (
                <div key={section} style={{ minWidth: 190 }}>
                  <div style={{ fontSize: '0.73rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: 6 }}>
                    {section}
                  </div>
                  {rows.map((r) => (
                    <div key={r.verdict} style={{ display: 'flex', justifyContent: 'space-between', gap: 12, fontSize: '0.78rem', padding: '3px 0' }}>
                      <span style={{ color: 'var(--text-secondary)' }}>{r.verdict}</span>
                      <span style={{ color: 'var(--text-primary)', fontWeight: 700, fontVariantNumeric: 'tabular-nums' }}>{r.pct}%</span>
                    </div>
                  ))}
                </div>
              ))}
              {report.tcsp && report.tcsp.stats && report.tcsp.stats.n > 0 && (
                <div style={{ minWidth: 190 }}>
                  <div style={{ fontSize: '0.73rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: 6 }}>
                    TCSP (P1×P2×P3)
                  </div>
                  {[['Mean', report.tcsp.stats.mean], ['Median', report.tcsp.stats.median], ['Min', report.tcsp.stats.min], ['Max', report.tcsp.stats.max]].map(
                    ([l, v]) => (
                      <div key={l} style={{ display: 'flex', justifyContent: 'space-between', gap: 12, fontSize: '0.78rem', padding: '3px 0' }}>
                        <span style={{ color: 'var(--text-secondary)' }}>{l}</span>
                        <span style={{ color: 'var(--text-primary)', fontWeight: 700, fontVariantNumeric: 'tabular-nums' }}>{fmtPct(v, 2)}</span>
                      </div>
                    )
                  )}
                </div>
              )}
            </div>
          </Card>

          {report.fingerprints && report.fingerprints.length > 0 && (
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', lineHeight: 1.6 }}>
              <strong>{report.fingerprints.length}</strong> of {report.n_requested} simulations were
              timestamped and stored; each is independently verifiable at{' '}
              <strong style={{ color: 'var(--accent-blue)' }}>{window.location.origin}/verify</strong>{' '}
              using its SHA-256 fingerprint. First: <code>{report.fingerprints[0]}</code>
            </div>
          )}
        </>
      )}
    </div>
  )
}
