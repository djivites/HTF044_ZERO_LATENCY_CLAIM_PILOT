import React, { useState, useEffect } from 'react';

/**
 * Investigation Component (Screen 3: Real-Time AI Processing Pipeline)
 */
export default function Investigation({ caseTitle = "Active Case", onComplete, onBack }) {
  const [activeStep, setActiveStep] = useState(0);

  const steps = [
    { title: "Reading documents", desc: "Extracting text from PDFs, images and emails" },
    { title: "Extracting claims", desc: "Identifying statements from each document" },
    { title: "Identifying evidence", desc: "Finding supporting and contradicting evidence" },
    { title: "Building evidence graph", desc: "Connecting claims, evidence and documents" },
    { title: "Searching for contradictions", desc: "Analyzing conflicts between statements" },
    { title: "Building timeline", desc: "Creating chronological sequence" },
    { title: "Calculating case strength", desc: "Evaluating evidence and reliability" }
  ];

  useEffect(() => {
    const timer = setInterval(() => {
      setActiveStep(prev => {
        if (prev + 1 >= steps.length) {
          clearInterval(timer);
          setTimeout(() => onComplete(), 700);
          return prev + 1;
        }
        return prev + 1;
      });
    }, 850);

    return () => clearInterval(timer);
  }, [steps.length, onComplete]);

  return (
    <div className="investigation-view page-transition">
      <div className="investigation-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          {onBack && (
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={onBack}
              style={{ background: '#1e293b', color: '#cbd5e1', borderColor: '#334155' }}
            >
              ← Back to Case
            </button>
          )}
          <div className="sidebar-brand" onClick={onBack || onComplete}>
            <div className="brand-icon">🧠</div>
            <span className="brand-title">ClaimPilot</span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <span className="case-badge" style={{ background: '#1e293b', color: '#cbd5e1', borderColor: '#334155' }}>
            Case: {caseTitle}
          </span>
          <div className="user-avatar">U</div>
        </div>
      </div>

      <div className="investigation-container">
        <div className="investigation-intro">
          <h2 className="investigation-title">Analyzing Your Case</h2>
          <p className="investigation-sub">
            Our AI is reading your documents, extracting evidence, and building your interactive case graph...
          </p>
        </div>

        <div className="investigation-grid">
          {/* Steps Pipeline */}
          <div className="pipeline-steps-card">
            <div>
              {steps.map((step, idx) => {
                let statusClass = 'pending';
                let icon = idx + 1;

                if (idx < activeStep) {
                  statusClass = 'done';
                  icon = '✓';
                } else if (idx === activeStep) {
                  statusClass = 'active';
                  icon = '◉';
                } else {
                  icon = '○';
                }

                return (
                  <div key={idx} className="pipeline-step-item">
                    <div className={`step-indicator ${statusClass}`}>{icon}</div>
                    <div className="step-details">
                      <h4>${step.title}</h4>
                      <p>${step.desc}</p>
                    </div>
                  </div>
                );
              })}
            </div>

            <div style={{ marginTop: '20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              {onBack && (
                <button type="button" className="btn btn-secondary btn-sm" onClick={onBack} style={{ background: '#1e293b', color: '#94a3b8', borderColor: '#334155' }}>
                  ← Modify Evidence
                </button>
              )}
              <button type="button" className="btn btn-primary btn-sm" onClick={onComplete}>
                View Dashboard Now →
              </button>
            </div>
          </div>

          {/* AI Neural Radar Visualizer */}
          <div className="investigation-visual-panel">
            <div className="neural-radar" />
            <div className="neural-radar-inner" />

            <div className="ai-core-brain">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96.44 2.5 2.5 0 0 1-2.96-3.08 3 3 0 0 1-.34-5.58 2.5 2.5 0 0 1 1.32-4.24 2.5 2.5 0 0 1 4.44-2.04z" />
                <path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96.44 2.5 2.5 0 0 0 2.96-3.08 3 3 0 0 0 .34-5.58 2.5 2.5 0 0 0-1.32-4.24 2.5 2.5 0 0 0-4.44-2.04z" />
              </svg>
            </div>

            <div className="floating-intel-badge badge-conflict">CONFLICT</div>
            <div className="floating-intel-badge badge-supports">SUPPORTS</div>
            <div className="floating-intel-badge badge-evidence">EVIDENCE</div>

            <div className="doc-bubble doc-bubble-1">📄</div>
            <div className="doc-bubble doc-bubble-2">🛡️</div>
            <div className="doc-bubble doc-bubble-3">🖼️</div>
            <div className="doc-bubble doc-bubble-4">✉️</div>
          </div>
        </div>
      </div>
    </div>
  );
}
