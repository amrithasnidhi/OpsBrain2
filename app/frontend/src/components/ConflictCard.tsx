import React from 'react';
import type { Conflict } from '../types/schemas';
import { AlertTriangle, Clock, CheckCircle2, TrendingUp } from 'lucide-react';

interface Props { conflict: Conflict; isActive?: boolean; }

export const ConflictCard: React.FC<Props> = ({ conflict, isActive = false }) => {
  const score = conflict.risk_score ?? 0;
  const isResolved = conflict.resolution === 'temporal_supersession';

  const riskColor = score >= 0.7 ? 'var(--danger)' : score >= 0.3 ? 'var(--warning)' : 'var(--accent)';
  const riskBg = score >= 0.7 ? 'var(--danger-dim)' : score >= 0.3 ? 'var(--warning-dim)' : 'var(--accent-dim)';

  return (
    <div className="animate-fade-in-up" style={{
      background: isActive ? 'rgba(255,71,87,0.06)' : 'var(--bg-card)',
      border: `1px solid ${isActive ? 'rgba(255,71,87,0.35)' : isResolved ? 'rgba(0,230,118,0.2)' : 'var(--border-subtle)'}`,
      borderRadius: 'var(--radius-md)',
      padding: '14px',
      transition: 'all 0.25s ease',
      boxShadow: isActive ? 'var(--shadow-danger)' : isResolved ? 'var(--shadow-glow)' : 'none',
    }}>
      {/* Top row */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '3px' }}>
            {/* Equipment chip */}
            <span style={{
              fontSize: '10px', fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase',
              color: 'var(--text-muted)',
            }}>
              {isResolved ? 'RESOLVED · ' : isActive ? 'ACTIVE · ' : ''}{conflict.risk_type === 'decay' ? 'DECAY' : 'CONTRADICTION'}
            </span>
          </div>
          <h3 style={{ fontFamily: 'var(--font-body)', fontWeight: 700, fontSize: '15px', color: 'var(--text-primary)' }}>
            {conflict.entity}
          </h3>
          <p style={{ fontFamily: 'monospace', fontSize: '11px', color: 'var(--text-muted)', marginTop: '2px' }}>
            {conflict.parameter}
          </p>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '4px' }}>
          {isResolved ? (
            <span style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '10px', fontWeight: 700, color: 'var(--accent)', background: 'var(--accent-dim)', padding: '2px 7px', borderRadius: '999px', border: '1px solid rgba(0,230,118,0.2)' }}>
              <CheckCircle2 size={10} /> RESOLVED
            </span>
          ) : (
            <span style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '10px', fontWeight: 700, color: riskColor, background: riskBg, padding: '2px 7px', borderRadius: '999px', border: `1px solid ${riskColor}30` }}>
              {conflict.risk_type === 'decay' ? <Clock size={10} /> : <AlertTriangle size={10} />}
              {conflict.risk_type === 'decay' ? 'DECAY' : 'CONFLICT'}
            </span>
          )}
          {conflict.risk_score !== undefined && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <TrendingUp size={10} color={riskColor} />
              <div style={{ width: '40px', height: '3px', background: 'var(--border-default)', borderRadius: '999px', overflow: 'hidden' }}>
                <div style={{ height: '100%', width: `${Math.min(score * 100, 100)}%`, background: riskColor, borderRadius: '999px' }} />
              </div>
              <span style={{ fontSize: '10px', color: riskColor, fontFamily: 'monospace' }}>{score.toFixed(2)}</span>
            </div>
          )}
        </div>
      </div>

      {/* Value comparison */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px', marginBottom: '10px' }}>
        {[
          { label: isResolved && conflict.authoritative_source?.doc_id === conflict.source_a.doc_id ? '✓ Current' : 'Source A', file: conflict.source_a.source_file, value: conflict.value_a },
          { label: isResolved && conflict.authoritative_source?.doc_id === conflict.source_b.doc_id ? '✓ Current' : 'Source B', file: conflict.source_b.source_file, value: conflict.value_b },
        ].map((src, i) => (
          <div key={i} style={{
            padding: '8px 10px', background: 'var(--bg-surface)',
            borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)',
          }}>
            <p style={{ fontSize: '10px', color: 'var(--text-muted)', marginBottom: '4px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={src.file}>
              {src.label}: {src.file}
            </p>
            <p style={{ fontFamily: 'monospace', fontSize: '13px', fontWeight: 700, color: i === 0 ? 'var(--danger)' : 'var(--warning)' }}>
              {src.value}
            </p>
          </div>
        ))}
      </div>

      {/* Business impact */}
      {conflict.business_impact && (
        <div style={{
          padding: '8px 10px', background: isResolved ? 'var(--accent-dim)' : 'var(--danger-dim)',
          borderRadius: 'var(--radius-sm)',
          borderLeft: `3px solid ${isResolved ? 'var(--accent)' : 'var(--danger)'}`,
          marginBottom: '8px',
        }}>
          <p style={{ fontSize: '10px', textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--text-muted)', marginBottom: '3px' }}>
            {isResolved ? 'Historical Impact' : 'Business Impact'}
          </p>
          <p style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>{conflict.business_impact}</p>
        </div>
      )}

      {/* Explanation */}
      <p style={{
        fontSize: '12px', color: 'var(--text-muted)', fontStyle: 'italic', lineHeight: 1.5,
        borderLeft: '2px solid var(--border-default)', paddingLeft: '8px',
      }}>
        {conflict.explanation || `Contradicting values for ${conflict.parameter}.`}
      </p>
    </div>
  );
};
