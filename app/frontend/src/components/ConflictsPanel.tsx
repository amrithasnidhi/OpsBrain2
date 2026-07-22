import React, { useEffect, useState } from 'react';
import type { Conflict } from '../types/schemas';
import { ConflictCard } from './ConflictCard';
import { AlertTriangle, TrendingUp, CheckCircle2 } from 'lucide-react';

interface Props { activeConflicts: Conflict[]; }

export const ConflictsPanel: React.FC<Props> = ({ activeConflicts }) => {
  const [allConflicts, setAllConflicts] = useState<Conflict[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://localhost:8000/api/conflicts')
      .then(r => r.json())
      .then(d => { setAllConflicts(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  const high = allConflicts.filter(c => (c.risk_score || 0) >= 0.7).length;
  const medium = allConflicts.filter(c => (c.risk_score || 0) >= 0.3 && (c.risk_score || 0) < 0.7).length;
  const resolved = allConflicts.filter(c => c.resolution === 'temporal_supersession').length;

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column', background: 'var(--bg-surface)' }}>
      {/* Header */}
      <div style={{
        padding: '18px 16px 14px',
        borderBottom: '1px solid var(--border-subtle)',
        backdropFilter: 'blur(12px)',
        background: 'rgba(13,18,37,0.9)',
        position: 'sticky', top: 0, zIndex: 10,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{
              width: '28px', height: '28px', borderRadius: '7px',
              background: 'var(--danger-dim)', border: '1px solid rgba(255,71,87,0.25)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <AlertTriangle size={14} color="var(--danger)" />
            </div>
            <span style={{ fontFamily: 'var(--font-body)', fontWeight: 700, fontSize: '14px', color: 'var(--text-primary)' }}>
              Flagged Conflicts
            </span>
          </div>
          <span style={{
            background: 'var(--danger-dim)', color: 'var(--danger)',
            border: '1px solid rgba(255,71,87,0.25)',
            padding: '2px 8px', borderRadius: '999px', fontSize: '11px', fontWeight: 700,
          }}>
            {allConflicts.length}
          </span>
        </div>

        {allConflicts.length > 0 && (
          <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
            {high > 0 && (
              <span style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '11px', color: 'var(--danger)', background: 'var(--danger-dim)', padding: '2px 8px', borderRadius: '999px', border: '1px solid rgba(255,71,87,0.2)' }}>
                <TrendingUp size={10} /> {high} High
              </span>
            )}
            {medium > 0 && (
              <span style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '11px', color: 'var(--warning)', background: 'var(--warning-dim)', padding: '2px 8px', borderRadius: '999px', border: '1px solid rgba(255,165,2,0.2)' }}>
                <TrendingUp size={10} /> {medium} Medium
              </span>
            )}
            {resolved > 0 && (
              <span style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '11px', color: 'var(--accent)', background: 'var(--accent-dim)', padding: '2px 8px', borderRadius: '999px', border: '1px solid rgba(0,230,118,0.2)' }}>
                <CheckCircle2 size={10} /> {resolved} Resolved
              </span>
            )}
          </div>
        )}
      </div>

      {/* Conflict list */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '12px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
        {loading ? (
          [1,2,3].map(i => (
            <div key={i} className="skeleton" style={{ height: '160px' }} />
          ))
        ) : allConflicts.length === 0 ? (
          <div style={{ textAlign: 'center', color: 'var(--text-muted)', marginTop: '60px', fontSize: '13px' }}>
            <CheckCircle2 size={24} style={{ margin: '0 auto 10px', opacity: 0.4 }} />
            No conflicts detected
          </div>
        ) : (
          allConflicts.map((conflict, idx) => (
            <ConflictCard
              key={`${conflict.entity}-${conflict.parameter}-${idx}`}
              conflict={conflict}
              isActive={activeConflicts.some(ac => ac.entity === conflict.entity && ac.parameter === conflict.parameter)}
            />
          ))
        )}
      </div>
    </div>
  );
};
