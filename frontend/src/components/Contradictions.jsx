import React, { useState } from 'react';

/**
 * Contradictions Component
 * Side-by-side breakdown of conflicting company claims vs. verified evidence facts.
 */
export default function Contradictions({ contradictions = [] }) {
  const [copiedId, setCopiedId] = useState(null);

  const handleCopyConflict = (item) => {
    const text = `CONTRADICTION ANALYSIS:\nCompany Claim: "${item.companyClaim.statement}" (${item.companyClaim.source})\nVS Verified Evidence: "${item.evidenceFact.statement}" (${item.evidenceFact.source})\nExplanation: ${item.explanation}`;
    navigator.clipboard?.writeText(text);
    setCopiedId(item.id);
    setTimeout(() => setCopiedId(null), 2500);
  };

  if (!contradictions || contradictions.length === 0) {
    return (
      <div className="content-box">
        <div style={{ padding: '24px', textAlign: 'center', color: '#64748b' }}>
          No contradictions detected. Case evidence is aligned.
        </div>
      </div>
    );
  }

  return (
    <div className="content-box">
      <div className="content-box-title">
        <span>Detected Contradictions</span>
        <span className="case-badge" style={{ background: '#fee2e2', color: '#dc2626' }}>
          {contradictions.length} Critical Conflicts Found
        </span>
      </div>

      <div className="contradictions-grid">
        {contradictions.map((c, index) => (
          <div key={c.id || index} className="contradiction-card">
            <div className="contradiction-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <strong style={{ fontSize: '0.95rem', color: '#0f172a' }}>
                  Contradiction #{index + 1}
                </strong>
                <span className="contradiction-badge">{c.severity}</span>
              </div>
              <button
                className="btn btn-secondary btn-sm"
                onClick={() => handleCopyConflict(c)}
              >
                {copiedId === c.id ? '✓ Copied Quote' : '📋 Copy Citation'}
              </button>
            </div>

            <div className="contradiction-versus">
              {/* Company Claim (Red) */}
              <div className="versus-box claim">
                <div className="versus-label">
                  🏢 {c.companyClaim.source}
                </div>
                <div className="versus-text">
                  "{c.companyClaim.statement}"
                </div>
              </div>

              {/* VS Badge */}
              <div className="versus-vs-badge">VS</div>

              {/* Evidence Fact (Green) */}
              <div className="versus-box fact">
                <div className="versus-label">
                  🛡️ {c.evidenceFact.source}
                </div>
                <div className="versus-text">
                  "{c.evidenceFact.statement}"
                </div>
              </div>
            </div>

            {/* AI Explanation */}
            <div style={{ marginTop: '12px', fontSize: '0.85rem', color: '#475569', lineHeight: 1.5 }}>
              <strong style={{ color: '#0f172a' }}>AI Dispute Analysis: </strong>
              {c.explanation}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
