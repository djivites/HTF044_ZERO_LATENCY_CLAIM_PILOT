import { ClaimPilotAPI, DEMO_CASES } from './api.js';
import { analyzeUserCase } from './caseEngine.js';

/**
 * ClaimPilot Application State & Controllers
 */
const state = {
  currentView: 'landing', // 'landing', 'create-case', 'investigation', 'dashboard', 'graph', 'response'
  currentTab: 'overview', // 'overview', 'evidence', 'timeline', 'contradictions', 'graph-tab'
  activeCaseKey: null,
  currentCase: null,
  uploadedFiles: [],
  investigationStep: 0,
  investigationTimer: null,
  selectedNode: null
};

// UI Elements Cache
const DOM = {
  views: {
    landing: document.getElementById('view-landing'),
    appShell: document.getElementById('view-app-shell'),
    createCase: document.getElementById('page-create-case'),
    investigation: document.getElementById('view-investigation'),
    dashboard: document.getElementById('page-dashboard'),
    graph: document.getElementById('page-graph'),
    response: document.getElementById('page-response')
  },
  sidebarNavs: document.querySelectorAll('.sidebar-nav .nav-item'),
  toastContainer: document.getElementById('toast-container')
};

/**
 * Navigation & Routing
 */
export function navigateTo(viewName) {
  state.currentView = viewName;
  window.location.hash = viewName === 'landing' ? '#/' : `#/${viewName}`;

  // Handle special full-screen views (landing and investigation)
  if (viewName === 'landing') {
    DOM.views.landing.classList.remove('hidden');
    DOM.views.appShell.classList.add('hidden');
    DOM.views.investigation.classList.add('hidden');
    window.scrollTo({ top: 0, behavior: 'smooth' });
    return;
  }

  if (viewName === 'investigation') {
    const titleVal = document.getElementById('case-title-input')?.value || state.currentCase.title;
    const descVal = document.getElementById('case-desc-input')?.value || state.currentCase.description;
    
    // Dynamically compute intelligence from actual user inputs & files
    state.currentCase = analyzeUserCase({
      title: titleVal,
      description: descVal,
      documents: state.uploadedFiles.map(f => ({
        name: f.name,
        size: f.size,
        type: f.ext.toLowerCase(),
        summary: `User attached evidence document (${f.size})`
      }))
    });

    const badge = document.getElementById('investigation-case-name');
    if (badge) badge.innerText = `Case: ${state.currentCase.title}`;

    DOM.views.landing.classList.add('hidden');
    DOM.views.appShell.classList.add('hidden');
    DOM.views.investigation.classList.remove('hidden');
    startInvestigationPipeline();
    return;
  }

  // App shell views
  DOM.views.landing.classList.add('hidden');
  DOM.views.investigation.classList.add('hidden');
  DOM.views.appShell.classList.remove('hidden');

  // Hide all inner pages
  ['createCase', 'dashboard', 'graph', 'response'].forEach(p => {
    DOM.views[p].classList.add('hidden');
  });

  // Activate target page
  if (viewName === 'create-case') {
    DOM.views.createCase.classList.remove('hidden');
    updateSidebarActive('create-case');
  } else if (viewName === 'dashboard') {
    DOM.views.dashboard.classList.remove('hidden');
    updateSidebarActive('dashboard');
    renderDashboard();
  } else if (viewName === 'graph') {
    DOM.views.graph.classList.remove('hidden');
    updateSidebarActive('graph');
    renderEvidenceGraph('graph-canvas-container', 'graph-svg-layer');
  } else if (viewName === 'response') {
    DOM.views.response.classList.remove('hidden');
    updateSidebarActive('response');
    renderResponseCenter();
  }

  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function updateSidebarActive(pageKey) {
  DOM.sidebarNavs.forEach(nav => {
    if (nav.dataset.target === pageKey) {
      nav.classList.add('active');
    } else {
      nav.classList.remove('active');
    }
  });
}

/**
 * Toast notifications
 */
export function showToast(message, type = 'info') {
  const toast = document.createElement('div');
  toast.className = 'toast';
  toast.innerHTML = `
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="${type === 'success' ? '#10b981' : '#6366f1'}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
      <polyline points="22 4 12 14.01 9 11.01"></polyline>
    </svg>
    <span>${message}</span>
  `;
  DOM.toastContainer.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    setTimeout(() => toast.remove(), 300);
  }, 3200);
}

