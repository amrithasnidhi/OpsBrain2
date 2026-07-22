import { useEffect, useState, useRef, useCallback } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import type { Conflict } from '../types/schemas';
import { AlertTriangle, X, GitBranch, Database, Network, RefreshCw } from 'lucide-react';

interface GraphNode { id: string; label: string; color: string; group: string; x?: number; y?: number; }
interface GraphLink { source: string | GraphNode; target: string | GraphNode; color: string; label: string; }
interface GraphData { nodes: GraphNode[]; links: GraphLink[]; }

export default function GraphView() {
  const [graphData, setGraphData]       = useState<GraphData>({ nodes: [], links: [] });
  const [conflicts, setConflicts]       = useState<Conflict[]>([]);
  const [selectedConflict, setSelectedConflict] = useState<Conflict | null>(null);
  const [loading, setLoading]           = useState(true);
  const [dims, setDims]                 = useState({ w: 800, h: 600 });
  const containerRef = useRef<HTMLDivElement>(null);

  /* ── Measure container ── */
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const ro = new ResizeObserver(entries => {
      for (const e of entries) {
        setDims({ w: Math.floor(e.contentRect.width), h: Math.floor(e.contentRect.height) });
      }
    });
    ro.observe(el);
    setDims({ w: el.clientWidth, h: el.clientHeight });
    return () => ro.disconnect();
  }, []);

  /* ── Load data ── */
  const load = useCallback(() => {
    setLoading(true);
    Promise.all([
      fetch('http://localhost:8000/api/graph').then(r => r.json()).catch(() => ({ nodes: [], links: [] })),
      fetch('http://localhost:8000/api/conflicts').then(r => r.json()).catch(() => []),
    ]).then(([g, c]) => {
      setGraphData(g);
      setConflicts(c);
      setLoading(false);
    });
  }, []);
  useEffect(() => { load(); }, [load]);

  /* ── Click conflict edge ── */
  const handleLinkClick = useCallback((link: GraphLink) => {
    if (link.color === '#ef4444' || link.color === '#ff4757') {
      const srcId = typeof link.source === 'object' ? link.source.id : link.source;
      const tgtId = typeof link.target === 'object' ? link.target.id : link.target;
      const match = conflicts.find(c => c.entity === srcId || c.entity === tgtId);
      setSelectedConflict(match ?? {
        entity: `${srcId} ↔ ${tgtId}`, parameter: 'Unknown',
        source_a: { doc_id: srcId, source_file: srcId, excerpt: '' },
        source_b: { doc_id: tgtId, source_file: tgtId, excerpt: '' },
        value_a: '—', value_b: '—',
        explanation: `A conflict edge was detected between ${srcId} and ${tgtId}.`,
        severity: 'medium', risk_type: 'direct_contradiction',
      });
    }
  }, [conflicts]);

  /* ── Custom node painter ── */
  const paintNode = useCallback((node: GraphNode, ctx: CanvasRenderingContext2D, scale: number) => {
    const isEquip = node.group === 'equipment';
    const r = isEquip ? 7 : 5;
    const fill = isEquip ? '#00e676' : '#3d9eff';

    ctx.shadowBlur = isEquip ? 18 : 10;
    ctx.shadowColor = fill;
    ctx.beginPath();
    ctx.arc(node.x ?? 0, node.y ?? 0, r, 0, Math.PI * 2);
    ctx.fillStyle = fill;
    ctx.fill();
    ctx.shadowBlur = 0;

    if (scale >= 1.0) {
      const label = node.label || node.id;
      ctx.font = `${Math.max(10, Math.round(11 / scale))}px Outfit, sans-serif`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'top';
      ctx.fillStyle = 'rgba(200,215,255,0.75)';
      ctx.fillText(label, node.x ?? 0, (node.y ?? 0) + r + 3);
    }
  }, []);

  /* ── Empty state ── */
  const isEmpty = !loading && graphData.nodes.length === 0;

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%', background: 'var(--bg-base)', overflow: 'hidden' }}>

      {/* ── Graph canvas ── */}
      <div ref={containerRef} style={{ width: '100%', height: '100%' }}>
        {!loading && !isEmpty && dims.w > 0 && dims.h > 0 && (
          <ForceGraph2D
            width={dims.w}
            height={dims.h}
            graphData={graphData}
            nodeLabel="label"
            linkColor={(link: GraphLink) => (link.color === '#ef4444' || link.color === '#ff4757') ? '#ff4757' : 'rgba(255,255,255,0.1)'}
            linkWidth={(link: GraphLink) => (link.color === '#ef4444' || link.color === '#ff4757') ? 2.5 : 1}
            onLinkClick={handleLinkClick}
            nodeCanvasObject={paintNode}
            nodeCanvasObjectMode={() => 'replace'}
            linkDirectionalArrowLength={4}
            linkDirectionalArrowRelPos={1}
            linkDirectionalParticles={(link: GraphLink) => (link.color === '#ef4444' || link.color === '#ff4757') ? 3 : 0}
            linkDirectionalParticleColor={() => '#ff4757'}
            linkDirectionalParticleWidth={2}
            backgroundColor="transparent"
            warmupTicks={80}
            cooldownTicks={200}
          />
        )}
      </div>

      {/* ── Loading overlay ── */}
      {loading && (
        <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '16px' }}>
          <div style={{ width: '56px', height: '56px', borderRadius: '50%', border: '3px solid var(--border-subtle)', borderTop: '3px solid var(--accent)', animation: 'spin 1s linear infinite' }} />
          <p style={{ color: 'var(--text-muted)', fontSize: '14px' }}>Loading knowledge graph…</p>
        </div>
      )}

      {/* ── Empty state ── */}
      {isEmpty && (
        <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '24px', padding: '40px' }}>
          <div style={{
            width: '100px', height: '100px', borderRadius: '50%',
            background: 'radial-gradient(circle at 40% 40%, rgba(0,230,118,0.12) 0%, transparent 70%)',
            border: '1px solid rgba(0,230,118,0.15)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <Network size={40} color="var(--accent)" style={{ opacity: 0.5 }} />
          </div>
          <div style={{ textAlign: 'center' }}>
            <h2 style={{ fontFamily: 'var(--font-display)', fontStyle: 'italic', fontSize: '28px', color: 'var(--text-primary)', marginBottom: '10px' }}>
              Graph is empty.
            </h2>
            <p style={{ color: 'var(--text-muted)', fontSize: '14px', maxWidth: '380px', lineHeight: 1.6 }}>
              The knowledge graph will populate after you ingest documents. Upload a PDF or SOP to see equipment nodes, relationships, and conflict edges appear here.
            </p>
          </div>
          <button onClick={load} style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '11px 24px', background: 'var(--accent-dim)', border: '1px solid rgba(0,230,118,0.25)', borderRadius: 'var(--radius-md)', color: 'var(--accent)', fontSize: '13px', fontWeight: 700, cursor: 'pointer', fontFamily: 'var(--font-body)' }}>
            <RefreshCw size={14} /> Reload Graph
          </button>
        </div>
      )}

      {/* ── Legend ── */}
      {!isEmpty && !loading && (
        <div style={{
          position: 'absolute', top: '20px', left: '20px',
          background: 'rgba(8,12,24,0.88)', border: '1px solid var(--border-default)',
          borderRadius: 'var(--radius-lg)', padding: '16px 20px',
          backdropFilter: 'blur(16px)', pointerEvents: 'none', minWidth: '180px',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px', paddingBottom: '12px', borderBottom: '1px solid var(--border-subtle)' }}>
            <GitBranch size={14} color="var(--accent)" />
            <span style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-primary)' }}>Knowledge Graph</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {[
              { type: 'dot', color: '#00e676', label: 'Equipment' },
              { type: 'dot', color: '#3d9eff', label: 'Documents' },
              { type: 'line', color: '#ff4757', label: 'Conflict (click)' },
              { type: 'line', color: 'rgba(255,255,255,0.18)', label: 'Relationship' },
            ].map(({ type, color, label }) => (
              <div key={label} style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                {type === 'dot'
                  ? <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: color, boxShadow: `0 0 8px ${color}`, flexShrink: 0 }} />
                  : <div style={{ width: '18px', height: '2px', background: color, borderRadius: '999px', flexShrink: 0 }} />
                }
                <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>{label}</span>
              </div>
            ))}
          </div>
          <div style={{ marginTop: '14px', paddingTop: '12px', borderTop: '1px solid var(--border-subtle)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Nodes</span>
              <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--accent)', fontFamily: 'monospace' }}>{graphData.nodes.length}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Edges</span>
              <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--accent)', fontFamily: 'monospace' }}>{graphData.links.length}</span>
            </div>
          </div>
        </div>
      )}

      {/* ── Stats pill (top-right) ── */}
      {!isEmpty && !loading && (
        <div style={{ position: 'absolute', top: '20px', right: '20px', display: 'flex', gap: '8px' }}>
          <div style={{ background: 'rgba(8,12,24,0.85)', border: '1px solid var(--border-default)', borderRadius: '999px', padding: '7px 14px', backdropFilter: 'blur(12px)', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Database size={12} color="var(--text-muted)" />
            <span style={{ fontSize: '12px', color: 'var(--text-secondary)', fontFamily: 'monospace' }}>{conflicts.length} conflicts</span>
          </div>
          <button onClick={load} style={{ background: 'rgba(8,12,24,0.85)', border: '1px solid var(--border-default)', borderRadius: '999px', padding: '7px 14px', backdropFilter: 'blur(12px)', display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer', color: 'var(--text-secondary)', fontSize: '12px', fontFamily: 'var(--font-body)' }}>
            <RefreshCw size={11} /> Reload
          </button>
        </div>
      )}

      {/* ── Conflict detail modal ── */}
      {selectedConflict && (
        <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'rgba(8,12,24,0.65)', backdropFilter: 'blur(6px)', zIndex: 50, padding: '24px' }}>
          <div className="animate-fade-in-up" style={{
            width: '100%', maxWidth: '520px',
            background: 'var(--bg-card)', border: '1px solid var(--border-default)',
            borderRadius: 'var(--radius-xl)', boxShadow: '0 0 40px rgba(255,71,87,0.2)', overflow: 'hidden',
          }}>
            {/* Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '18px 22px', borderBottom: '1px solid var(--border-subtle)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <div style={{ width: '32px', height: '32px', borderRadius: '8px', background: 'var(--danger-dim)', border: '1px solid rgba(255,71,87,0.25)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <AlertTriangle size={16} color="var(--danger)" />
                </div>
                <div>
                  <p style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-primary)' }}>Conflict Detail</p>
                  <p style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '1px' }}>Click anywhere outside to close</p>
                </div>
              </div>
              <button onClick={() => setSelectedConflict(null)} style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)', borderRadius: '8px', width: '32px', height: '32px', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
                <X size={16} />
              </button>
            </div>

            {/* Body */}
            <div style={{ padding: '22px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                {[
                  { label: 'Entity', val: selectedConflict.entity, color: 'var(--accent)' },
                  { label: 'Parameter', val: selectedConflict.parameter, color: 'var(--warning)' },
                ].map(({ label, val, color }) => (
                  <div key={label} style={{ padding: '12px 14px', background: 'var(--bg-surface)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                    <p style={{ fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: '5px' }}>{label}</p>
                    <p style={{ fontFamily: 'monospace', fontSize: '14px', fontWeight: 700, color }}>{val}</p>
                  </div>
                ))}
              </div>

              <div style={{ padding: '14px', background: 'var(--bg-surface)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                <p style={{ fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: '8px' }}>Explanation</p>
                <p style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: 1.6 }}>{selectedConflict.explanation}</p>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                {[
                  { label: 'Value A', val: selectedConflict.value_a, color: 'var(--danger)' },
                  { label: 'Value B', val: selectedConflict.value_b, color: 'var(--warning)' },
                ].map(({ label, val, color }) => (
                  <div key={label} style={{ padding: '12px 14px', background: 'var(--bg-surface)', borderRadius: 'var(--radius-md)', borderLeft: `3px solid ${color}` }}>
                    <p style={{ fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: '5px' }}>{label}</p>
                    <p style={{ fontFamily: 'monospace', fontSize: '18px', fontWeight: 700, color }}>{val}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* click-outside to close modal */}
      {selectedConflict && (
        <div onClick={() => setSelectedConflict(null)} style={{ position: 'absolute', inset: 0, zIndex: 40 }} />
      )}
    </div>
  );
}
