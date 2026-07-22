import React, { useState } from 'react';
import type { RootCauseChain } from '../types/schemas';
import { AlertOctagon, ChevronDown, ChevronUp, ClipboardList, Database, GitBranch } from 'lucide-react';

interface Props {
  chain: RootCauseChain;
}

export function RootCausePanel({ chain }: Props) {
  const [expanded, setExpanded] = useState(true);

  return (
    <div
      id="rca-panel"
      className="mt-4 rounded-xl border border-amber-700/50 bg-amber-950/20 overflow-hidden"
    >
      {/* Header */}
      <button
        id="rca-toggle-btn"
        onClick={() => setExpanded(e => !e)}
        className="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-amber-900/20 transition-colors"
      >
        <div className="flex items-center gap-2">
          <AlertOctagon size={16} className="text-amber-400" />
          <span className="text-sm font-semibold text-amber-300">Root Cause Analysis</span>
          {chain.incident && (
            <span className="text-xs px-2 py-0.5 rounded-full bg-amber-900/40 text-amber-400 border border-amber-700/50 uppercase font-medium">
              {chain.incident.severity}
            </span>
          )}
        </div>
        {expanded ? <ChevronUp size={14} className="text-slate-400" /> : <ChevronDown size={14} className="text-slate-400" />}
      </button>

      {expanded && (
        <div className="px-4 pb-4 space-y-4 border-t border-amber-800/30">
          {/* Likely Root Cause */}
          <div className="pt-3">
            <p className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
              <GitBranch size={11} /> Likely Root Cause
            </p>
            <p className="text-sm text-amber-200 leading-relaxed">{chain.likely_root_cause}</p>
          </div>

          {/* Recommended Checks */}
          {chain.recommended_checks.length > 0 && (
            <div>
              <p className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                <ClipboardList size={11} /> Recommended Checks
              </p>
              <ol className="space-y-1.5">
                {chain.recommended_checks.map((check, i) => (
                  <li key={i} className="flex items-start gap-2.5 text-sm text-slate-200">
                    <span className="flex-shrink-0 w-5 h-5 rounded-full bg-amber-800/50 text-amber-300 text-xs font-bold flex items-center justify-center mt-0.5">
                      {i + 1}
                    </span>
                    {check}
                  </li>
                ))}
              </ol>
            </div>
          )}

          {/* Evidence Chips */}
          <div className="flex flex-wrap gap-2">
            {chain.related_claims.slice(0, 4).map((c, i) => (
              <span
                key={i}
                title={c.source_text}
                className="inline-flex items-center gap-1 text-xs px-2 py-1 rounded-full bg-slate-800 border border-slate-700 text-slate-400"
              >
                <Database size={9} className="text-cyan-500" />
                {c.equipment_tag}/{c.parameter_name}
              </span>
            ))}
            {chain.related_conflicts.slice(0, 2).map((c, i) => (
              <span
                key={i}
                title={c.explanation}
                className="inline-flex items-center gap-1 text-xs px-2 py-1 rounded-full bg-red-900/30 border border-red-800/50 text-red-400"
              >
                ⚠ {c.entity}/{c.parameter}
              </span>
            ))}
            {chain.similar_incidents.slice(0, 2).map((inc, i) => (
              <span
                key={i}
                title={inc.description}
                className="inline-flex items-center gap-1 text-xs px-2 py-1 rounded-full bg-orange-900/30 border border-orange-800/50 text-orange-400"
              >
                📋 {inc.incident_type}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
