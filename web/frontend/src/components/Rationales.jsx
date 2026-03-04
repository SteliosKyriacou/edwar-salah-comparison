import { useState } from "react";

function Collapsible({ title, children, defaultOpen = true }) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <div className="collapsible">
      <div className="collapsible-header" onClick={() => setOpen(!open)}>
        <h3>{title}</h3>
        <span className={`arrow ${open ? "open" : ""}`}>&#9654;</span>
      </div>
      {open && <div className="collapsible-body">{children}</div>}
    </div>
  );
}

export default function Rationales({ edward, salah }) {
  const edwardRationale = edward.rational ?? edward.rationale ?? "N/A";
  const salahRationale = salah.biological_rationale ?? "N/A";
  const p3Cap = salah.p3_cap_reason;

  return (
    <>
      <h2 className="section-title">Detailed Analysis</h2>

      <Collapsible title="Edward's MedChem Rationale">
        {edwardRationale.split("\n").map((line, i) => (
          <p key={i}>{line}</p>
        ))}
      </Collapsible>

      <Collapsible title="Salah's Biological & Clinical Rationale">
        {salahRationale.split("\n").map((line, i) => (
          <p key={i}>{line}</p>
        ))}
        {p3Cap && (
          <p>
            <strong>P3 Cap Reason:</strong> {p3Cap}
          </p>
        )}
      </Collapsible>
    </>
  );
}
