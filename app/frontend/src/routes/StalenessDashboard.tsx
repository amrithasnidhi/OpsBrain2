import { useEffect, useState } from 'react';
import type { StalenessRow } from '../types/schemas';
import { Clock, CheckCircle2, AlertTriangle, RefreshCw } from 'lucide-react';

const STATUS_CFG = {
  ok:      { color: 'var(--accent)',   bg: 'var(--accent-dim)',   Icon: CheckCircle2,  label: 'HEALTHY' },
  warning: { color: 'var(--warning)',  bg: 'var(--warning-dim)',  Icon: Clock,         label: 'WARNING' },
  overdue: { color: 'var(--danger)',   bg: 'var(--danger-dim)',   Icon: AlertTriangle, label: 'OVERDUE' },
};

export default function StalenessDashboard() {
  const [rows, setRows] = useState<StalenessRow[]>([]);
  const [loading, setLoading] = useState(true);

  const load = () => {
    setLoading(true);
    fetch('http://localhost:8000/api/staleness')
      .then(r => r.json()).then(d => { setRows(d); setLoading(false); })
      .catch(() => setLoading(false));
  };
  useEffect(() => { load(); }, []);

  const overdue = rows.filter(r => r.status === 'overdue').length;
  const warning = rows.filter(r => r.status === 'warning').length;
  const ok      = rows.filter(r => r.status === 'ok').length;

  return (
    <div style={{ height: '100%', overflowY: 'auto', background: 'var(--bg-base)' }}>
      {/* ── Header bar ── */}
      <div style={{
        padding: '32px 48px 28px',
        background: 'linear-gradient(180deg, var(--bg-surface) 0%, var(--bg-base) 100%)',
        borderBottom: '1px solid var(--border-subtle)',
        display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end',
      }}>
        <div>
          <p style={{ fontSize: '11px', fontWeight: 700, letterSpacing: '0.14em', textTransform: 'uppercase', color: 'var(--accent)', marginBottom: '8px' }}>
            Maintenance Intelligence
          </p>
          <h1 style={{ fontFamily: 'var(--font-display)', fontStyle: 'italic', fontSize: '42px', fontWeight: 700, color: 'var(--text-primary)', lineHeight: 1.0, marginBottom: '8px' }}>
            Maintenance Health.
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '14px' }}>Real-time staleness detection across all tracked equipment</p>
        </div>
        <button onClick={load} disabled={loading} style={{
          display: 'flex', alignItems: 'center', gap: '7px', padding: '10px 20px',
          borderRadius: 'var(--radius-md)', background: 'var(--bg-card)', border: '1px solid var(--border-default)',
          color: 'var(--text-secondary)', fontSize: '13px', fontWeight: 500, cursor: 'pointer', fontFamily: 'var(--font-body)',
        }}>
          <RefreshCw size={14} style={{ animation: loading ? 'spin 1s linear infinite' : 'none' }} /> Refresh
        </button>
      </div>

      <div style={{ padding: '32px 48px' }}>
        {/* KPI row */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px', marginBottom: '32px' }}>
          {[
            { label: 'Overdue', count: overdue, cfg: STATUS_CFG.overdue },
            { label: 'Warning', count: warning, cfg: STATUS_CFG.warning },
            { label: 'Healthy', count: ok,      cfg: STATUS_CFG.ok      },
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

        {/* Table */}
        <div style={{ background: 'var(--bg-card)', borderRadius: 'var(--radius-xl)', border: '1px solid var(--border-subtle)', overflow: 'hidden' }}>
          <div style={{ padding: '18px 24px', borderBottom: '1px solid var(--border-subtle)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <p style={{ fontWeight: 700, fontSize: '14px', color: 'var(--text-primary)' }}>Equipment Registry</p>
            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{rows.length} items tracked</span>
          </div>

          {loading ? (
            <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {[1,2,3,4].map(i => <div key={i} className="skeleton" style={{ height: '56px' }} />)}
            </div>
          ) : rows.length === 0 ? (
            <div style={{ padding: '64px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '14px' }}>
              <Clock size={32} style={{ margin: '0 auto 12px', opacity: 0.3 }} />
              No maintenance data found. Ingest documents to populate.
            </div>
          ) : (
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-subtle)', background: 'var(--bg-surface)' }}>
                  {['Equipment', 'Required Interval', 'Last Inspection', 'Days Overdue', 'Status'].map(h => (
                    <th key={h} style={{ padding: '12px 24px', textAlign: 'left', fontSize: '11px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.07em' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {rows.map((row, idx) => {
                  const cfg = STATUS_CFG[row.status as keyof typeof STATUS_CFG] || STATUS_CFG.ok;
                  const Icon = cfg.Icon;
                  return (
                    <tr key={idx}
                      style={{ borderBottom: idx < rows.length - 1 ? '1px solid var(--border-subtle)' : 'none', transition: 'background 0.15s' }}
                      onMouseEnter={e => (e.currentTarget.style.background = 'var(--bg-card-hover)')}
                      onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
                    >
                      <td style={{ padding: '16px 24px' }}>
                        <span style={{ fontFamily: 'monospace', fontSize: '13px', fontWeight: 700, color: 'var(--text-primary)', background: 'var(--bg-surface)', padding: '4px 10px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>{row.equipment_tag}</span>
                      </td>
                      <td style={{ padding: '16px 24px', fontSize: '13px', color: 'var(--text-secondary)' }}>{row.required_interval}</td>
                      <td style={{ padding: '16px 24px', fontSize: '13px', color: 'var(--text-muted)', fontFamily: 'monospace' }}>{String(row.last_inspection_date) || '—'}</td>
                      <td style={{ padding: '16px 24px', fontSize: '14px', fontWeight: 700, color: row.days_overdue > 0 ? cfg.color : 'var(--text-muted)' }}>
                        {row.days_overdue > 0 ? `+${row.days_overdue}d` : '—'}
                      </td>
                      <td style={{ padding: '16px 24px' }}>
                        <span style={{ display: 'inline-flex', alignItems: 'center', gap: '5px', fontSize: '11px', fontWeight: 700, letterSpacing: '0.06em', color: cfg.color, background: cfg.bg, border: `1px solid ${cfg.color}30`, padding: '4px 10px', borderRadius: '999px' }}>
                          <Icon size={11} />{cfg.label}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}
