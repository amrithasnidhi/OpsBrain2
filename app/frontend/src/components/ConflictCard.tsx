import React from 'react';
import type { Conflict } from '../types/schemas';
import { AlertTriangle, Clock, CheckCircle, TrendingUp } from 'lucide-react';

interface Props {
  conflict: Conflict;
  isActive?: boolean;
}

export const ConflictCard: React.FC<Props> = ({ conflict, isActive = false }) => {
  // Risk meter: green (0-0.3), amber (0.3-0.7), red (0.7+)
  const getRiskColor = (score: number | undefined) => {
    if (!score) return { bg: 'bg-slate-500', text: 'text-slate-400', label: 'Unknown' };
    if (score >= 0.7) return { bg: 'bg-red-500', text: 'text-red-400', label: 'High Risk' };
    if (score >= 0.3) return { bg: 'bg-amber-500', text: 'text-amber-400', label: 'Medium Risk' };
    return { bg: 'bg-green-500', text: 'text-green-400', label: 'Low Risk' };
  };

  const riskStyle = getRiskColor(conflict.risk_score);
  const riskPercent = Math.min((conflict.risk_score || 0) * 50, 100);

  // Check if temporally resolved
  const isResolved = conflict.resolution === 'temporal_supersession';

  return (
    <div
      className={`p-4 rounded-lg border-2 transition-all duration-300 ${
        isActive
          ? 'border-red-500 bg-red-900/20 scale-[1.02] shadow-lg shadow-red-500/20'
          : isResolved
            ? 'border-green-700 bg-green-900/10'
            : 'border-slate-700 bg-slate-800'
      }`}
    >
      {/* Header with entity and badges */}
      <div className="flex justify-between items-start mb-3">
        <h3 className="font-bold text-lg">{conflict.entity}</h3>
        <div className="flex gap-2 flex-wrap justify-end">
          {/* Risk Score Meter */}
          {conflict.risk_score !== undefined && (
            <div className="flex items-center gap-1">
              <TrendingUp size={14} className={riskStyle.text} />
              <div className="w-16 h-2 bg-slate-700 rounded-full overflow-hidden">
                <div
                  className={`h-full ${riskStyle.bg} transition-all`}
                  style={{ width: `${riskPercent}%` }}
                />
              </div>
              <span className={`text-xs ${riskStyle.text} font-mono`}>
                {conflict.risk_score.toFixed(2)}
              </span>
            </div>
          )}

          {/* Resolution or Type Badge */}
          {isResolved ? (
            <span className="text-xs px-2 py-1 rounded-full font-semibold flex items-center gap-1 bg-green-500/20 text-green-400">
              <CheckCircle size={14} />
              RESOLVED
            </span>
          ) : (
            <span className={`text-xs px-2 py-1 rounded-full font-semibold flex items-center gap-1 ${
              conflict.risk_type === 'direct_contradiction'
                ? 'bg-red-500/20 text-red-400'
                : 'bg-orange-500/20 text-orange-400'
            }`}>
              {conflict.risk_type === 'direct_contradiction' ? <AlertTriangle size={14} /> : <Clock size={14} />}
              {conflict.risk_type.replace('_', ' ').toUpperCase()}
            </span>
          )}
        </div>
      </div>

      {/* Temporal Resolution Badge */}
      {isResolved && conflict.authoritative_source && conflict.superseded_source && (
        <div className="mb-3 p-2 bg-green-900/30 border border-green-700/50 rounded text-sm text-green-300">
          <CheckCircle size={14} className="inline mr-1" />
          <strong>Resolved:</strong> {conflict.authoritative_source.source_file} supersedes {conflict.superseded_source.source_file}
        </div>
      )}

      <p className="text-sm text-slate-400 mb-3 font-mono">{conflict.parameter}</p>

      {/* Source comparison */}
      <div className="grid grid-cols-2 gap-2 mb-3">
        <div className={`p-3 rounded border ${
          isResolved && conflict.superseded_source?.doc_id === conflict.source_a.doc_id
            ? 'bg-slate-900/50 border-slate-700 opacity-60'
            : 'bg-slate-900 border-slate-700'
        }`}>
          <p className="text-xs text-slate-500 mb-1 line-clamp-1" title={conflict.source_a.source_file}>
            {isResolved && conflict.authoritative_source?.doc_id === conflict.source_a.doc_id
              ? '✓ Current: '
              : isResolved
                ? '✗ Superseded: '
                : 'Source A: '
            }
            {conflict.source_a.source_file}
          </p>
          <p className={`font-mono text-sm break-all ${
            isResolved && conflict.authoritative_source?.doc_id === conflict.source_a.doc_id
              ? 'text-green-300'
              : 'text-red-300'
          }`}>{conflict.value_a}</p>
        </div>
        <div className={`p-3 rounded border ${
          isResolved && conflict.superseded_source?.doc_id === conflict.source_b.doc_id
            ? 'bg-slate-900/50 border-slate-700 opacity-60'
            : 'bg-slate-900 border-slate-700'
        }`}>
          <p className="text-xs text-slate-500 mb-1 line-clamp-1" title={conflict.source_b.source_file}>
            {isResolved && conflict.authoritative_source?.doc_id === conflict.source_b.doc_id
              ? '✓ Current: '
              : isResolved
                ? '✗ Superseded: '
                : 'Source B: '
            }
            {conflict.source_b.source_file}
          </p>
          <p className={`font-mono text-sm break-all ${
            isResolved && conflict.authoritative_source?.doc_id === conflict.source_b.doc_id
              ? 'text-green-300'
              : 'text-red-300'
          }`}>{conflict.value_b}</p>
        </div>
      </div>

      {/* Business Impact - prominent display */}
      {conflict.business_impact && (
        <div className={`mb-3 p-3 rounded border-l-4 ${
          isResolved
            ? 'bg-green-900/20 border-green-500 text-green-200'
            : conflict.severity === 'high'
              ? 'bg-red-900/30 border-red-500 text-red-200'
              : 'bg-amber-900/20 border-amber-500 text-amber-200'
        }`}>
          <p className="text-xs uppercase tracking-wider mb-1 opacity-70">
            {isResolved ? 'Historical Impact (Resolved)' : 'Business Impact'}
          </p>
          <p className="text-sm font-medium">{conflict.business_impact}</p>
        </div>
      )}

      {/* Explanation */}
      <p className="text-sm text-slate-300 bg-slate-900/50 p-3 rounded italic border-l-4 border-slate-600">
        {conflict.explanation || `Contradicting values detected for ${conflict.parameter}.`}
      </p>

      {/* Severity indicator */}
      <div className="mt-3 flex items-center justify-between text-xs">
        <span className={`px-2 py-0.5 rounded ${
          conflict.severity === 'high'
            ? 'bg-red-900/50 text-red-300'
            : conflict.severity === 'medium'
              ? 'bg-amber-900/50 text-amber-300'
              : 'bg-slate-700 text-slate-400'
        }`}>
          {conflict.severity.toUpperCase()} SEVERITY
        </span>
        {conflict.risk_score !== undefined && (
          <span className={`${riskStyle.text}`}>
            Risk: {riskStyle.label}
          </span>
        )}
      </div>
    </div>
  );
};