/**
 * Case Presets Loader
 */
export function loadCasePreset(key) {
  if (!DEMO_CASES[key]) return;
  state.activeCaseKey = key;
  state.currentCase = JSON.parse(JSON.stringify(DEMO_CASES[key]));

  const titleInput = document.getElementById('case-title-input');
  const descInput = document.getElementById('case-desc-input');
  if (titleInput && descInput) {
    titleInput.value = state.currentCase.title;
    descInput.value = state.currentCase.description;
    document.getElementById('char-count').innerText = `${state.currentCase.description.length}/500`;
  }

  // Update uploaded files
  state.uploadedFiles = state.currentCase.documents.map(d => ({
    name: d.name,
    size: d.size,
    type: d.type === 'pdf' ? 'badge-pdf' : (d.type === 'image' ? 'badge-jpg' : 'badge-eml'),
    ext: d.type.toUpperCase()
  }));

  renderUploadedFiles();
  showToast(`Loaded "${state.currentCase.title}" preset data.`, 'success');
}

/**
 * Render Uploaded Documents List
 */
function renderUploadedFiles() {
  const list = document.getElementById('uploaded-docs-list');
  const countSpan = document.getElementById('uploaded-count-span');
  if (!list) return;

  if (state.uploadedFiles.length === 0) {
    list.innerHTML = `
      <div class="empty-state-card">
        <p style="font-weight:600; color:#334155; margin-bottom:4px;">No evidence documents attached yet</p>
        <p style="font-size:0.825rem;">Drag & drop files above or click to browse.</p>
      </div>
    `;
    return;
  }

  state.uploadedFiles.forEach((file, index) => {
    const item = document.createElement('div');
    item.className = 'uploaded-doc-item';
    item.innerHTML = `
      <div class="doc-info">
        <div class="doc-icon-badge ${file.type}">${file.ext || 'DOC'}</div>
        <div>
          <div class="doc-name">${file.name}</div>
          <div class="doc-size">${file.size} • Ready for analysis</div>
        </div>
      </div>
      <button class="doc-remove-btn" title="Remove" data-index="${index}">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="18" y1="6" x2="6" y2="18"></line>
          <line x1="6" y1="6" x2="18" y2="18"></line>
        </svg>
      </button>
    `;

    item.querySelector('.doc-remove-btn').addEventListener('click', (e) => {
      e.stopPropagation();
      state.uploadedFiles.splice(index, 1);
      renderUploadedFiles();
      showToast(`Removed ${file.name}`);
    });

    list.appendChild(item);
  });
}

/**
 * Investigation Pipeline Logic (Screen 3)
 */
function startInvestigationPipeline() {
  const steps = [
    { title: "Reading documents", desc: "Extracting text from PDFs, images and emails" },
    { title: "Extracting claims", desc: "Identifying statements from each document" },
    { title: "Identifying evidence", desc: "Finding supporting and contradicting evidence" },
    { title: "Building evidence graph", desc: "Connecting claims, evidence and documents" },
    { title: "Searching for contradictions", desc: "Analyzing conflicts between statements" },
    { title: "Building timeline", desc: "Creating chronological sequence" },
    { title: "Calculating case strength", desc: "Evaluating evidence and reliability" }
  ];

  const stepsList = document.getElementById('investigation-pipeline-steps');
  if (!stepsList) return;

  state.investigationStep = 0;
  if (state.investigationTimer) clearInterval(state.investigationTimer);

  function renderSteps() {
    stepsList.innerHTML = '';
    steps.forEach((step, idx) => {
      let statusClass = 'pending';
      let icon = idx + 1;

      if (idx < state.investigationStep) {
        statusClass = 'done';
        icon = '✓';
      } else if (idx === state.investigationStep) {
        statusClass = 'active';
        icon = '◉';
      } else {
        icon = '○';
      }

      const item = document.createElement('div');
      item.className = 'pipeline-step-item';
      item.innerHTML = `
        <div class="step-indicator ${statusClass}">${icon}</div>
        <div class="step-details">
          <h4>${step.title}</h4>
          <p>${step.desc}</p>
        </div>
      `;
      stepsList.appendChild(item);
    });
  }

  renderSteps();

  // Step progression every 900ms
  state.investigationTimer = setInterval(() => {
    state.investigationStep++;
    renderSteps();

    if (state.investigationStep >= steps.length) {
      clearInterval(state.investigationTimer);
      setTimeout(() => {
        showToast("Investigation complete! Case Intelligence Ready.", "success");
        navigateTo('dashboard');
      }, 700);
    }
  }, 850);
}

