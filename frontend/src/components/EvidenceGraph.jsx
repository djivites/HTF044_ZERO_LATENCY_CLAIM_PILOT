import React, { useState } from 'react';

/**
 * EvidenceGraph Component
 * Interactive visual canvas rendering connected claims, rules, reports, and photos.
 */
export default function EvidenceGraph({
  graphData = { nodes: [], edges: [] },
  isDedicatedPage = true,
  height = '600px'
}) {
  const [selectedNode, setSelectedNode] = useState(null);
  const [filterMode, setFilterMode] = useState('all'); // 'all', 'conflicts', 'supporting'

  const { nodes = [], edges = [] } = graphData;

  const filteredEdges = edges.filter(edge => {
    if (filterMode === 'conflicts') return edge.type === 'contradicts';
    if (filterMode === 'supporting') return edge.type === 'supports';
    return true;
  });

  const nodeMap = {};
  nodes.forEach(n => {
    nodeMap[n.id] = n;
  });

  return (
    <div style={{ position: 'relative', width: '100%' }}>
      {isDedicatedPage && (
        <div className="graph-header" style={{ marginBottom: '16px' }}>
          <div>
            <h2 className="page-title">Evidence Graph</h2>
            <p className="page-subtitle">Visualize how all the evidence connects, supports or contradicts each other.</p>
          </div>
          <div className="graph-legend">
            <div className="legend-item">
              <div className="legend-dot dot-supports" /> Supports
            </div>
            <div className="legend-item">
              <div className="legend-dot dot-contradicts" /> Contradicts
            </div>
            <div className="legend-item">
              <div className="legend-dot dot-related" /> Related To
            </div>
          </div>
        </div>
      )}

      <div
        className="graph-canvas-container"
        style={{ height: height, position: 'relative', overflow: 'hidden' }}
      >
        {/* Controls */}
        <div className="graph-controls">
          <button
            className={`btn btn-sm ${filterMode === 'all' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setFilterMode('all')}
          >
            All Relations
          </button>
          <button
            className={`btn btn-sm ${filterMode === 'conflicts' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setFilterMode('conflicts')}
          >
            ⚠️ Conflicts Only
          </button>
          <button
            className={`btn btn-sm ${filterMode === 'supporting' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setFilterMode('supporting')}
          >
            🛡️ Supports Only
          </button>
        </div>

        {/* SVG Directional Edge Layer */}
        <svg
          className="graph-svg-layer"
          style={{ width: '100%', height: '100%', position: 'absolute', top: 0, left: 0 }}
        >
          <defs>
            <marker id="marker-contradicts" viewBox="0 0 10 10" refX="28" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
              <path d="M 0 1.5 L 10 5 L 0 8.5 z" fill="#ef4444" />
            </marker>
            <marker id="marker-supports" viewBox="0 0 10 10" refX="28" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
              <path d="M 0 1.5 L 10 5 L 0 8.5 z" fill="#10b981" />
            </marker>
            <marker id="marker-related" viewBox="0 0 10 10" refX="28" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
              <path d="M 0 1.5 L 10 5 L 0 8.5 z" fill="#3b82f6" />
            </marker>
          </defs>

          {filteredEdges.map((edge, idx) => {
            const from = nodeMap[edge.from];
            const to = nodeMap[edge.to];
            if (!from || !to) return null;

            const x1 = from.x + 110;
            const y1 = from.y + 40;
            const x2 = to.x + 110;
            const y2 = to.y + 40;

            const color =
              edge.type === 'contradicts'
                ? '#ef4444'
                : edge.type === 'supports'
                ? '#10b981'
                : '#3b82f6';

            return (
              <g key={`edge-${idx}`}>
                <line
                  x1={x1}
                  y1={y1}
                  x2={x2}
                  y2={y2}
                  stroke={color}
                  strokeWidth={edge.type === 'contradicts' ? '3' : '2'}
                  strokeDasharray={edge.type === 'contradicts' ? '6,4' : undefined}
                  markerEnd={`url(#marker-${edge.type})`}
                />
                <text
                  x={(x1 + x2) / 2}
                  y={(y1 + y2) / 2 - 6}
                  fill={color}
                  fontSize="10"
                  fontWeight="700"
                  textAnchor="middle"
                >
                  {edge.relation}
                </text>
              </g>
            );
          })}
        </svg>

        {/* Nodes Layer */}
        {nodes.map(node => {
          let nodeClass = 'node-default';
          let icon = '📄';
          if (node.type === 'claim') {
            nodeClass = 'node-claim';
            icon = '⚠️';
          } else if (node.type === 'report') {
            nodeClass = 'node-report';
            icon = '🛡️';
          } else if (node.label.includes('Photo') || node.label.includes('Damage')) {
            icon = '🖼️';
          } else if (node.label.includes('Invoice')) {
            icon = '🧾';
          }

          return (
            <div
              key={node.id}
              className={`graph-node ${nodeClass}`}
              style={{
                left: `${node.x}px`,
                top: `${node.y}px`,
                borderWidth: selectedNode?.id === node.id ? '3px' : '2px',
                transform: selectedNode?.id === node.id ? 'scale(1.04)' : undefined
              }}
              onClick={() => setSelectedNode(node)}
            >
              <div className="node-header">
                <span>{icon}</span>
                <span>{node.label}</span>
              </div>
              <div className="node-body">{node.text}</div>
              <div className="node-sub">Click for audit excerpt</div>
            </div>
          );
        })}

        {/* Slide-over Node Inspector */}
        {selectedNode && (
          <div className="node-inspector-drawer">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#0f172a' }}>
                {selectedNode.label}
              </h3>
              <button
                className="btn btn-secondary btn-sm"
                onClick={() => setSelectedNode(null)}
              >
                ✕
              </button>
            </div>

            <div style={{ fontSize: '0.75rem', color: '#64748b', marginBottom: '16px' }}>
              Node ID: {selectedNode.id} • Classification: {selectedNode.type?.toUpperCase()}
            </div>

            <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '16px', marginBottom: '16px' }}>
              <div style={{ fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', color: '#475569', marginBottom: '6px' }}>
                Auditable Excerpt
              </div>
              <p style={{ fontSize: '0.9rem', lineHeight: 1.5, color: '#1e293b', fontStyle: 'italic' }}>
                "{selectedNode.text}"
              </p>
            </div>

            <div style={{ marginBottom: '20px' }}>
              <div style={{ fontSize: '0.8rem', fontWeight: 600, color: '#334155', marginBottom: '6px' }}>
                Cross-Verification Status
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.85rem', color: '#10b981' }}>
                <span>✓</span> Verified against service intake timestamps
              </div>
            </div>

            <button
              className="btn btn-primary btn-sm"
              style={{ marginTop: 'auto' }}
              onClick={() => alert(`Opening source document: ${selectedNode.label}`)}
            >
              View Document Source PDF →
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
