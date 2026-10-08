import React from 'react';

/**
 * Timeline Component
 * Chronological sequence of events from purchase, defect, diagnostic report to rejection.
 */
export default function Timeline({ timeline = [] }) {
  if (!timeline || timeline.length === 0) {
    return (
      <div className="content-box">
        <div style={{ padding: '24px', textAlign: 'center', color: '#64748b' }}>
          No timeline events recorded for this case.
        </div>
      </div>
    );
  }

  return (
    <div className="content-box">
      <div className="content-box-title">
        <span>Case Timeline & Chronology</span>
        <span className="case-badge">Sequential Chain of Evidence</span>
      </div>

      <div className="timeline-list">
        {timeline.map((event, idx) => (
          <div key={idx} className="timeline-event">
            <div className={`timeline-dot ${event.type || 'neutral'}`} />
            <div className="timeline-content">
              <div className="timeline-date">{event.date}</div>
              <div className="timeline-title">{event.title}</div>
              <div className="timeline-desc">{event.desc}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
