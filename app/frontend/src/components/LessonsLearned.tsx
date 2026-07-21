import React from 'react';
import type { Incident } from '../types/schemas';
import { ShieldAlert } from 'lucide-react';

interface Props {
  incidents: Incident[];
}

export const LessonsLearned: React.FC<Props> = ({ incidents }) => {
  if (!incidents || incidents.length === 0) return null;

  return (
    <div className="mt-4 space-y-2">
      {incidents.map((inc, idx) => (
        <div key={idx} className="bg-red-950/30 border border-red-900/50 p-4 rounded-lg flex items-start gap-3">
          <ShieldAlert className="text-red-500 mt-1 shrink-0" size={20} />
          <div>
            <h4 className="text-red-400 font-semibold mb-1 flex items-center gap-2">
              Related Past Incident
              <span className="text-xs bg-red-900/50 px-2 py-0.5 rounded text-red-300 font-mono">
                {inc.equipment_tag}
              </span>
            </h4>
            <p className="text-sm text-slate-300">{inc.description}</p>
            <div className="flex gap-4 mt-2 text-xs text-slate-500">
              {inc.date && <span>Date: {inc.date}</span>}
              <span className="uppercase tracking-wider">Severity: <span className="text-red-400 font-bold">{inc.severity}</span></span>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};
