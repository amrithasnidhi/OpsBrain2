import React from 'react';
import type { Incident } from '../types/schemas';
import { ShieldAlert } from 'lucide-react';

interface Props { incidents: Incident[]; }

export const LessonsLearned: React.FC<Props> = ({ incidents }) => {
  if (!incidents || incidents.length === 0) return null;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '4px' }}>
      {incidents.map((inc, idx) => (
        <div key={idx} style={{
          display: 'flex', alignItems: 'flex-start', gap: '10px',
          padding: '12px 14px', borderRadius: 'var(--radius-md)',
          background: 'var(--danger-dim)', border: '1px solid rgba(255,71,87,0.2)',
          borderLeft: '3px solid var(--danger)',
        }}>
          <ShieldAlert size={16} color="var(--danger)" style={{ flexShrink: 0, marginTop: '2px' }} />
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
              <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--danger)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                Past Incident
              </span>
              <span style={{
                fontFamily: 'monospace', fontSize: '11px', color: 'var(--danger)', opacity: 0.8,
                background: 'rgba(255,71,87,0.15)', padding: '1px 6px', borderRadius: '4px',
              }}>
                {inc.equipment_tag}
              </span>
            </div>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: 1.5 }}>{inc.description}</p>
            <div style={{ display: 'flex', gap: '14px', marginTop: '6px' }}>
              {inc.date && <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Date: {inc.date}</span>}
              <span style={{ fontSize: '11px', color: 'var(--danger)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                {inc.severity} severity
              </span>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};
