import { useState } from "react";

export default function RawJson({ edward, salah }) {
  const [tab, setTab] = useState("edward");
  const [open, setOpen] = useState(false);

  return (
    <div className="collapsible">
      <div className="collapsible-header" onClick={() => setOpen(!open)}>
        <h3>Raw JSON Output</h3>
        <span className={`arrow ${open ? "open" : ""}`}>&#9654;</span>
      </div>
      {open && (
        <div className="collapsible-body">
          <div className="json-tabs">
            <button
              className={`json-tab ${tab === "edward" ? "active" : ""}`}
              onClick={() => setTab("edward")}
            >
              Edward
            </button>
            <button
              className={`json-tab ${tab === "salah" ? "active" : ""}`}
              onClick={() => setTab("salah")}
            >
              Salah
            </button>
          </div>
          <pre className="json-pre">
            {JSON.stringify(tab === "edward" ? edward : salah, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}