/**
 * Case Intelligence Dashboard Controller (Screen 4)
 */
function renderDashboard() {
  if (!state.currentCase) {
    state.currentCase = JSON.parse(JSON.stringify(DEMO_CASES.laptop));
  }
  const c = state.currentCase;
  const intel = c.intelligence;

  // Header & Title
  document.getElementById('dash-case-title').innerText = c.title;
  document.getElementById('dash-case-date').innerText = `Analyzed on ${c.createdAt || 'Aug 19, 2024'}`;
  document.getElementById('nav-case-badge').innerText = `Case: ${c.title}`;

  // Metric Cards
  document.getElementById('gauge-score-val').innerText = intel.strengthScore;
  document.getElementById('metric-val-supporting').innerText = intel.metrics.supporting;
  document.getElementById('metric-val-company').innerText = intel.metrics.company;
  document.getElementById('metric-val-contradictions').innerText = intel.metrics.contradictions;
  document.getElementById('metric-val-missing').innerText = intel.metrics.missing;

  // Gauge animation
  const circle = document.getElementById('gauge-progress-circle');
  if (circle) {
    const radius = 26;
    const circumference = 2 * Math.PI * radius;
    const offset = circumference - (intel.strengthScore / 100) * circumference;
    circle.style.strokeDashoffset = offset;
  }

  renderDashboardTab(state.currentTab);
}

export function switchDashboardTab(tabName) {
  state.currentTab = tabName;
  document.querySelectorAll('.dash-tab-btn').forEach(btn => {
    if (btn.dataset.tab === tabName) btn.classList.add('active');
    else btn.classList.remove('active');
  });
  renderDashboardTab(tabName);
}

