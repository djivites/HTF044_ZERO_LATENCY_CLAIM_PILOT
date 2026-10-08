import React, { useState } from 'react';
import CaseScore from '../components/CaseScore';
import Contradictions from '../components/Contradictions';
import EvidenceGraph from '../components/EvidenceGraph';
import EvidenceList from '../components/EvidenceList';
import Timeline from '../components/Timeline';
import UploadBox from '../components/UploadBox';
import { analyzeUserCase } from '../services/caseEngine';
import { DEMO_CASES } from '../services/api';

/**
 * CaseAnalysis Page (Main Workspace)
 * Handles Dashboard, Create Case, Evidence Graph, and Response Center views.
 * Features back buttons on every page, smooth transitions, and zero unsolicited static data.
 */
export default function CaseAnalysis({
  activeView = 'dashboard',
  onNavigate,
  caseData = null,
  onCaseUpdate,
  onLoadDemo
}) {
  const [currentView, setCurrentView] = useState(activeView);
  const [currentTab, setCurrentTab] = useState('overview');
  
  // Active case state: strictly null if no case created and no demo selected
  const [activeCase, setActiveCase] = useState(caseData);

  const [responseTone, setResponseTone] = useState('firm');
  const [claimantName, setClaimantName] = useState(caseData?.claimantName || "");
  const [companyName, setCompanyName] = useState(caseData?.companyName || "");
  const [claimId, setClaimId] = useState(caseData?.claimId || "");
  const [responseText, setResponseText] = useState(caseData?.intelligence?.generatedResponse || "");
  const [toastMessage, setToastMessage] = useState(null);
  const [showAddEvidenceModal, setShowAddEvidenceModal] = useState(false);
  const [newEvidenceName, setNewEvidenceName] = useState("");

  const showToast = (msg) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3200);
  };

  const handleCopyResponse = () => {
    navigator.clipboard?.writeText(responseText);
    showToast('Dispute response copied to clipboard!');
  };

  const handleExportReport = () => {
    if (!activeCase) return;
    const report = `CLAIM PILOT CASE AUDIT DOSSIER
==================================================
Case: ${activeCase.title}
Claimant: ${claimantName || 'Claimant'}
Opposing Party: ${companyName || 'Opposing Party'}
Reference ID: ${claimId || 'N/A'}
Date: ${activeCase.createdAt}
Strength Score: ${activeCase.intelligence.strengthScore} / 100

METRICS
- Supporting Evidence: ${activeCase.intelligence.metrics.supporting}
- Company Claims: ${activeCase.intelligence.metrics.company}
- Contradictions Detected: ${activeCase.intelligence.metrics.contradictions}
- Missing Evidence Items: ${activeCase.intelligence.metrics.missing}

KEY FINDINGS
${activeCase.intelligence.keyFindings.map(f => `* ${f.text}`).join('\n')}

CONTRADICTIONS
${activeCase.intelligence.contradictions.map((c, i) => `
[Contradiction #${i + 1}] (${c.severity})
Company Assertion: "${c.companyClaim.statement}" (${c.companyClaim.source})
Evidence Record: "${c.evidenceFact.statement}" (${c.evidenceFact.source})
Analysis: ${c.explanation}
`).join('\n')}

FORMAL DISPUTE LETTER
--------------------------------------------------
${responseText}
`;

    const blob = new Blob([report], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `ClaimPilot_${activeCase.title.replace(/\s+/g, '_')}_Audit.txt`;
    a.click();
    showToast('Audit Dossier downloaded successfully!');
  };

  const handleToneChange = (tone) => {
    if (!activeCase) return;
    setResponseTone(tone);
    const intel = activeCase.intelligence;
    if (tone === 'formal') {
      setResponseText(intel.generatedResponse.replace(`Dear ${companyName || 'Company'}`, `Attention: Formal Legal & Dispute Bureau, ${companyName || 'Company'}`));
    } else if (tone === 'concise') {
      setResponseText(`To ${companyName || 'Dispute Department'},\n\nRe: Formal Denial Contest — ${activeCase.title} (Claim ID: ${claimId || 'N/A'}).\n\nYour denial asserts claimant liability. However, verified records and submitted evidence (${activeCase.documents.map(d => d.name).join(', ')}) confirm full compliance and lack of any external abuse.\n\nPlease furnish internal inspection photographs or approve immediate replacement/refund within five (5) business days.\n\nRespectfully,\n${claimantName || 'Claimant'}`);
    } else {
      setResponseText(intel.generatedResponse);
    }
    showToast(`Updated dispute response with ${tone} tone.`);
  };

  // Resolve a missing evidence item dynamically
  const handleResolveMissingEvidence = (missingItem) => {
    if (!activeCase) return;
    const updatedDocs = [
      ...activeCase.documents,
      {
        id: `doc-${Date.now()}`,
        name: `${missingItem.name.replace(/\s+/g, '_')}.pdf`,
        size: "1.8 MB",
        type: "pdf",
        summary: `User provided to resolve: ${missingItem.name}`
      }
    ];

    const updatedCase = analyzeUserCase({
      title: activeCase.title,
      description: activeCase.description,
      companyName,
      claimantName,
      claimId,
      documents: updatedDocs
    });

    setActiveCase(updatedCase);
    setResponseText(updatedCase.intelligence.generatedResponse);
    if (onCaseUpdate) onCaseUpdate(updatedCase);
    showToast(`✓ Resolved "${missingItem.name}". Strength score updated!`);
  };

  // Add custom evidence document to active case
  const handleAddCustomEvidence = (e) => {
    e.preventDefault();
    if (!newEvidenceName.trim() || !activeCase) return;

    const updatedDocs = [
      ...activeCase.documents,
      {
        id: `doc-${Date.now()}`,
        name: newEvidenceName.includes('.') ? newEvidenceName : `${newEvidenceName}.pdf`,
        size: "2.0 MB",
        type: newEvidenceName.toLowerCase().includes("jpg") || newEvidenceName.toLowerCase().includes("png") ? "jpg" : "pdf",
        summary: "User added evidence document"
      }
    ];

    const updatedCase = analyzeUserCase({
      title: activeCase.title,
      description: activeCase.description,
      companyName,
      claimantName,
      claimId,
      documents: updatedDocs
    });

    setActiveCase(updatedCase);
    setResponseText(updatedCase.intelligence.generatedResponse);
    setNewEvidenceName("");
    setShowAddEvidenceModal(false);
    if (onCaseUpdate) onCaseUpdate(updatedCase);
    showToast(`Added evidence: ${newEvidenceName}`);
  };

  const intel = activeCase?.intelligence;

  return (
    <div className="app-container">
      {/* Toast Notification */}
      {toastMessage && (
        <div className="toast-container">
          <div className="toast">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#10b981" strokeWidth="2">
              <polyline points="20 6 9 17 4 12" />
            </svg>
            <span>{toastMessage}</span>
          </div>
        </div>
      )}

      {/* Left Navigation Sidebar */}
      <aside className="app-sidebar">
        <div className="sidebar-brand" onClick={() => onNavigate('landing')} title="Go to Home">
          <div className="brand-icon">🧠</div>
          <span className="brand-title">ClaimPilot</span>
        </div>

        <div className="sidebar-action">
          <button className="btn-new-case" onClick={() => setCurrentView('create-case')}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <line x1="12" y1="5" x2="12" y2="19" />
              <line x1="5" y1="12" x2="19" y2="12" />
            </svg>
            <span>New Case</span>
          </button>
        </div>

        <nav className="sidebar-nav">
          <a
            className={`nav-item ${currentView === 'dashboard' ? 'active' : ''}`}
            onClick={() => setCurrentView('dashboard')}
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="3" y="3" width="7" height="9" /><rect x="14" y="3" width="7" height="5" />
              <rect x="14" y="12" width="7" height="9" /><rect x="3" y="16" width="7" height="5" />
            </svg>
            <span>Case Analysis</span>
          </a>

          <a
            className={`nav-item ${currentView === 'create-case' ? 'active' : ''}`}
            onClick={() => setCurrentView('create-case')}
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <polyline points="14 2 14 8 20 8" />
              <line x1="12" y1="18" x2="12" y2="12" /><line x1="9" y1="15" x2="15" y2="15" />
            </svg>
            <span>Upload Evidence</span>
          </a>

          <a
            className={`nav-item ${currentView === 'graph' ? 'active' : ''}`}
            onClick={() => setCurrentView('graph')}
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="18" cy="5" r="3" /><circle cx="6" cy="12" r="3" /><circle cx="18" cy="19" r="3" />
              <line x1="8.59" y1="13.51" x2="15.42" y2="17.49" />
              <line x1="15.41" y1="6.51" x2="8.59" y2="10.49" />
            </svg>
            <span>Evidence Graph</span>
          </a>

          <a
            className={`nav-item ${currentView === 'response' ? 'active' : ''}`}
            onClick={() => setCurrentView('response')}
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
            </svg>
            <span>Response Center</span>
          </a>
        </nav>

        <div className="sidebar-footer">
          <a className="nav-item" onClick={() => onNavigate('landing')}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
              <polyline points="9 22 9 12 15 12 15 22" />
            </svg>
            <span>Home Landing</span>
          </a>
          <a className="nav-item" onClick={() => showToast(activeCase ? `Active Case: ${activeCase.title}` : 'No active case loaded')}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
              <circle cx="12" cy="7" r="4" />
            </svg>
            <span>{claimantName || 'Profile'}</span>
          </a>
        </div>
      </aside>

      {/* Main Viewport */}
      <main className="app-main">
        {/* Universal Top Bar */}
        <header className="top-navbar">
          <div className="top-navbar-left">
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={() => onNavigate('landing')}
              title="Return to Landing Page"
            >
              ← Home
            </button>
            <span className="case-badge">
              {activeCase ? `Case: ${activeCase.title}` : 'No Active Case'}
            </span>
            {companyName && (
              <span style={{ fontSize: '0.8rem', color: '#64748b' }}>vs. {companyName}</span>
            )}
          </div>
          <div className="top-navbar-right">
            {activeCase && (
              <button type="button" className="btn btn-secondary btn-sm" onClick={handleExportReport}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                  <polyline points="7 10 12 15 17 10" />
                  <line x1="12" y1="15" x2="12" y2="3" />
                </svg>
                Export Report
              </button>
            )}
            <div className="user-avatar" title={`Claimant: ${claimantName || 'User'}`}>
              {claimantName ? claimantName[0].toUpperCase() : 'U'}
            </div>
          </div>
        </header>

        {/* ========================================================
             SCREEN 2: CREATE CASE / UPLOAD EVIDENCE
             ======================================================== */}
        {currentView === 'create-case' && (
          <UploadBox
            onBack={() => onNavigate('landing')}
            onAnalyze={(userInputs) => {
              const generated = analyzeUserCase(userInputs);
              setActiveCase(generated);
              setCompanyName(userInputs.companyName);
              setClaimantName(userInputs.claimantName);
              setResponseText(generated.intelligence.generatedResponse);
              if (onCaseUpdate) onCaseUpdate(generated);
              onNavigate('investigation');
            }}
          />
        )}

        {/* ========================================================
             SCREEN 4: CASE INTELLIGENCE DASHBOARD ⭐
             ======================================================== */}
        {currentView === 'dashboard' && (
          !activeCase ? (
            /* Pristine Empty State when user navigates directly without creating a case */
            <div style={{ padding: '40px', maxWidth: '800px', margin: '40px auto', textAlign: 'center' }} className="page-transition">
              <div style={{ fontSize: '3rem', marginBottom: '16px' }}>📂</div>
              <h2 style={{ fontSize: '1.75rem', fontWeight: 700, color: '#0f172a', marginBottom: '8px' }}>
                No Case Data Loaded
              </h2>
              <p style={{ color: '#64748b', fontSize: '0.95rem', marginBottom: '28px' }}>
                You haven't created or analyzed a case yet. Enter your own dispute evidence or explore a pre-built demo case to see ClaimPilot in action.
              </p>
              <div className="flex justify-center gap-3">
                <button type="button" className="btn btn-primary" onClick={() => setCurrentView('create-case')}>
                  + Create Your Case
                </button>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => {
                    const demo = DEMO_CASES.laptop;
                    setActiveCase(demo);
                    setCompanyName("Acme Tech Support & Service Center");
                    setClaimantName("Alex Morgan");
                    setClaimId("CLM-88421");
                    setResponseText(demo.intelligence.generatedResponse);
                    if (onLoadDemo) onLoadDemo('laptop');
                  }}
                >
                  Load Sample Live Demo
                </button>
              </div>
            </div>
          ) : (
            <section className="dashboard-view page-transition">
              {/* Back to Home Button */}
              <button type="button" className="btn-back" onClick={() => onNavigate('landing')}>
                ← Back to Home
              </button>

              <div className="dashboard-header">
                <div className="dashboard-title-area">
                  <h2>{activeCase.title}</h2>
                  <p>Analyzed on {activeCase.createdAt || 'Today'} • Disputing with {companyName || 'Service Provider'}</p>
                </div>
                <div className="flex gap-2">
                  <button
                    type="button"
                    className="btn btn-secondary btn-sm"
                    onClick={() => setCurrentView('create-case')}
                  >
                    ✏️ Edit Case
                  </button>
                  <button
                    type="button"
                    className="btn btn-secondary btn-sm"
                    onClick={() => setShowAddEvidenceModal(true)}
                  >
                    + Add Evidence
                  </button>
                  <button type="button" className="btn btn-secondary btn-sm" onClick={handleExportReport}>
                    Export Report
                  </button>
                </div>
              </div>

              {/* CaseScore Gauge & 4 Key Metric Cards */}
              <CaseScore score={intel.strengthScore} metrics={intel.metrics} />

              {/* Sub-tab Navigation Bar */}
              <div className="dash-tabs-bar">
                <button
                  type="button"
                  className={`dash-tab-btn ${currentTab === 'overview' ? 'active' : ''}`}
                  onClick={() => setCurrentTab('overview')}
                >
                  Overview
                </button>
                <button
                  type="button"
                  className={`dash-tab-btn ${currentTab === 'evidence' ? 'active' : ''}`}
                  onClick={() => setCurrentTab('evidence')}
                >
                  Evidence ({activeCase.documents.length})
                </button>
                <button
                  type="button"
                  className={`dash-tab-btn ${currentTab === 'timeline' ? 'active' : ''}`}
                  onClick={() => setCurrentTab('timeline')}
                >
                  Timeline
                </button>
                <button
                  type="button"
                  className={`dash-tab-btn ${currentTab === 'contradictions' ? 'active' : ''}`}
                  onClick={() => setCurrentTab('contradictions')}
                >
                  Contradictions ({intel.contradictions.length})
                </button>
                <button
                  type="button"
                  className={`dash-tab-btn ${currentTab === 'graph-tab' ? 'active' : ''}`}
                  onClick={() => setCurrentTab('graph-tab')}
                >
                  Evidence Graph
                </button>
              </div>

              {/* Tab Contents */}
              {currentTab === 'overview' && (
                <EvidenceList
                  documents={activeCase.documents}
                  keyFindings={intel.keyFindings}
                  onViewDocument={(d) => showToast(`Auditing source document: ${d.name}`)}
                />
              )}

              {currentTab === 'evidence' && (
                <div className="content-box">
                  <div className="content-box-title">
                    <span>Extracted Evidence Items ({activeCase.documents.length})</span>
                    <button
                      type="button"
                      className="btn btn-primary btn-sm"
                      onClick={() => setShowAddEvidenceModal(true)}
                    >
                      + Upload More Evidence
                    </button>
                  </div>
                  <div className="uploaded-docs-list">
                    {activeCase.documents.map((d, i) => (
                      <div key={i} className="uploaded-doc-item">
                        <div className="doc-info">
                          <div className={`doc-icon-badge ${d.type === 'pdf' ? 'badge-pdf' : 'badge-jpg'}`}>
                            {d.type ? d.type.toUpperCase() : 'DOC'}
                          </div>
                          <div>
                            <div className="doc-name">{d.name}</div>
                            <div className="doc-size">{d.summary || `${d.size} • Verified source`}</div>
                          </div>
                        </div>
                        <button
                          type="button"
                          className="btn btn-secondary btn-sm"
                          onClick={() => showToast(`Auditing ${d.name}`)}
                        >
                          Inspect
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {currentTab === 'timeline' && <Timeline timeline={intel.timeline} />}

              {currentTab === 'contradictions' && (
                <Contradictions contradictions={intel.contradictions} />
              )}

              {currentTab === 'graph-tab' && (
                <div className="content-box" style={{ padding: '16px' }}>
                  <div className="flex justify-between items-center" style={{ marginBottom: '12px' }}>
                    <h4 style={{ fontSize: '1rem', fontWeight: 700 }}>Interactive Case Evidence Graph</h4>
                    <button
                      type="button"
                      className="btn btn-primary btn-sm"
                      onClick={() => setCurrentView('graph')}
                    >
                      Open Dedicated Graph Screen →
                    </button>
                  </div>
                  <EvidenceGraph
                    graphData={activeCase.graph}
                    isDedicatedPage={false}
                    height="450px"
                  />
                </div>
              )}
            </section>
          )
        )}

        {/* ========================================================
             SCREEN 5: EVIDENCE GRAPH
             ======================================================== */}
        {currentView === 'graph' && (
          !activeCase ? (
            <div style={{ padding: '40px', textAlign: 'center' }} className="page-transition">
              <h3>No Case Loaded</h3>
              <p style={{ color: '#64748b', marginTop: '8px', marginBottom: '20px' }}>Create a case to explore its interactive evidence graph.</p>
              <button type="button" className="btn btn-primary" onClick={() => setCurrentView('create-case')}>+ Create Case</button>
            </div>
          ) : (
            <section className="graph-view page-transition">
              <button type="button" className="btn-back" onClick={() => setCurrentView('dashboard')}>
                ← Back to Dashboard
              </button>
              <EvidenceGraph
                graphData={activeCase.graph}
                isDedicatedPage={true}
                height="650px"
              />
            </section>
          )
        )}

        {/* ========================================================
             SCREEN 6: RESPONSE & ACTION CENTER
             ======================================================== */}
        {currentView === 'response' && (
          !activeCase ? (
            <div style={{ padding: '40px', textAlign: 'center' }} className="page-transition">
              <h3>No Case Loaded</h3>
              <p style={{ color: '#64748b', marginTop: '8px', marginBottom: '20px' }}>Create a case to generate evidence-backed dispute responses.</p>
              <button type="button" className="btn btn-primary" onClick={() => setCurrentView('create-case')}>+ Create Case</button>
            </div>
          ) : (
            <section className="response-view page-transition">
              <button type="button" className="btn-back" onClick={() => setCurrentView('dashboard')}>
                ← Back to Dashboard
              </button>

              <div className="response-header">
                <h2 className="page-title">Response & Action Center</h2>
                <p className="page-subtitle">Generate an evidence-backed formal response and execute recommended next steps.</p>
              </div>

              {/* Editable Parties Bar */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '16px', marginBottom: '20px' }}>
                <div>
                  <label className="form-label" style={{ fontSize: '0.8rem' }}>Recipient Company</label>
                  <input
                    type="text"
                    className="form-input"
                    value={companyName}
                    onChange={(e) => setCompanyName(e.target.value)}
                    placeholder="e.g. Acme Tech"
                  />
                </div>
                <div>
                  <label className="form-label" style={{ fontSize: '0.8rem' }}>Your Name (Claimant)</label>
                  <input
                    type="text"
                    className="form-input"
                    value={claimantName}
                    onChange={(e) => setClaimantName(e.target.value)}
                    placeholder="e.g. Alex Morgan"
                  />
                </div>
                <div>
                  <label className="form-label" style={{ fontSize: '0.8rem' }}>Claim / Reference ID</label>
                  <input
                    type="text"
                    className="form-input"
                    value={claimId}
                    onChange={(e) => setClaimId(e.target.value)}
                    placeholder="e.g. CLM-88421"
                  />
                </div>
              </div>

              <div className="response-grid">
                {/* Left Column */}
                <div>
                  {/* Mini Overview Meter */}
                  <div className="overview-mini-card">
                    <div className="mini-score-gauge">
                      <div className="gauge-circle" style={{ width: '48px', height: '48px' }}>
                        <svg className="gauge-svg" style={{ width: '48px', height: '48px' }}>
                          <circle className="gauge-bg" cx="24" cy="24" r="20" />
                          <circle
                            className="gauge-progress"
                            cx="24"
                            cy="24"
                            r="20"
                            style={{
                              strokeDasharray: 125,
                              strokeDashoffset: 125 - (intel.strengthScore / 100) * 125
                            }}
                          />
                        </svg>
                        <div className="gauge-text">
                          <span style={{ fontSize: '0.75rem', fontWeight: 800 }}>{intel.strengthScore}</span>
                        </div>
                      </div>
                      <div>
                        <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#0f172a' }}>Case Strength: {intel.strengthScore} / 100</h4>
                        <p style={{ fontSize: '0.75rem', color: '#64748b' }}>
                          {intel.strengthScore >= 75 ? 'High viability based on contradictory denial' : 'Moderate leverage'}
                        </p>
                      </div>
                    </div>

                    <div className="flex gap-2">
                      <div className="mini-pill-tag amber">
                        <span>⚠️</span>
                        <span>{intel.metrics.contradictions} Contradictions</span>
                      </div>
                      <div className="mini-pill-tag orange">
                        <span>📋</span>
                        <span>{intel.missingEvidence.length} Missing Items</span>
                      </div>
                    </div>
                  </div>

                  {/* Recommended Action */}
                  <div className="action-recommendation-card">
                    <div className="action-icon-box">💡</div>
                    <div className="action-text">
                      <h4>{intel.recommendedAction.headline}</h4>
                      <p>{intel.recommendedAction.detail}</p>
                    </div>
                  </div>

                  {/* Generated Response Editor */}
                  <div className="response-editor-card">
                    <div className="editor-header">
                      <div className="editor-title">Generated Response Letter</div>
                      <div className="tone-selector">
                        <button
                          type="button"
                          className={`btn btn-sm ${responseTone === 'formal' ? 'btn-primary' : 'btn-secondary'}`}
                          onClick={() => handleToneChange('formal')}
                        >
                          Formal Legal
                        </button>
                        <button
                          type="button"
                          className={`btn btn-sm ${responseTone === 'firm' ? 'btn-primary' : 'btn-secondary'}`}
                          onClick={() => handleToneChange('firm')}
                        >
                          Firm & Assertive
                        </button>
                        <button
                          type="button"
                          className={`btn btn-sm ${responseTone === 'concise' ? 'btn-primary' : 'btn-secondary'}`}
                          onClick={() => handleToneChange('concise')}
                        >
                          Concise
                        </button>
                      </div>
                    </div>

                    <textarea
                      className="response-textarea"
                      value={responseText}
                      rows={12}
                      onChange={(e) => setResponseText(e.target.value)}
                    />

                    <div className="response-actions-bar">
                      <div className="flex gap-2">
                        <button type="button" className="btn btn-secondary btn-sm" onClick={handleCopyResponse}>
                          📋 Copy Letter
                        </button>
                        <button type="button" className="btn btn-secondary btn-sm" onClick={handleExportReport}>
                          📥 Download Dossier
                        </button>
                      </div>
                      <button
                        type="button"
                        className="btn btn-primary btn-sm"
                        onClick={() => {
                          const targetEmail = `support@${(companyName || 'company').toLowerCase().replace(/[^a-z0-9]/g, '')}.com`;
                          window.location.href = `mailto:${targetEmail}?subject=Dispute:%20${encodeURIComponent(activeCase.title)}&body=${encodeURIComponent(responseText)}`;
                          showToast('Opened email draft in your default client!');
                        }}
                      >
                        ✉️ Send Email
                      </button>
                    </div>
                  </div>
                </div>

                {/* Right Column: Missing Evidence Checklist */}
                <div>
                  <div className="missing-evidence-card">
                    <h3 className="missing-evidence-title">Missing Evidence Checklist</h3>
                    <p className="missing-evidence-sub">
                      Upload or add these items to immediately increase your case strength score and legal leverage:
                    </p>

                    <div className="missing-checklist">
                      {intel.missingEvidence.length === 0 ? (
                        <div style={{ padding: '16px', background: '#ecfdf5', borderRadius: '8px', color: '#065f46', fontSize: '0.875rem' }}>
                          ✓ All critical evidence collected! No pending missing items.
                        </div>
                      ) : (
                        intel.missingEvidence.map((item) => (
                          <div key={item.id} className="missing-item-card">
                            <div className="missing-item-header">
                              <span className="missing-item-name">{item.name}</span>
                              <span className={`priority-tag priority-${item.priority.toLowerCase()}`}>
                                {item.priority} Priority
                              </span>
                            </div>
                            <div className="missing-item-desc">{item.desc}</div>
                            <button
                              type="button"
                              className="btn btn-secondary btn-sm"
                              onClick={() => handleResolveMissingEvidence(item)}
                            >
                              + Add This Evidence Item
                            </button>
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </section>
          )
        )}
      </main>

      {/* Add Custom Evidence Modal */}
      {showAddEvidenceModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <h3 style={{ fontSize: '1.2rem', fontWeight: 700, marginBottom: '12px', color: '#0f172a' }}>
              Add Evidence Document
            </h3>
            <p style={{ fontSize: '0.85rem', color: '#64748b', marginBottom: '16px' }}>
              Enter document title (e.g. Technician_Bench_Photos.jpg, Intake_Checklist.pdf):
            </p>
            <input
              type="text"
              className="form-input"
              value={newEvidenceName}
              onChange={(e) => setNewEvidenceName(e.target.value)}
              placeholder="e.g. Independent_Diagnostic_Report.pdf"
              style={{ marginBottom: '20px' }}
              autoFocus
            />
            <div className="flex justify-between">
              <button type="button" className="btn btn-secondary" onClick={() => setShowAddEvidenceModal(false)}>
                Cancel
              </button>
              <button type="button" className="btn btn-primary" onClick={handleAddCustomEvidence}>
                Upload & Recalculate
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
