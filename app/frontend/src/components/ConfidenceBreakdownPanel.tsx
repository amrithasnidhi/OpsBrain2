import React from 'react';
import type { ConfidenceBreakdown } from '../types/schemas';
import { CheckCircle2, AlertTriangle } from 'lucide-react';

interface Props { breakdown: ConfidenceBreakdown; }

export const ConfidenceBreakdownPanel: React.FC<Props> = ({ breakdown }) => {
  if (breakdown.reasons.length === 0 && breakdown.warnings.length === 0) return null;

  return (
    <div style={{
      display: 'flex', flexDirection: 'column', gap: '5px',
      padding: '10px 12px', borderRadius: 'var(--radius-sm)',
      background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)',
    }}>
      <p style={{ fontSize: '10px', fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '4px' }}>
        Confidence Breakdown
      </p>
      {breakdown.reasons.map((reason, i) => (
        <div key={`r-${i}`} style={{ display: 'flex', alignItems: 'flex-start', gap: '7px' }}>
          <CheckCircle2 size={12} color="var(--accent)" style={{ flexShrink: 0, marginTop: '2px' }} />
          <span style={{ fontSize: '12px', color: 'var(--text-secondary)', lineHeight: 1.5 }}>{reason}</span>
        </div>
      ))}
      {breakdown.warnings.map((warning, i) => (
        <div key={`w-${i}`} style={{ display: 'flex', alignItems: 'flex-start', gap: '7px' }}>
          <AlertTriangle size={12} color="var(--warning)" style={{ flexShrink: 0, marginTop: '2px' }} />
          <span style={{ fontSize: '12px', color: 'var(--text-secondary)', lineHeight: 1.5 }}>{warning}</span>
        </div>
      ))}
    </div>
  );
};
