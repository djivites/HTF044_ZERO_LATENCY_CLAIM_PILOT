import React, { useState, useRef } from 'react';

/**
 * UploadBox Component
 * Clean, user-driven case creation form with zero hardcoded data.
 * All fields start blank unless the user explicitly loads a demo preset.
 */
export default function UploadBox({
  onAnalyze,
  onBack,
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
  const [files, setFiles] = useState(initialFiles);
  const [customDocName, setCustomDocName] = useState("");
  const [showAddDocModal, setShowAddDocModal] = useState(false);
  const [validationError, setValidationError] = useState("");

  const fileInputRef = useRef(null);

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
    }
  };

  const addRealFiles = (newFiles) => {
    setValidationError("");
    const formatted = newFiles.map(f => {
      const ext = f.name.split('.').pop().toLowerCase();
      return {
        name: f.name,
        size: (f.size / (1024 * 1024)).toFixed(1) + ' MB',
        type: ext.includes('jp') || ext.includes('png') ? 'jpg' : 'pdf',
        summary: `User attached ${ext.toUpperCase()} document`
      };
    });
    setFiles(prev => [...prev, ...formatted]);
  };

  const handleAddCustomDoc = (e) => {
    e.preventDefault();
    if (!customDocName.trim()) return;
    setValidationError("");
    const ext = customDocName.includes('.') ? customDocName.split('.').pop().toLowerCase() : 'pdf';
    setFiles(prev => [
      ...prev,
      {
        name: customDocName.includes('.') ? customDocName : `${customDocName}.pdf`,
        size: "1.2 MB",
        type: ext.includes('jp') || ext.includes('png') ? 'jpg' : 'pdf',
        summary: "User added evidence file"
      }
    ]);
    setCustomDocName("");
    setShowAddDocModal(false);
  };

  const removeFile = (idx) => {
    setFiles(prev => prev.filter((_, i) => i !== idx));
  };

  // Explicit preset loader (Only fills data when user clicks a preset)
  const handlePreset = (key) => {
    setValidationError("");
    if (key === 'laptop') {
      setCaseTitle("Laptop Warranty Claim");
      setCompanyName("Acme Tech Support & Service Center");
      setClaimantName("Alex Morgan");
      setDescription("My laptop screen stopped working after 8 months of normal usage and the company rejected my warranty claim alleging customer physical damage.");
      setFiles([
        { name: "Invoice.pdf", size: "2.4 MB", type: "pdf", summary: "Purchase on Jan 10, 2024" },
        { name: "Warranty.pdf", size: "1.1 MB", type: "pdf", summary: "Standard coverage clause 4.2" },
        { name: "Company_Response.pdf", size: "845 KB", type: "pdf", summary: "Rejection citing physical damage" },
        { name: "Repair_Report.pdf", size: "1.3 MB", type: "pdf", summary: "Service note: No external impact marks observed" },
        { name: "Laptop_Damage.jpg", size: "2.1 MB", type: "jpg", summary: "High-res photos showing intact bezel" }
      ]);
    } else if (key === 'rental') {
      setCaseTitle("Apartment Security Deposit Dispute");
      setCompanyName("Metropolitan Property Management");
      setClaimantName("Jordan Taylor");
      setDescription("Landlord withheld $1,800 security deposit alleging carpet stain and repainting, despite move-in checklist acknowledging pre-existing wear.");
      setFiles([
        { name: "Lease_Agreement.pdf", size: "1.8 MB", type: "pdf", summary: "Standard lease agreement Section 14" },
        { name: "Move_In_Inspection.pdf", size: "950 KB", type: "pdf", summary: "Pre-existing carpet wear acknowledged" },
        { name: "Move_Out_Photos.zip", size: "8.2 MB", type: "jpg", summary: "Pristine walls and clean floors" },
        { name: "Deposit_Notice.pdf", size: "620 KB", type: "pdf", summary: "Deduction notice itemizing $1,800" }
      ]);
    } else if (key === 'insurance') {
      setCaseTitle("Auto Insurance Hail Damage Rejection");
      setCompanyName("Apex Casualty Insurance Co");
      setClaimantName("Sam Rivera");
      setDescription("Insurance claims adjuster denied comprehensive hail storm roof damage claim stating damage was pre-existing wear and tear.");
      setFiles([
        { name: "Insurance_Policy.pdf", size: "2.2 MB", type: "pdf", summary: "Comprehensive weather peril coverage" },
        { name: "Body_Shop_Estimate.pdf", size: "1.4 MB", type: "pdf", summary: "Certified hail dent count & repair quote" },
        { name: "Weather_Service_Hail_Report.pdf", size: "890 KB", type: "pdf", summary: "NOAA verified severe hail storm timestamp" },
        { name: "Vehicle_Photos.jpg", size: "4.5 MB", type: "jpg", summary: "Recent hood and roof hail impact photos" }
      ]);
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
    if (files.length === 0) {
      setValidationError("Please upload or add at least one evidence document before running investigation.");
      return;
    }

    setValidationError("");
    onAnalyze({
      title: caseTitle,
      companyName: companyName.trim() || "Service Provider / Vendor",
      claimantName: claimantName.trim() || "Claimant",
      description,
      documents: files
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
        <span className="demo-preset-label">⚡ Want to test with sample data?</span>
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

      <div className="case-form-card">
        {/* Case Title */}
        <div className="form-group">
          <label className="form-label">Case Title *</label>
          <input
            type="text"
            className="form-input"
            value={caseTitle}
            onChange={(e) => { setCaseTitle(e.target.value); setValidationError(""); }}
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
              onChange={(e) => setCompanyName(e.target.value)}
              placeholder="e.g. Acme Tech Support, Landlord LLC"
            />
          </div>
          <div>
            <label className="form-label">Your Name (Claimant) (Optional)</label>
            <input
              type="text"
              className="form-input"
              value={claimantName}
              onChange={(e) => setClaimantName(e.target.value)}
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
            onChange={(e) => { setDescription(e.target.value); setValidationError(""); }}
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
          accept=".pdf,.doc,.docx,.jpg,.jpeg,.png,.eml,.zip"
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
          <div className="dropzone-subtitle">or click to browse from your device (PDF, DOCX, Images, Emails)</div>
        </div>

        {/* Document Action Row */}
        <div className="flex justify-between items-center" style={{ marginBottom: '14px' }}>
          <div className="uploaded-section-title" style={{ margin: 0 }}>
            Uploaded Evidence Documents ({files.length})
          </div>
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={() => setShowAddDocModal(true)}
          >
            + Add Document by Name
          </button>
        </div>

        {/* Uploaded Documents List */}
        {files.length === 0 ? (
          <div className="empty-state-card">
            <p style={{ fontWeight: 600, color: '#334155', marginBottom: '4px' }}>No evidence documents attached yet</p>
            <p style={{ fontSize: '0.825rem' }}>Drag & drop files above, browse from your computer, or click "+ Add Document by Name" to add a file reference.</p>
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
          >
            Analyze Case →
          </button>
        </div>
      </div>

      {/* Add Custom Document Modal */}
      {showAddDocModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <h3 style={{ fontSize: '1.2rem', fontWeight: 700, marginBottom: '12px', color: '#0f172a' }}>
              Add Document Reference
            </h3>
            <p style={{ fontSize: '0.85rem', color: '#64748b', marginBottom: '16px' }}>
              Type the name of the document or report to include in your case graph:
            </p>
            <input
              type="text"
              className="form-input"
              value={customDocName}
              onChange={(e) => setCustomDocName(e.target.value)}
              placeholder="e.g. Diagnostic_Inspection_Sheet.pdf, Damaged_Screen.jpg, Rejection_Notice.pdf"
              style={{ marginBottom: '20px' }}
              autoFocus
            />
            <div className="flex justify-between">
              <button type="button" className="btn btn-secondary" onClick={() => setShowAddDocModal(false)}>
                Cancel
              </button>
              <button type="button" className="btn btn-primary" onClick={handleAddCustomDoc}>
                Add Document
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
