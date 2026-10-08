import React from 'react';

/**
 * CaseScore Component
 * Displays the case strength gauge and key intelligence metrics.
 */
export default function CaseScore({ score = 82, metrics = { supporting: 7, company: 2, contradictions: 3, missing: 1 } }) {
  const radius = 26;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (score / 100) * circumference;

  return (
    <div className="metrics-row">
      {/* Radial Strength Gauge Card */}
      <div className="metric-card metric-card-strength">
        <div className="gauge-circle">
          <svg className="gauge-svg">
            <circle className="gauge-bg" cx="32" cy="32" r={radius} />
            <circle
              className="gauge-progress"
              cx="32"
              cy="32"
              r={radius}
              style={{
                strokeDasharray: circumference,
                strokeDashoffset: strokeDashoffset
              }}
            />
          </svg>
          <div className="gauge-text">
            <div className="gauge-number">{score}</div>
            <div className="gauge-denom">/ 100</div>
          </div>
        </div>
        <div className="metric-info">
          <span className="metric-label">Case Strength</span>
          <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#10b981' }}>
            {score >= 75 ? 'High Viability' : score >= 50 ? 'Moderate Leverage' : 'Needs Evidence'}
          </span>
        </div>
      </div>

      {/* Supporting Evidence Card */}
      <div className="metric-card">
        <div className="metric-info">
          <span className="metric-label">Supporting</span>
          <span className="metric-value val-supporting">{metrics.supporting}</span>
          <span style={{ fontSize: '0.75rem', color: '#64748b' }}>Evidence items</span>
        </div>
        <span style={{ fontSize: '1.6rem' }}>🛡️</span>
      </div>

      {/* Company Evidence Card */}
      <div className="metric-card">
        <div className="metric-info">
          <span className="metric-label">Company</span>
          <span className="metric-value val-company">{metrics.company}</span>
          <span style={{ fontSize: '0.75rem', color: '#64748b' }}>Defense points</span>
        </div>
        <span style={{ fontSize: '1.6rem' }}>🏢</span>
      </div>

      {/* Contradictions Card */}
      <div className="metric-card" style={{ borderLeft: '4px solid #f59e0b' }}>
        <div className="metric-info">
          <span className="metric-label">Contradictions</span>
          <span className="metric-value val-contradictions">{metrics.contradictions}</span>
          <span style={{ fontSize: '0.75rem', color: '#b45309' }}>Conflicts detected</span>
        </div>
        <span style={{ fontSize: '1.6rem' }}>⚠️</span>
      </div>

      {/* Missing Evidence Card */}
      <div className="metric-card" style={{ borderLeft: '4px solid #ea580c' }}>
        <div className="metric-info">
          <span className="metric-label">Missing</span>
          <span className="metric-value val-missing">{metrics.missing}</span>
          <span style={{ fontSize: '0.75rem', color: '#c2410c' }}>Items needed</span>
        </div>
        <span style={{ fontSize: '1.6rem' }}>📋</span>
      </div>
    </div>
  );
}
