import { useEffect, useState } from 'react';
import type { ComplianceGap } from '../types/schemas';
import { Shield, AlertTriangle, CheckCircle2, HelpCircle, RefreshCw } from 'lucide-react';

export default function CompliancePanel() {
  const [gaps, setGaps] = useState<ComplianceGap[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = () => {
    setLoading(true); setError(null);
    fetch('http://localhost:8000/api/compliance')
      .then(r => { if (!r.ok) throw new Error('Failed to fetch'); return r.json(); })
      .then(d => { setGaps(d); setLoading(false); })
      .catch(e => { setError(e.message); setLoading(false); });
  };
  useEffect(() => { load(); }, []);

  const gapCount  = gaps.filter(g => g.status === 'gap').length;
  const compliant = gaps.filter(g => g.status === 'compliant').length;
  const unknown   = gaps.filter(g => g.status === 'unknown').length;

  const grouped = gaps.reduce((acc, g) => {
    if (!acc[g.standard]) acc[g.standard] = [];
    acc[g.standard].push(g);
    return acc;
  }, {} as Record<string, ComplianceGap[]>);

  const statusCfg = (status: string) => {
    if (status === 'compliant') return { color: 'var(--accent)',     bg: 'var(--accent-dim)',  Icon: CheckCircle2,  label: 'COMPLIANT' };
    if (status === 'gap')       return { color: 'var(--danger)',     bg: 'var(--danger-dim)',  Icon: AlertTriangle, label: 'GAP'       };
    return                             { color: 'var(--text-muted)', bg: 'var(--bg-surface)',  Icon: HelpCircle,    label: 'UNKNOWN'   };
  };

  return (
    <div style={{ height: '100%', overflowY: 'auto', background: 'var(--bg-base)' }}>
      {/* ── Header ── */}
      <div style={{
        padding: '32px 48px 28px',
        background: 'linear-gradient(180deg, var(--bg-surface) 0%, var(--bg-base) 100%)',
        borderBottom: '1px solid var(--border-subtle)',
        display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end',
      }}>
        <div>
          <p style={{ fontSize: '11px', fontWeight: 700, letterSpacing: '0.14em', textTransform: 'uppercase', color: 'var(--accent)', marginBottom: '8px' }}>
            Regulatory Intelligence
          </p>
          <h1 style={{ fontFamily: 'var(--font-display)', fontStyle: 'italic', fontSize: '42px', fontWeight: 700, color: 'var(--text-primary)', lineHeight: 1.0, marginBottom: '8px' }}>
            Compliance Status.
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '14px' }}>Real-time gap detection against industry standards</p>
        </div>
        <button onClick={load} disabled={loading} style={{ display: 'flex', alignItems: 'center', gap: '7px', padding: '10px 20px', borderRadius: 'var(--radius-md)', background: 'var(--bg-card)', border: '1px solid var(--border-default)', color: 'var(--text-secondary)', fontSize: '13px', fontWeight: 500, cursor: 'pointer', fontFamily: 'var(--font-body)' }}>
          <RefreshCw size={14} style={{ animation: loading ? 'spin 1s linear infinite' : 'none' }} /> Refresh
        </button>
      </div>

      <div style={{ padding: '32px 48px' }}>
        {/* KPI row */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px', marginBottom: '32px' }}>
          {[
            { label: 'Gaps Found', count: gapCount, cfg: statusCfg('gap') },
            { label: 'Compliant',  count: compliant, cfg: statusCfg('compliant') },
            { label: 'Unknown',    count: unknown,   cfg: statusCfg('unknown') },
          ].map(({ label, count, cfg }) => {
            const Icon = cfg.Icon;
            return (
              <div key={label} style={{ padding: '24px 28px', borderRadius: 'var(--radius-xl)', background: cfg.bg, border: `1px solid ${cfg.color}22` }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                  <Icon size={18} color={cfg.color} />
                  <span style={{ fontSize: '12px', fontWeight: 700, color: cfg.color, textTransform: 'uppercase', letterSpacing: '0.08em' }}>{label}</span>
                </div>
                <p style={{ fontFamily: 'var(--font-display)', fontSize: '52px', fontWeight: 700, color: cfg.color, lineHeight: 1 }}>{count}</p>
              </div>
            );
          })}
        </div>

        {/* Error */}
        {error && (
          <div style={{ padding: '14px 16px', background: 'var(--danger-dim)', border: '1px solid rgba(255,71,87,0.25)', borderRadius: 'var(--radius-md)', marginBottom: '24px', color: 'var(--danger)', fontSize: '13px', display: 'flex', gap: '8px' }}>
            <AlertTriangle size={16} style={{ flexShrink: 0 }} /> {error}
          </div>
        )}

        {/* Standards */}
        {loading ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {[1,2,3].map(i => <div key={i} className="skeleton" style={{ height: '140px' }} />)}
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(480px, 1fr))', gap: '16px' }}>
            {Object.entries(grouped).map(([standard, items]) => (
              <div key={standard} style={{ background: 'var(--bg-card)', borderRadius: 'var(--radius-xl)', border: '1px solid var(--border-subtle)', overflow: 'hidden' }}>
                <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border-subtle)', display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <Shield size={15} color="var(--text-muted)" />
                  <span style={{ fontWeight: 700, fontSize: '14px', color: 'var(--text-primary)', flex: 1 }}>{standard}</span>
                  <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{items.length} item{items.length !== 1 ? 's' : ''}</span>
                </div>
                {items.map((gap, idx) => {
                  const cfg = statusCfg(gap.status);
                  const Icon = cfg.Icon;
                  return (
                    <div key={idx} style={{
                      padding: '14px 20px', display: 'flex', alignItems: 'flex-start', gap: '12px',
                      borderBottom: idx < items.length - 1 ? '1px solid var(--border-subtle)' : 'none',
                      background: gap.status === 'gap' ? 'rgba(255,71,87,0.03)' : 'transparent',
                    }}>
                      <Icon size={16} color={cfg.color} style={{ flexShrink: 0, marginTop: '2px' }} />
                      <div style={{ flex: 1 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '5px', flexWrap: 'wrap' }}>
                          <span style={{ fontFamily: 'monospace', fontSize: '12px', fontWeight: 700, color: 'var(--text-primary)', background: 'var(--bg-surface)', padding: '2px 8px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>{gap.equipment_tag}</span>
                          <span style={{ fontSize: '10px', fontWeight: 700, letterSpacing: '0.06em', color: cfg.color, background: cfg.bg, padding: '2px 8px', borderRadius: '999px', border: `1px solid ${cfg.color}30` }}>{cfg.label}</span>
                        </div>
                        <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '3px' }}>{gap.requirement}</p>
                        <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{gap.details}</p>
                      </div>
                    </div>
                  );
                })}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