function renderDashboardTab(tabName) {
  const container = document.getElementById('dash-tab-content');
  if (!container) return;

  const intel = state.currentCase.intelligence;

  if (tabName === 'overview') {
    container.innerHTML = `
      <div class="overview-grid">
        <div class="content-box">
          <div class="content-box-title">
            <span>Key Findings</span>
            <span class="case-badge">${intel.keyFindings.length} Insights</span>
          </div>
          <div class="findings-list">
            ${intel.keyFindings.map(f => `
              <div class="finding-item ${f.type}">
                <div class="finding-icon">
                  ${f.type === 'success' ? '🟢' : f.type === 'danger' ? '🔴' : '🟠'}
                </div>
                <div>${f.text}</div>
              </div>
            `).join('')}
          </div>
        </div>

        <div class="content-box">
          <div class="content-box-title">
            <span>Document Summary</span>
            <span class="case-badge">${state.currentCase.documents.length} Files</span>
          </div>
          <div class="doc-summary-list">
            ${state.currentCase.documents.map(d => `
              <div class="doc-summary-card">
                <div class="doc-info">
                  <div class="doc-icon-badge ${d.type === 'pdf' ? 'badge-pdf' : 'badge-jpg'}">${d.type.toUpperCase()}</div>
                  <div class="doc-summary-meta">
                    <h5>${d.name}</h5>
                    <p>${d.summary}</p>
                  </div>
                </div>
                <span class="doc-size">${d.size}</span>
              </div>
            `).join('')}
          </div>
        </div>
      </div>
    `;
  } else if (tabName === 'evidence') {
    container.innerHTML = `
      <div class="content-box">
        <div class="content-box-title">
          <span>Extracted Evidence Items</span>
          <span class="case-badge">${intel.metrics.supporting + intel.metrics.company} Items</span>
        </div>
        <div class="uploaded-docs-list">
          ${state.currentCase.documents.map(d => `
            <div class="uploaded-doc-item">
              <div class="doc-info">
                <div class="doc-icon-badge ${d.type === 'pdf' ? 'badge-pdf' : 'badge-jpg'}">${d.type.toUpperCase()}</div>
                <div>
                  <div class="doc-name">${d.name} — ${d.summary}</div>
                  <div class="doc-size">Extracted on ${d.date} • Verified Evidence Source</div>
                </div>
              </div>
              <button class="btn btn-secondary btn-sm" onclick="window.viewDocumentMock('${d.name}')">View Source</button>
            </div>
          `).join('')}
        </div>
      </div>
    `;
  } else if (tabName === 'timeline') {
    container.innerHTML = `
      <div class="content-box">
        <div class="content-box-title">
          <span>Case Timeline & Sequence of Events</span>
          <span class="case-badge">Chronological Order</span>
        </div>
        <div class="timeline-list">
          ${intel.timeline.map(t => `
            <div class="timeline-event">
              <div class="timeline-dot ${t.type}"></div>
              <div class="timeline-content">
                <div class="timeline-date">${t.date}</div>
                <div class="timeline-title">${t.title}</div>
                <div class="timeline-desc">${t.desc}</div>
              </div>
            </div>
          `).join('')}
        </div>
      </div>
    `;
  } else if (tabName === 'contradictions') {
    container.innerHTML = `
      <div class="content-box">
        <div class="content-box-title">
          <span>Detected Contradictions</span>
          <span class="case-badge" style="background:#fee2e2;color:#dc2626;">${intel.contradictions.length} Critical Conflicts</span>
        </div>
        <div class="contradictions-grid">
          ${intel.contradictions.map((c, i) => `
            <div class="contradiction-card">
              <div class="contradiction-header">
                <strong>Contradiction #${i + 1}</strong>
                <span class="contradiction-badge">${c.severity}</span>
              </div>
              <div class="contradiction-versus">
                <div class="versus-box claim">
                  <div class="versus-label">${c.companyClaim.source}</div>
                  <div class="versus-text">"${c.companyClaim.statement}"</div>
                </div>
                <div class="versus-vs-badge">VS</div>
                <div class="versus-box fact">
                  <div class="versus-label">${c.evidenceFact.source}</div>
                  <div class="versus-text">"${c.evidenceFact.statement}"</div>
                </div>
              </div>
              <p style="font-size:0.85rem; color:#475569; margin-top:12px;"><strong>AI Analysis:</strong> ${c.explanation}</p>
            </div>
          `).join('')}
        </div>
      </div>
    `;
  } else if (tabName === 'graph-tab') {
    container.innerHTML = `
      <div class="content-box" style="padding:16px;">
        <div class="flex justify-between items-center" style="margin-bottom:12px;">
          <h4 style="font-size:1rem; font-weight:700;">Mini Evidence Graph</h4>
          <button class="btn btn-primary btn-sm" onclick="window.ClaimPilot.navigateTo('graph')">Open Dedicated Graph Screen →</button>
        </div>
        <div id="mini-graph-canvas" style="position:relative; height:440px; background:#f8fafc; border:1px solid #e2e8f0; border-radius:12px; overflow:hidden;">
          <svg id="mini-svg-layer" class="graph-svg-layer"></svg>
        </div>
      </div>
    `;
    setTimeout(() => {
      renderEvidenceGraph('mini-graph-canvas', 'mini-svg-layer', 0.85);
    }, 50);
  }
}

/**
 * Visual Interactive Evidence Graph (Screen 5)
 */
