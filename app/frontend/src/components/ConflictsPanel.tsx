import React, { useEffect, useState } from 'react';
import type { Conflict } from '../types/schemas';
import { ConflictCard } from './ConflictCard';
import { AlertTriangle, TrendingUp } from 'lucide-react';

interface Props {
  activeConflicts: Conflict[];
}

export const ConflictsPanel: React.FC<Props> = ({ activeConflicts }) => {
  const [allConflicts, setAllConflicts] = useState<Conflict[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch((import.meta.env.VITE_API_URL || 'http://localhost:8000') + '/api/conflicts')
      .then(res => res.json())
      .then(data => {
        // Data comes pre-sorted by risk_score from backend
        setAllConflicts(data);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  // Count by risk level
  const highRisk = allConflicts.filter(c => (c.risk_score || 0) >= 0.7).length;
  const mediumRisk = allConflicts.filter(c => (c.risk_score || 0) >= 0.3 && (c.risk_score || 0) < 0.7).length;
  const resolved = allConflicts.filter(c => c.resolution === 'temporal_supersession').length;

  return (
    <div className="h-full flex flex-col bg-slate-900 border-l border-slate-800">
      <div className="p-4 border-b border-slate-800 bg-slate-900/95 sticky top-0 backdrop-blur z-10">
        <h2 className="text-xl font-bold flex items-center gap-2">
          <AlertTriangle className="text-red-500" />
          Flagged Conflicts
          <span className="bg-slate-800 text-slate-300 text-xs px-2 py-1 rounded-full">
            {allConflicts.length}
          </span>
        </h2>

        {/* Risk summary */}
        {allConflicts.length > 0 && (
          <div className="flex gap-3 mt-2 text-xs">
            {highRisk > 0 && (
              <span className="flex items-center gap-1 text-red-400">
                <TrendingUp size={12} />
                {highRisk} High Risk
              </span>
            )}
            {mediumRisk > 0 && (
              <span className="flex items-center gap-1 text-amber-400">
                <TrendingUp size={12} />
                {mediumRisk} Medium
              </span>
            )}
            {resolved > 0 && (
              <span className="flex items-center gap-1 text-green-400">
                {resolved} Resolved
              </span>
            )}
          </div>
        )}
      </div>

      <div className="p-4 overflow-y-auto flex-1 flex flex-col gap-4">
        {loading ? (
          <div className="animate-pulse space-y-4">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-48 bg-slate-800 rounded-lg"></div>
            ))}
          </div>
        ) : allConflicts.length === 0 ? (
          <div className="text-center text-slate-500 mt-10">
            No conflicts detected in the knowledge base.
          </div>
        ) : (
          allConflicts.map((conflict, idx) => {
            const isActive = activeConflicts.some(
              ac => ac.entity === conflict.entity && ac.parameter === conflict.parameter
            );
            return (
              <ConflictCard
                key={`${conflict.entity}-${conflict.parameter}-${idx}`}
                conflict={conflict}
                isActive={isActive}
              />
            );
          })
        )}
      </div>
    </div>
  );
};
