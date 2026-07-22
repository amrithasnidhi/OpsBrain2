import React, { useEffect, useState } from 'react';
import type { ComplianceGap } from '../types/schemas';
import { Shield, AlertTriangle, CheckCircle, HelpCircle, RefreshCw } from 'lucide-react';

export default function CompliancePanel() {
  const [gaps, setGaps] = useState<ComplianceGap[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchCompliance = () => {
    setLoading(true);
    setError(null);
    fetch((import.meta.env.VITE_API_URL || 'http://localhost:8000') + '/api/compliance')
      .then(res => {
        if (!res.ok) throw new Error('Failed to fetch compliance data');
        return res.json();
      })
      .then(data => {
        setGaps(data);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchCompliance();
  }, []);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'compliant':
        return <CheckCircle className="text-green-400" size={18} />;
      case 'gap':
        return <AlertTriangle className="text-red-400" size={18} />;
      default:
        return <HelpCircle className="text-slate-400" size={18} />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'compliant':
        return 'bg-green-900/30 border-green-700 text-green-300';
      case 'gap':
        return 'bg-red-900/30 border-red-700 text-red-300';
      default:
        return 'bg-slate-800 border-slate-600 text-slate-400';
    }
  };

  // Group by standard
  const groupedByStandard = gaps.reduce((acc, gap) => {
    if (!acc[gap.standard]) acc[gap.standard] = [];
    acc[gap.standard].push(gap);
    return acc;
  }, {} as Record<string, ComplianceGap[]>);

  // Count summary
  const gapCount = gaps.filter(g => g.status === 'gap').length;
  const compliantCount = gaps.filter(g => g.status === 'compliant').length;
  const unknownCount = gaps.filter(g => g.status === 'unknown').length;

  return (
    <div className="h-full bg-slate-950 text-slate-200 overflow-auto">
      <div className="max-w-6xl mx-auto p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <Shield className="text-blue-500" size={32} />
            <div>
              <h1 className="text-2xl font-bold">Compliance Status</h1>
              <p className="text-slate-400 text-sm">
                Real-time compliance gap detection against industry standards
              </p>
            </div>
          </div>
          <button
            onClick={fetchCompliance}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors disabled:opacity-50"
          >
            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
            Refresh
          </button>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className="bg-red-900/20 border border-red-700/50 rounded-lg p-4">
            <div className="flex items-center gap-2 text-red-400 mb-1">
              <AlertTriangle size={20} />
              <span className="font-semibold">Gaps Found</span>
            </div>
            <p className="text-3xl font-bold text-red-300">{gapCount}</p>
          </div>
          <div className="bg-green-900/20 border border-green-700/50 rounded-lg p-4">
            <div className="flex items-center gap-2 text-green-400 mb-1">
              <CheckCircle size={20} />
              <span className="font-semibold">Compliant</span>
            </div>
            <p className="text-3xl font-bold text-green-300">{compliantCount}</p>
          </div>
          <div className="bg-slate-800 border border-slate-600 rounded-lg p-4">
            <div className="flex items-center gap-2 text-slate-400 mb-1">
              <HelpCircle size={20} />
              <span className="font-semibold">Unknown</span>
            </div>
            <p className="text-3xl font-bold text-slate-300">{unknownCount}</p>
          </div>
        </div>

        {/* Error State */}
        {error && (
          <div className="bg-red-900/30 border border-red-700 rounded-lg p-4 mb-6 text-red-300">
            <AlertTriangle className="inline mr-2" size={16} />
            {error}
          </div>
        )}

        {/* Loading State */}
        {loading ? (
          <div className="space-y-4">
            {[1, 2, 3].map(i => (
              <div key={i} className="animate-pulse bg-slate-800 rounded-lg h-32"></div>
            ))}
          </div>
        ) : (
          /* Compliance Table by Standard */
          <div className="space-y-6">
            {Object.entries(groupedByStandard).map(([standard, items]) => (
              <div key={standard} className="bg-slate-900 rounded-lg border border-slate-800 overflow-hidden">
                <div className="bg-slate-800 px-4 py-3 border-b border-slate-700">
                  <h2 className="font-semibold text-lg">{standard}</h2>
                </div>
                <div className="divide-y divide-slate-800">
                  {items.map((gap, idx) => (
                    <div
                      key={`${gap.equipment_tag}-${idx}`}
                      className={`p-4 flex items-start gap-4 ${
                        gap.status === 'gap' ? 'bg-red-900/10' : ''
                      }`}
                    >
                      <div className="mt-1">{getStatusIcon(gap.status)}</div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-mono text-sm bg-slate-800 px-2 py-0.5 rounded">
                            {gap.equipment_tag}
                          </span>
                          <span className={`text-xs px-2 py-0.5 rounded border ${getStatusColor(gap.status)}`}>
                            {gap.status.toUpperCase()}
                          </span>
                        </div>
                        <p className="text-sm text-slate-300 mb-1">{gap.requirement}</p>
                        <p className="text-xs text-slate-500">{gap.details}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