export function renderEvidenceGraph(containerId = 'graph-canvas-container', svgId = 'graph-svg-layer', scale = 1) {
  const container = document.getElementById(containerId);
  const svg = document.getElementById(svgId);
  if (!container || !svg) return;

  const graphData = state.currentCase.graph;
  if (!graphData) return;

  // Clear existing rendered nodes inside container (except svg and controls)
  const existingNodes = container.querySelectorAll('.graph-node');
  existingNodes.forEach(n => n.remove());

  // Set SVG size
  svg.innerHTML = `
    <defs>
      <marker id="arrow-contradicts" viewBox="0 0 10 10" refX="28" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
        <path d="M 0 1.5 L 10 5 L 0 8.5 z" fill="#ef4444" />
      </marker>
      <marker id="arrow-supports" viewBox="0 0 10 10" refX="28" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
        <path d="M 0 1.5 L 10 5 L 0 8.5 z" fill="#10b981" />
      </marker>
      <marker id="arrow-related" viewBox="0 0 10 10" refX="28" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
        <path d="M 0 1.5 L 10 5 L 0 8.5 z" fill="#3b82f6" />
      </marker>
    </defs>
  `;

  // Place Nodes
  const nodeMap = {};
  graphData.nodes.forEach(node => {
    const nodeEl = document.createElement('div');
    nodeEl.className = `graph-node ${node.type === 'claim' ? 'node-claim' : node.type === 'report' ? 'node-report' : 'node-default'}`;
    nodeEl.id = `rendered-${node.id}`;
    nodeEl.style.left = `${node.x * scale}px`;
    nodeEl.style.top = `${node.y * scale}px`;

    let icon = '📄';
    if (node.type === 'claim') icon = '⚠️';
    if (node.type === 'report') icon = '🛡️';
    if (node.label.includes('Photo')) icon = '🖼️';

    nodeEl.innerHTML = `
      <div class="node-header">
        <span>${icon}</span>
        <span>${node.label}</span>
      </div>
      <div class="node-body">${node.text}</div>
      <div class="node-sub">Click for auditable quote & source</div>
    `;

    nodeEl.addEventListener('click', () => openNodeInspector(node));
    container.appendChild(nodeEl);
    nodeMap[node.id] = { node, el: nodeEl };
  });

  // Draw Edges
  graphData.edges.forEach(edge => {
    const fromNode = nodeMap[edge.from]?.node;
    const toNode = nodeMap[edge.to]?.node;
    if (!fromNode || !toNode) return;

    const x1 = (fromNode.x + 110) * scale;
    const y1 = (fromNode.y + 40) * scale;
    const x2 = (toNode.x + 110) * scale;
    const y2 = (toNode.y + 40) * scale;

    const color = edge.type === 'contradicts' ? '#ef4444' : edge.type === 'supports' ? '#10b981' : '#3b82f6';
    const markerId = `arrow-${edge.type}`;

    // Line path
    const path = document.createElementNS('http://www.w3.org/2000/svg', 'line');
    path.setAttribute('x1', x1);
    path.setAttribute('y1', y1);
    path.setAttribute('x2', x2);
    path.setAttribute('y2', y2);
    path.setAttribute('stroke', color);
    path.setAttribute('stroke-width', edge.type === 'contradicts' ? '3' : '2');
    if (edge.type === 'contradicts') {
      path.setAttribute('stroke-dasharray', '6,4');
    }
    path.setAttribute('marker-end', `url(#${markerId})`);
    svg.appendChild(path);

    // Label on line
    const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    text.setAttribute('x', (x1 + x2) / 2);
    text.setAttribute('y', (y1 + y2) / 2 - 6);
    text.setAttribute('fill', color);
    text.setAttribute('font-size', '10');
    text.setAttribute('font-weight', '700');
    text.setAttribute('text-anchor', 'middle');
    text.textContent = edge.relation;
    svg.appendChild(text);
  });
}

