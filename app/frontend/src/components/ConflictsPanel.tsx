import React, { useEffect, useState } from 'react';
import { Conflict } from '../types/schemas';
import { AlertTriangle, Clock } from 'lucide-react';

interface Props {
  activeConflicts: Conflict[];
}

export const ConflictsPanel: React.FC<Props> = ({ activeConflicts }) => {
  const [allConflicts, setAllConflicts] = useState<Conflict[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://localhost:8000/api/conflicts')
      .then(res => res.json())
      .then(data => {
        setAllConflicts(data);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  const renderConflictCard = (conflict: Conflict, idx: number) => {
    const isActive = activeConflicts.some(
      ac => ac.entity === conflict.entity && ac.parameter === conflict.parameter
    );

    return (
      <div 
        key={idx} 
        className={`p-4 rounded-lg border-2 transition-all duration-300 ${isActive ? 'border-red-500 bg-red-900/20 scale-[1.02] shadow-lg shadow-red-500/20' : 'border-slate-700 bg-slate-800'}`}
      >
        <div className="flex justify-between items-start mb-3">
          <h3 className="font-bold text-lg">{conflict.entity}</h3>
          <div className="flex gap-2">
            <span className={`text-xs px-2 py-1 rounded-full font-semibold flex items-center gap-1 ${conflict.risk_type === 'direct_contradiction' ? 'bg-red-500/20 text-red-400' : 'bg-orange-500/20 text-orange-400'}`}>
              {conflict.risk_type === 'direct_contradiction' ? <AlertTriangle size={14} /> : <Clock size={14} />}
              {conflict.risk_type.replace('_', ' ').toUpperCase()}
            </span>
          </div>
        </div>
        
        <p className="text-sm text-slate-400 mb-3 font-mono">{conflict.parameter}</p>
        
        <div className="grid grid-cols-2 gap-2 mb-3">
          <div className="bg-slate-900 p-3 rounded border border-slate-700">
            <p className="text-xs text-slate-500 mb-1 line-clamp-1" title={conflict.source_a.source_file}>Source A: {conflict.source_a.source_file}</p>
            <p className="font-mono text-sm text-red-300 break-all">{conflict.value_a}</p>
          </div>
          <div className="bg-slate-900 p-3 rounded border border-slate-700">
            <p className="text-xs text-slate-500 mb-1 line-clamp-1" title={conflict.source_b.source_file}>Source B: {conflict.source_b.source_file}</p>
            <p className="font-mono text-sm text-red-300 break-all">{conflict.value_b}</p>
          </div>
        </div>
        
        <p className="text-sm text-slate-300 bg-slate-900/50 p-3 rounded italic border-l-4 border-slate-600">
          {conflict.explanation || `Contradicting values detected for ${conflict.parameter}.`}
        </p>
      </div>
    );
  };

  return (
    <div className="h-full flex flex-col bg-slate-900 border-l border-slate-800">
      <div className="p-4 border-b border-slate-800 bg-slate-900/95 sticky top-0 backdrop-blur z-10">
        <h2 className="text-xl font-bold flex items-center gap-2">
          <AlertTriangle className="text-red-500" />
          Flagged Conflicts
          <span className="bg-slate-800 text-slate-300 text-xs px-2 py-1 rounded-full">{allConflicts.length}</span>
        </h2>
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
          allConflicts.map(renderConflictCard)
        )}
      </div>
    </div>
  );
};
