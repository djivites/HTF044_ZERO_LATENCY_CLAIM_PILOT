import React from 'react';

/**
 * Home Component (Landing Page)
 */
export default function Home({ onGetStarted, onDemoCase }) {
  return (
    <div className="landing-view page-transition">
      {/* Landing Header */}
      <header className="landing-header">
        <div className="sidebar-brand">
          <div className="brand-icon">🧠</div>
          <span className="brand-title" style={{ color: '#0f172a' }}>ClaimPilot</span>
        </div>
        <nav className="landing-nav-links">
          <a href="#home">Home</a>
          <a href="#how-it-works" onClick={() => onGetStarted('create-case')}>How it works</a>
          <a href="#use-cases">Use Cases</a>
          <a href="#demo" onClick={() => onDemoCase('laptop')}>Demo Case</a>
        </nav>
        <div>
          <button className="btn btn-primary" onClick={() => onGetStarted('create-case')}>
            Get Started
          </button>
        </div>
      </header>

      <main>
        {/* Hero Section */}
        <section className="hero-section">
          <div className="hero-content">
            <h1>
              Turn messy evidence into an <br />
              <span className="gradient-text">auditable case.</span>
            </h1>
            <p className="hero-subtitle">
              Upload your documents. Let AI investigate. See the evidence, contradictions and your case strength in real time.
            </p>
            <div className="hero-actions">
              <button className="btn btn-primary btn-lg" onClick={() => onGetStarted('create-case')}>
                Analyze My Case →
              </button>
              <button className="btn btn-secondary" onClick={() => onDemoCase('laptop')}>
                Explore Live Demo
              </button>
            </div>
            <div className="hero-stats-row">
              <div className="stat-pill">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <polyline points="20 6 9 17 4 12" />
                </svg>
                Evidence Graph Extraction
              </div>
              <div className="stat-pill">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <polyline points="20 6 9 17 4 12" />
                </svg>
                Contradiction Discovery
              </div>
              <div className="stat-pill">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <polyline points="20 6 9 17 4 12" />
                </svg>
                Auditable Dispute Output
              </div>
            </div>
          </div>

          {/* Visual Hero Graphic */}
          <div className="hero-visual-card">
            <img
              src="/hero-graph.png"
              alt="ClaimPilot evidence graph and contradictions overview"
              className="hero-graph-image"
            />
          </div>
        </section>

        {/* Use Cases Section */}
        <section id="use-cases" className="use-cases-section">
          <div className="section-label">Tailored For Dispute Resolution</div>
          <h2 className="section-title">Common Use Cases</h2>
          <div className="use-cases-grid">
            <div className="use-case-card" onClick={() => onDemoCase('laptop')}>
              <div className="use-case-icon" style={{ background: '#eef2ff', color: '#4f46e5' }}>💻</div>
              <h3>Warranty Claims</h3>
              <p>Electronics, appliances, vehicles, and denied manufacturer warranties.</p>
            </div>
            <div className="use-case-card" onClick={() => onGetStarted('create-case')}>
              <div className="use-case-icon" style={{ background: '#ecfdf5', color: '#059669' }}>🏥</div>
              <h3>Insurance Claims</h3>
              <p>Health, vehicle, home repair rejections and out-of-network chargebacks.</p>
            </div>
            <div className="use-case-card" onClick={() => onDemoCase('rental')}>
              <div className="use-case-icon" style={{ background: '#fffbeb', color: '#d97706' }}>🏠</div>
              <h3>Rental Disputes</h3>
              <p>Unlawful security deposit withholdings, damage allegations, and wear-and-tear.</p>
            </div>
            <div className="use-case-card" onClick={() => onGetStarted('create-case')}>
              <div className="use-case-icon" style={{ background: '#fef2f2', color: '#dc2626' }}>🔨</div>
              <h3>Contractor Disputes</h3>
              <p>Incomplete scopes of work, unlicensed billing, delays, and defective repairs.</p>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
