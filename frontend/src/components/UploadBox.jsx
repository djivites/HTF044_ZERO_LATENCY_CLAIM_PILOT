import React, { useState, useRef } from 'react';

/**
 * UploadBox Component
 * Clean, user-driven case creation form with zero hardcoded data.
 * All fields start blank unless the user explicitly loads a demo preset.
 */
export default function UploadBox({
  onAnalyze,
  onBack,
  onFormEdit = () => {},
  isAnalyzing = false,
  analysisError = '',
  initialTitle = "",
  initialCompany = "",
  initialClaimant = "",
  initialDesc = "",
  initialFiles = []
}) {
  const [caseTitle, setCaseTitle] = useState(initialTitle);
  const [companyName, setCompanyName] = useState(initialCompany);
  const [claimantName, setClaimantName] = useState(initialClaimant);
  const [description, setDescription] = useState(initialDesc);
  const [isDragging, setIsDragging] = useState(false);
  const [files, setFiles] = useState(() => initialFiles.filter(item => item.file instanceof File));
  const [validationError, setValidationError] = useState("");

  const fileInputRef = useRef(null);

  const handleFormEdit = () => {
    setValidationError("");
    onFormEdit();
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files) {
      addRealFiles(Array.from(e.dataTransfer.files));
    }
  };

  const handleFileInputChange = (e) => {
    if (e.target.files) {
      addRealFiles(Array.from(e.target.files));
      e.target.value = '';
    }
  };

  const addRealFiles = (newFiles) => {
    handleFormEdit();
    const supportedExtensions = new Set(['pdf', 'docx', 'txt', 'md', 'json']);
    const supportedFiles = [];
    const unsupportedFiles = [];
    newFiles.forEach(file => {
      const ext = file.name.split('.').pop().toLowerCase();
      if (!supportedExtensions.has(ext)) {
        unsupportedFiles.push(file.name);
        return;
      }
      supportedFiles.push({
        file,
        name: file.name,
        size: (file.size / (1024 * 1024)).toFixed(1) + ' MB',
        type: ext,
        summary: `Attached ${ext.toUpperCase()} file`
      });
    });
    if (supportedFiles.length) {
      setFiles(prev => [...prev, ...supportedFiles]);
    }
    if (unsupportedFiles.length) {
      setValidationError(`Unsupported file type: ${unsupportedFiles.join(', ')}. Use PDF, DOCX, TXT, MD, or JSON.`);
    }
  };

  const removeFile = (idx) => {
    handleFormEdit();
    setFiles(prev => prev.filter((_, i) => i !== idx));
  };

  // Sample presets fill case details only; submitted evidence must come from the user.
  const handlePreset = (key) => {
    handleFormEdit();
    if (key === 'laptop') {
      setCaseTitle("Laptop Warranty Claim");
      setCompanyName("Acme Tech Support & Service Center");
      setClaimantName("Alex Morgan");
      setDescription("My laptop screen stopped working after 8 months of normal usage and the company rejected my warranty claim alleging customer physical damage.");
    } else if (key === 'rental') {
      setCaseTitle("Apartment Security Deposit Dispute");
      setCompanyName("Metropolitan Property Management");
      setClaimantName("Jordan Taylor");
      setDescription("Landlord withheld a security deposit alleging carpet stain and repainting, despite a move-in checklist acknowledging pre-existing wear.");
    } else if (key === 'insurance') {
      setCaseTitle("Auto Insurance Hail Damage Rejection");
      setCompanyName("Apex Casualty Insurance Co");
      setClaimantName("Sam Rivera");
      setDescription("An insurance claim for hail damage was denied on the basis that the damage was pre-existing wear and tear.");
    }
  };

  const handleTriggerAnalyze = () => {
    if (!caseTitle.trim()) {
      setValidationError("Please enter a Case Title.");
      return;
    }
    if (!description.trim()) {
      setValidationError("Please explain what happened in the description field.");
      return;
    }
    if (!files.some(file => file.file instanceof File)) {
      setValidationError("Attach at least one actual evidence file. Document name references cannot be analyzed.");
      return;
    }

    setValidationError("");
    onAnalyze({
      title: caseTitle,
      companyName: companyName.trim() || "Service Provider / Vendor",
      claimantName: claimantName.trim() || "Claimant",
      description,
      documents: files,
      uploadedFiles: files.map(file => file.file).filter(Boolean)
    });
  };

  return (
    <div className="create-case-view page-transition">
      {/* Back Button */}
      {onBack && (
        <button type="button" className="btn-back" onClick={onBack}>
          ← Back to Landing
        </button>
      )}

      <div className="page-header">
        <h2 className="page-title">Create a New Case</h2>
        <p className="page-subtitle">Enter your case facts and upload your evidence documents for AI investigation.</p>
      </div>

      {/* Demo Preset Bar */}
      <div className="demo-preset-row">
        <span className="demo-preset-label">Sample details only. Attach your own source documents to analyze.</span>
        <div className="preset-buttons">
          <button type="button" className="btn btn-secondary btn-sm" onClick={() => handlePreset('laptop')}>
            Sample: Laptop Warranty
          </button>
          <button type="button" className="btn btn-secondary btn-sm" onClick={() => handlePreset('rental')}>
            Sample: Rental Dispute
          </button>
          <button type="button" className="btn btn-secondary btn-sm" onClick={() => handlePreset('insurance')}>
            Sample: Auto Insurance
          </button>
        </div>
      </div>

      {validationError && (
        <div style={{ background: '#fef2f2', border: '1px solid #fecaca', color: '#dc2626', padding: '12px 16px', borderRadius: '8px', marginBottom: '20px', fontSize: '0.9rem', fontWeight: 600 }}>
          ⚠️ {validationError}
        </div>
      )}
      {analysisError && (
        <div role="alert" style={{ background: '#fef2f2', border: '1px solid #fecaca', color: '#dc2626', padding: '12px 16px', borderRadius: '8px', marginBottom: '20px', fontSize: '0.9rem', fontWeight: 600 }}>
          {analysisError}
        </div>
      )}

      <div className="case-form-card">
        {/* Case Title */}
        <div className="form-group">
          <label className="form-label">Case Title *</label>
          <input
            type="text"
            className="form-input"
            value={caseTitle}
            onChange={(e) => { setCaseTitle(e.target.value); handleFormEdit(); }}
            placeholder="e.g. Broken Laptop Screen Warranty Denial, Deposit Unlawfully Withheld..."
          />
        </div>

        {/* Company & Claimant Names */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '24px' }}>
          <div>
            <label className="form-label">Opposing Company / Vendor (Optional)</label>
            <input
              type="text"
              className="form-input"
              value={companyName}
              onChange={(e) => { setCompanyName(e.target.value); handleFormEdit(); }}
              placeholder="e.g. Acme Tech Support, Landlord LLC"
            />
          </div>
          <div>
            <label className="form-label">Your Name (Claimant) (Optional)</label>
            <input
              type="text"
              className="form-input"
              value={claimantName}
              onChange={(e) => { setClaimantName(e.target.value); handleFormEdit(); }}
              placeholder="e.g. Alex Morgan"
            />
          </div>
        </div>

        {/* What happened? */}
        <div className="form-group">
          <label className="form-label">What happened? (Dispute Summary) *</label>
          <textarea
            className="form-input form-textarea"
            value={description}
            onChange={(e) => { setDescription(e.target.value); handleFormEdit(); }}
            maxLength={600}
            rows={4}
            placeholder="Explain what the opposing party claimed, why their denial is wrongful, and what evidence you have..."
          />
          <div className="char-counter">{description.length}/600</div>
        </div>

        {/* Drag and Drop Zone */}
        <input
          type="file"
          ref={fileInputRef}
          multiple
          style={{ display: 'none' }}
          onChange={handleFileInputChange}
          accept=".pdf,.docx,.txt,.md,.json"
        />

        <div
          className={`dropzone ${isDragging ? 'dragover' : ''}`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
        >
          <div className="dropzone-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="17 8 12 3 7 8" />
              <line x1="12" y1="3" x2="12" y2="15" />
            </svg>
          </div>
          <div className="dropzone-title">Drag & drop evidence files here</div>
          <div className="dropzone-subtitle">or click to browse (PDF, DOCX, TXT, MD, JSON)</div>
        </div>

        {/* Document Action Row */}
        <div className="uploaded-section-title" style={{ margin: '0 0 14px' }}>
          Uploaded Evidence Documents ({files.length})
        </div>

        {/* Uploaded Documents List */}
        {files.length === 0 ? (
          <div className="empty-state-card">
            <p style={{ fontWeight: 600, color: '#334155', marginBottom: '4px' }}>No evidence documents attached yet</p>
            <p style={{ fontSize: '0.825rem' }}>Only files you attach here are uploaded and analyzed.</p>
          </div>
        ) : (
          <div className="uploaded-docs-list">
            {files.map((file, index) => (
              <div key={index} className="uploaded-doc-item">
                <div className="doc-info">
                  <div className={`doc-icon-badge ${file.type === 'pdf' ? 'badge-pdf' : 'badge-jpg'}`}>
                    {file.type.toUpperCase()}
                  </div>
                  <div>
                    <div className="doc-name">{file.name}</div>
                    <div className="doc-size">{file.size} • {file.summary}</div>
                  </div>
                </div>
                <button
                  type="button"
                  className="doc-remove-btn"
                  onClick={() => removeFile(index)}
                  title="Remove document"
                >
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <line x1="18" y1="6" x2="6" y2="18" />
                    <line x1="6" y1="6" x2="18" y2="18" />
                  </svg>
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Action Controls */}
        <div className="flex justify-between items-center" style={{ marginTop: '24px', paddingTop: '20px', borderTop: '1px solid #f1f5f9' }}>
          {onBack ? (
            <button type="button" className="btn btn-secondary" onClick={onBack}>
              Cancel
            </button>
          ) : <div />}
          
          <button
            type="button"
            className="btn btn-primary"
            onClick={handleTriggerAnalyze}
            disabled={isAnalyzing}
          >
            {isAnalyzing ? 'Analyzing documents...' : 'Analyze Case →'}
          </button>
        </div>
      </div>

    </div>
  );
}
