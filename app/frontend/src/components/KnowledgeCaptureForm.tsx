import React, { useState } from 'react';
import { Brain, CheckCircle, AlertTriangle, Loader2, User, Tag, BookOpen, FileText } from 'lucide-react';

type CaptureState = 'idle' | 'capturing' | 'success' | 'error';

const KNOWLEDGE_TYPES = [
  { value: 'undocumented_procedure', label: 'Undocumented Procedure' },
  { value: 'tribal_knowledge',       label: 'Tribal Knowledge'       },
  { value: 'failure_pattern',        label: 'Failure Pattern'        },
];

export function KnowledgeCaptureForm() {
  const [form, setForm] = useState({
    expert_name: '',
    equipment_tag: '',
    knowledge_type: 'tribal_knowledge',
    free_text: '',
  });
  const [state, setState] = useState<CaptureState>('idle');
  const [resultDocId, setResultDocId] = useState('');
  const [errorMsg, setErrorMsg] = useState('');

  const set = (key: string, val: string) => setForm(f => ({ ...f, [key]: val }));

  const valid = form.expert_name.trim() && form.equipment_tag.trim() && form.free_text.trim().length >= 20;

  const handleSubmit = async () => {
    if (!valid) return;
    setState('capturing');
    setErrorMsg('');
    setResultDocId('');

    try {
      const res = await fetch('http://127.0.0.1:8000/api/capture-knowledge', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail ?? 'Capture failed');
      setResultDocId(data.doc_id);
      setState('success');
    } catch (err: any) {
      setErrorMsg(err.message ?? 'Unknown error');
      setState('error');
    }
  };

  const handleReset = () => {
    setState('idle');
    setResultDocId('');
    setErrorMsg('');
    setForm({ expert_name: '', equipment_tag: '', knowledge_type: 'tribal_knowledge', free_text: '' });
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200 flex items-center justify-center p-6">
      <div className="w-full max-w-xl">
        <div className="mb-8 text-center">
          <div className="inline-flex items-center gap-2 text-violet-400 mb-2">
            <Brain size={28} />
            <span className="text-2xl font-bold tracking-tight">Capture Expert Knowledge</span>
          </div>
          <p className="text-slate-400 text-sm">
            Record tribal knowledge, undocumented procedures, or observed failure patterns.
            Once captured, this knowledge is immediately searchable by the AI.
          </p>
        </div>

        {state === 'success' ? (
          <div id="capture-success-panel" className="p-6 rounded-xl bg-violet-900/20 border border-violet-700 text-center space-y-4">
            <CheckCircle size={40} className="text-violet-400 mx-auto" />
            <p className="font-semibold text-violet-300 text-lg">Knowledge Captured!</p>
            <p className="text-sm text-slate-400">Stored as <code className="text-violet-300">{resultDocId}</code></p>
            <p className="text-sm text-slate-400">
              You can now ask the AI about <strong className="text-slate-200">{form.equipment_tag}</strong> and it will cite this knowledge.
            </p>
            <button
              id="capture-again-btn"
              onClick={handleReset}
              className="mt-2 px-6 py-2 rounded-lg bg-violet-600 hover:bg-violet-500 text-white text-sm font-medium transition-colors"
            >
              Capture Another
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            {/* Expert Name */}
            <div>
              <label className="flex items-center gap-2 text-xs font-medium text-slate-400 uppercase tracking-wider mb-1.5">
                <User size={12} /> Expert Name
              </label>
              <input
                id="capture-expert-name"
                value={form.expert_name}
                onChange={e => set('expert_name', e.target.value)}
                placeholder="e.g. John Smith (Senior Operator)"
                className="w-full px-3 py-2.5 rounded-lg bg-slate-800 border border-slate-700 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-violet-500 text-sm"
              />
            </div>

            {/* Equipment Tag */}
            <div>
              <label className="flex items-center gap-2 text-xs font-medium text-slate-400 uppercase tracking-wider mb-1.5">
                <Tag size={12} /> Equipment Tag
              </label>
              <input
                id="capture-equipment-tag"
                value={form.equipment_tag}
                onChange={e => set('equipment_tag', e.target.value)}
                placeholder="e.g. PUMP-203, PSV-101"
                className="w-full px-3 py-2.5 rounded-lg bg-slate-800 border border-slate-700 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-violet-500 text-sm"
              />
            </div>

            {/* Knowledge Type */}
            <div>
              <label className="flex items-center gap-2 text-xs font-medium text-slate-400 uppercase tracking-wider mb-1.5">
                <BookOpen size={12} /> Knowledge Type
              </label>
              <select
                id="capture-knowledge-type"
                value={form.knowledge_type}
                onChange={e => set('knowledge_type', e.target.value)}
                className="w-full px-3 py-2.5 rounded-lg bg-slate-800 border border-slate-700 text-slate-200 focus:outline-none focus:border-violet-500 text-sm"
              >
                {KNOWLEDGE_TYPES.map(t => (
                  <option key={t.value} value={t.value}>{t.label}</option>
                ))}
              </select>
            </div>

            {/* Free Text */}
            <div>
              <label className="flex items-center gap-2 text-xs font-medium text-slate-400 uppercase tracking-wider mb-1.5">
                <FileText size={12} /> Knowledge Description
              </label>
              <textarea
                id="capture-free-text"
                value={form.free_text}
                onChange={e => set('free_text', e.target.value)}
                rows={6}
                placeholder="Describe the procedure, observation, or pattern in detail. Be as specific as possible — include equipment parameters, thresholds, and steps observed."
                className="w-full px-3 py-2.5 rounded-lg bg-slate-800 border border-slate-700 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-violet-500 text-sm resize-none"
              />
              <p className="text-xs text-slate-600 mt-1">{form.free_text.length} characters (min 20)</p>
            </div>

            {state === 'error' && (
              <div id="capture-error-banner" className="p-3 rounded-lg bg-red-900/30 border border-red-700 flex items-center gap-2">
                <AlertTriangle size={16} className="text-red-400 flex-shrink-0" />
                <p className="text-sm text-red-300">{errorMsg}</p>
              </div>
            )}

            <button
              id="capture-submit-btn"
              onClick={handleSubmit}
              disabled={!valid || state === 'capturing'}
              className={`
                w-full py-3 rounded-xl font-semibold text-sm flex items-center justify-center gap-2 transition-all
                ${!valid || state === 'capturing'
                  ? 'bg-slate-800 text-slate-500 cursor-not-allowed'
                  : 'bg-violet-600 hover:bg-violet-500 text-white cursor-pointer'}
              `}
            >
              {state === 'capturing' ? (
                <><Loader2 size={16} className="animate-spin" /> Saving Knowledge…</>
              ) : (
                <><Brain size={16} /> Save to Knowledge Base</>
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