function openNodeInspector(node) {
  state.selectedNode = node;
  const inspector = document.getElementById('node-inspector-drawer');
  if (!inspector) return;

  inspector.classList.remove('hidden');
  document.getElementById('inspector-title').innerText = node.label;
  document.getElementById('inspector-text').innerText = `"${node.text}"`;
  document.getElementById('inspector-meta').innerText = `Node ID: ${node.id} • Classification: ${node.type.toUpperCase()}`;
}

export function closeNodeInspector() {
  const inspector = document.getElementById('node-inspector-drawer');
  if (inspector) inspector.classList.add('hidden');
}

/**
 * Response & Action Center (Screen 6)
 */
function renderResponseCenter() {
  const c = state.currentCase;
  const intel = c.intelligence;

  // Top summary widgets
  document.getElementById('resp-strength-score').innerText = `${intel.strengthScore} / 100`;
  document.getElementById('resp-contradictions-count').innerText = `${intel.metrics.contradictions} Contradictions`;
  document.getElementById('resp-missing-count').innerText = `${intel.metrics.missing} Missing Evidence`;

  // Recommended Action
  document.getElementById('action-rec-headline').innerText = intel.recommendedAction.headline;
  document.getElementById('action-rec-detail').innerText = intel.recommendedAction.detail;

  // Textarea
  const textarea = document.getElementById('generated-response-textarea');
  if (textarea) {
    textarea.value = intel.generatedResponse;
  }

  // Missing evidence checklist
  const missingList = document.getElementById('missing-checklist-container');
  if (missingList) {
    if (intel.missingEvidence.length === 0) {
      missingList.innerHTML = `<div style="padding:16px; background:#ecfdf5; border-radius:8px; color:#065f46; font-size:0.875rem;">✓ All critical evidence collected! No items currently missing.</div>`;
    } else {
      missingList.innerHTML = intel.missingEvidence.map(item => `
        <div class="missing-item-card">
          <div class="missing-item-header">
            <span class="missing-item-name">${item.name}</span>
            <span class="priority-tag priority-${item.priority.toLowerCase()}">${item.priority} Priority</span>
          </div>
          <div class="missing-item-desc">${item.desc}</div>
          <button class="btn btn-secondary btn-sm" onclick="window.ClaimPilot.promptUploadEvidence('${item.name}')">+ Upload This Item</button>
        </div>
      `).join('');
    }
  }
}

/**
 * Copy response to clipboard
 */
export function copyResponseToClipboard() {
  const textarea = document.getElementById('generated-response-textarea');
  if (!textarea) return;
  navigator.clipboard.writeText(textarea.value).then(() => {
    showToast("Dispute response copied to clipboard!", "success");
  }).catch(() => {
    textarea.select();
    document.execCommand('copy');
    showToast("Dispute response copied to clipboard!", "success");
  });
}

/**
 * Tone selector change
 */
export async function changeTone(tone) {
  showToast(`Regenerating letter with ${tone} tone...`);
  const res = await ClaimPilotAPI.generateResponse(state.activeCaseKey, tone);
  const textarea = document.getElementById('generated-response-textarea');
  if (textarea && res.response) {
    textarea.value = res.response;
    showToast("Response updated with selected tone.", "success");
  }
}

/**
 * Export Report Modal / PDF
 */
export function exportReport() {
  const modal = document.getElementById('export-modal');
  if (modal) modal.classList.remove('hidden');
}

export function closeExportModal() {
  const modal = document.getElementById('export-modal');
  if (modal) modal.classList.add('hidden');
}

