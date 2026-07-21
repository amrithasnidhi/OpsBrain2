import React from 'react';
import type { ConfidenceBreakdown } from '../types/schemas';
import { CheckCircle2, AlertTriangle } from 'lucide-react';

interface Props {
  breakdown: ConfidenceBreakdown;
}

export const ConfidenceBreakdownPanel: React.FC<Props> = ({ breakdown }) => {
  if (breakdown.reasons.length === 0 && breakdown.warnings.length === 0) {
    return null;
  }

  return (
    <div className="flex flex-col gap-1 mt-2 text-xs text-slate-300 bg-slate-900/50 p-3 rounded border border-slate-800">
      {breakdown.reasons.map((reason, idx) => (
        <div key={`reason-${idx}`} className="flex items-start gap-2">
          <CheckCircle2 size={14} className="text-green-500 shrink-0 mt-0.5" />
          <span>{reason}</span>
        </div>
      ))}
      {breakdown.warnings.map((warning, idx) => (
        <div key={`warning-${idx}`} className="flex items-start gap-2">
          <AlertTriangle size={14} className="text-amber-500 shrink-0 mt-0.5" />
          <span>{warning}</span>
        </div>
      ))}
    </div>
  );
};
