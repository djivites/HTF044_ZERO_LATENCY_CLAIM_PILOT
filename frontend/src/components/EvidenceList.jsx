import React from 'react';

/**
 * EvidenceList Component
 * Displays extracted evidence documents, metadata, and key findings.
 */
export default function EvidenceList({
  documents = [],
  keyFindings = [],
  onViewDocument
}) {
  return (
    <div className="overview-grid">
      {/* Key Findings Box */}
      <div className="content-box">
        <div className="content-box-title">
          <span>Key Findings</span>
          <span className="case-badge">{keyFindings.length} Insights</span>
        </div>
        <div className="findings-list">
          {keyFindings.map((finding, idx) => (
            <div key={idx} className={`finding-item ${finding.type}`}>
              <div className="finding-icon">
                {finding.type === 'success' ? '🟢' : finding.type === 'danger' ? '🔴' : '🟠'}
              </div>
              <div>{finding.text}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Document Summary Box */}
      <div className="content-box">
        <div className="content-box-title">
          <span>Document Summary</span>
          <span className="case-badge">{documents.length} Files</span>
        </div>
        <div className="doc-summary-list">
          {documents.map((doc, idx) => (
            <div key={doc.id || idx} className="doc-summary-card">
              <div className="doc-info">
                <div className={`doc-icon-badge ${doc.type === 'pdf' ? 'badge-pdf' : 'badge-jpg'}`}>
                  {doc.type ? doc.type.toUpperCase() : 'DOC'}
                </div>
                <div className="doc-summary-meta">
                  <h5>{doc.name}</h5>
                  <p>{doc.summary || doc.size}</p>
                </div>
              </div>
              <button
                className="btn btn-secondary btn-sm"
                onClick={() => onViewDocument ? onViewDocument(doc) : alert(`Inspecting ${doc.name}`)}
              >
                Inspect
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