export function downloadReportFile() {
  const c = state.currentCase;
  const content = `CLAIM PILOT AUDIT REPORT
==================================================
Case: ${c.title}
Date: ${c.createdAt}
Case Strength Score: ${c.intelligence.strengthScore} / 100

METRICS
- Supporting Evidence: ${c.intelligence.metrics.supporting}
- Company Evidence: ${c.intelligence.metrics.company}
- Contradictions Detected: ${c.intelligence.metrics.contradictions}
- Missing Items: ${c.intelligence.metrics.missing}

KEY FINDINGS
${c.intelligence.keyFindings.map(f => `* ${f.text}`).join('\n')}

CONTRADICTIONS
${c.intelligence.contradictions.map((cnt, i) => `
[Conflict #${i + 1}] (${cnt.severity})
Company Assertion: "${cnt.companyClaim.statement}" (${cnt.companyClaim.source})
Evidence Fact: "${cnt.evidenceFact.statement}" (${cnt.evidenceFact.source})
Explanation: ${cnt.explanation}
`).join('\n')}

GENERATED FORMAL DISPUTE LETTER
--------------------------------------------------
${document.getElementById('generated-response-textarea')?.value || c.intelligence.generatedResponse}
`;

  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `ClaimPilot_${c.title.replace(/\s+/g, '_')}_Report.txt`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);

  closeExportModal();
  showToast("Audit Report downloaded successfully!", "success");
}

// Window Globals for HTML onclick triggers
window.ClaimPilot = {
  navigateTo,
  loadCasePreset,
  switchDashboardTab,
  copyResponseToClipboard,
  changeTone,
  exportReport,
  closeExportModal,
  downloadReportFile,
  closeNodeInspector,
  showToast,
  promptUploadEvidence: (name) => {
    showToast(`Opening file selector for: ${name}`);
    document.getElementById('hidden-file-input')?.click();
  }
};

window.viewDocumentMock = (name) => {
  showToast(`Inspecting auditable file source: ${name}`, 'info');
};

/**
 * Event Listeners Initializer
 */
document.addEventListener('DOMContentLoaded', () => {
  if (window.__CLAIMPILOT_REACT_APP__) return;

  // Nav items click handler
  DOM.sidebarNavs.forEach(nav => {
    nav.addEventListener('click', (e) => {
      e.preventDefault();
      const target = nav.dataset.target;
      navigateTo(target);
    });
  });

  // Drag and Drop Zone
  const dropzone = document.getElementById('case-dropzone');
  const fileInput = document.getElementById('hidden-file-input');

  if (dropzone && fileInput) {
    dropzone.addEventListener('click', () => fileInput.click());

    ['dragenter', 'dragover'].forEach(eventName => {
      dropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        dropzone.classList.add('dragover');
      });
    });

    ['dragleave', 'drop'].forEach(eventName => {
      dropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        dropzone.classList.remove('dragover');
      });
    });

    dropzone.addEventListener('drop', (e) => {
      const files = Array.from(e.dataTransfer.files);
      if (files.length > 0) handleFilesAdded(files);
    });

    fileInput.addEventListener('change', (e) => {
      const files = Array.from(e.target.files);
      if (files.length > 0) handleFilesAdded(files);
    });
  }

  function handleFilesAdded(files) {
    files.forEach(file => {
      const sizeMB = (file.size / (1024 * 1024)).toFixed(1) + ' MB';
      const ext = file.name.split('.').pop().toUpperCase();
      state.uploadedFiles.push({
        name: file.name,
        size: sizeMB,
        type: ext === 'PDF' ? 'badge-pdf' : 'badge-jpg',
        ext: ext
      });
    });
    renderUploadedFiles();
    showToast(`Added ${files.length} document(s) successfully.`, 'success');
  }

  // Character counter
  const descInput = document.getElementById('case-desc-input');
  const charCounter = document.getElementById('char-count');
  if (descInput && charCounter) {
    descInput.addEventListener('input', () => {
      charCounter.innerText = `${descInput.value.length}/500`;
    });
  }

  // Initialize uploaded docs
  renderUploadedFiles();

  // Listen for browser back/forward hash changes
  window.addEventListener('hashchange', () => {
    const hash = window.location.hash.replace('#/', '').replace('#', '');
    if (['landing', 'create-case', 'investigation', 'dashboard', 'graph', 'response'].includes(hash)) {
      navigateTo(hash);
    } else if (!hash) {
      navigateTo('landing');
    }
  });

  // Check initial hash
  const initialHash = window.location.hash.replace('#/', '').replace('#', '');
  if (['create-case', 'investigation', 'dashboard', 'graph', 'response'].includes(initialHash)) {
    navigateTo(initialHash);
  }
});
