import { useEffect, useState } from 'react';
import type { StalenessRow } from '../types/schemas';
import { AlertCircle, CheckCircle, Clock } from 'lucide-react';

export default function StalenessDashboard() {
  const [rows, setRows] = useState<StalenessRow[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://localhost:8000/api/staleness')
      .then(res => res.json())
      .then(data => {
        setRows(data);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'overdue': return <AlertCircle className="text-red-500" size={20} />;
      case 'warning': return <Clock className="text-amber-500" size={20} />;
      case 'ok': return <CheckCircle className="text-green-500" size={20} />;
      default: return null;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'overdue': return <span className="px-2 py-1 bg-red-500/20 text-red-400 rounded-full text-xs font-bold border border-red-500/30">Overdue</span>;
      case 'warning': return <span className="px-2 py-1 bg-amber-500/20 text-amber-400 rounded-full text-xs font-bold border border-amber-500/30">Warning</span>;
      case 'ok': return <span className="px-2 py-1 bg-green-500/20 text-green-400 rounded-full text-xs font-bold border border-green-500/30">On Schedule</span>;
      default: return null;
    }
  };

  if (loading) {
    return <div className="p-8 text-slate-400">Loading Maintenance Health...</div>;
  }

  return (
    <div className="h-full bg-slate-950 text-slate-200 p-8 overflow-y-auto">
      <h1 className="text-2xl font-bold mb-6 text-white">Maintenance Health Dashboard</h1>
      <div className="bg-slate-900 border border-slate-800 rounded-lg overflow-hidden shadow-xl">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-slate-800 text-slate-400 text-sm border-b border-slate-700">
              <th className="p-4 font-semibold">Equipment</th>
              <th className="p-4 font-semibold">Required Interval</th>
              <th className="p-4 font-semibold">Last Inspection</th>
              <th className="p-4 font-semibold">Days Overdue</th>
              <th className="p-4 font-semibold text-right">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {rows.map((row, i) => (
              <tr key={i} className="hover:bg-slate-800/50 transition-colors">
                <td className="p-4 font-mono font-medium text-blue-400">{row.equipment_tag}</td>
                <td className="p-4 text-slate-300">{row.required_interval}</td>
                <td className="p-4 text-slate-400">{row.last_inspection_date ? row.last_inspection_date.toString() : 'Unknown'}</td>
                <td className="p-4 font-mono">{row.days_overdue > 0 ? <span className="text-red-400">+{row.days_overdue}</span> : <span className="text-green-400">{row.days_overdue}</span>}</td>
                <td className="p-4 flex items-center justify-end gap-3">
                  {getStatusBadge(row.status)}
                  {getStatusIcon(row.status)}
                </td>
              </tr>
            ))}
            {rows.length === 0 && (
              <tr>
                <td colSpan={5} className="p-8 text-center text-slate-500">No maintenance data found.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
