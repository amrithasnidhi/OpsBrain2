import { useState } from 'react';
import type { RootCauseChain } from '../types/schemas';
import { AlertOctagon, ChevronDown, ChevronUp, ClipboardList, Database, GitBranch } from 'lucide-react';

interface Props { chain: RootCauseChain; }

export function RootCausePanel({ chain }: Props) {
  const [expanded, setExpanded] = useState(true);

  return (
    <div id="rca-panel" style={{
      borderRadius: 'var(--radius-md)', border: '1px solid rgba(255,165,2,0.2)',
      background: 'var(--warning-dim)', overflow: 'hidden', marginTop: '4px',
    }}>
      {/* Header toggle */}
      <button id="rca-toggle-btn" onClick={() => setExpanded(e => !e)} style={{
        width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '12px 14px', background: 'transparent', border: 'none', cursor: 'pointer',
        transition: 'background 0.15s ease',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <AlertOctagon size={14} color="var(--warning)" />
          <span style={{ fontSize: '12px', fontWeight: 700, color: 'var(--warning)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
            Root Cause Analysis
          </span>
          {chain.incident && (
            <span style={{
              fontSize: '10px', padding: '1px 7px', borderRadius: '999px',
              background: 'rgba(255,165,2,0.2)', color: 'var(--warning)', border: '1px solid rgba(255,165,2,0.3)',
              fontWeight: 700, textTransform: 'uppercase',
            }}>
              {chain.incident.severity}
            </span>
          )}
        </div>
        {expanded
          ? <ChevronUp size={13} color="var(--text-muted)" />
          : <ChevronDown size={13} color="var(--text-muted)" />
        }
      </button>

      {expanded && (
        <div style={{ padding: '0 14px 14px', display: 'flex', flexDirection: 'column', gap: '12px', borderTop: '1px solid rgba(255,165,2,0.15)' }}>

          {/* Root cause */}
          <div style={{ paddingTop: '12px' }}>
            <p style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '10px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text-muted)', marginBottom: '6px' }}>
              <GitBranch size={10} /> Likely Root Cause
            </p>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: 1.6 }}>{chain.likely_root_cause}</p>
          </div>

          {/* Recommended checks */}
          {chain.recommended_checks.length > 0 && (
            <div>
              <p style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '10px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text-muted)', marginBottom: '8px' }}>
                <ClipboardList size={10} /> Recommended Checks
              </p>
              <ol style={{ display: 'flex', flexDirection: 'column', gap: '6px', paddingLeft: 0, listStyle: 'none' }}>
                {chain.recommended_checks.map((check, i) => (
                  <li key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: '8px', fontSize: '13px', color: 'var(--text-secondary)' }}>
                    <span style={{
                      flexShrink: 0, width: '18px', height: '18px', borderRadius: '50%',
                      background: 'rgba(255,165,2,0.2)', color: 'var(--warning)',
                      fontSize: '10px', fontWeight: 700,
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      marginTop: '2px',
                    }}>
                      {i + 1}
                    </span>
                    {check}
                  </li>
                ))}
              </ol>
            </div>
          )}

          {/* Evidence chips */}
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
            {chain.related_claims.slice(0, 4).map((c, i) => (
              <span key={i} title={c.source_text} style={{
                display: 'inline-flex', alignItems: 'center', gap: '4px',
                fontSize: '11px', padding: '3px 8px', borderRadius: '999px',
                background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', color: 'var(--text-muted)',
              }}>
                <Database size={9} color="var(--info)" />
                {c.equipment_tag}/{c.parameter_name}
              </span>
            ))}
            {chain.related_conflicts.slice(0, 2).map((c, i) => (
              <span key={i} title={c.explanation} style={{
                display: 'inline-flex', alignItems: 'center', gap: '4px',
                fontSize: '11px', padding: '3px 8px', borderRadius: '999px',
                background: 'var(--danger-dim)', border: '1px solid rgba(255,71,87,0.2)', color: 'var(--danger)',
              }}>
                ⚠ {c.entity}/{c.parameter}
              </span>
            ))}
            {chain.similar_incidents.slice(0, 2).map((inc, i) => (
              <span key={i} title={inc.description} style={{
                display: 'inline-flex', alignItems: 'center', gap: '4px',
                fontSize: '11px', padding: '3px 8px', borderRadius: '999px',
                background: 'var(--warning-dim)', border: '1px solid rgba(255,165,2,0.2)', color: 'var(--warning)',
              }}>
                📋 {inc.incident_type}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
