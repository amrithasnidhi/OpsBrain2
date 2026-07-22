import React, { useState } from 'react';
import { Brain, CheckCircle2, AlertTriangle, Loader2, User, Tag, BookOpen, FileText, RotateCcw, Lightbulb, GitMerge, AlertOctagon } from 'lucide-react';

type CaptureState = 'idle' | 'capturing' | 'success' | 'error';

const KNOWLEDGE_TYPES = [
  { value: 'undocumented_procedure', label: 'Undocumented Procedure' },
  { value: 'tribal_knowledge',       label: 'Tribal Knowledge'       },
  { value: 'failure_pattern',        label: 'Failure Pattern'        },
];

const inputStyle: React.CSSProperties = {
  width: '100%', background: 'var(--bg-surface)',
  border: '1px solid var(--border-default)',
  borderRadius: 'var(--radius-md)', padding: '12px 16px',
  fontSize: '14px', color: 'var(--text-primary)',
  outline: 'none', fontFamily: 'var(--font-body)',
  transition: 'border-color 0.2s, box-shadow 0.2s',
};

const labelStyle: React.CSSProperties = {
  display: 'flex', alignItems: 'center', gap: '6px',
  fontSize: '11px', fontWeight: 700, letterSpacing: '0.08em',
  textTransform: 'uppercase', color: 'var(--text-muted)',
  marginBottom: '6px',
};

const INFO_ITEMS = [
  { icon: Lightbulb, label: 'Searchable instantly', desc: 'AI incorporates captured knowledge immediately after saving.' },
  { icon: GitMerge, label: 'Conflict detection', desc: 'New claims are compared against the existing knowledge graph.' },
  { icon: AlertOctagon, label: 'Pattern recognition', desc: 'Failure patterns help the AI predict future risks proactively.' },
];

export function KnowledgeCaptureForm() {
  const [form, setForm] = useState({ expert_name: '', equipment_tag: '', knowledge_type: 'tribal_knowledge', free_text: '' });
  const [state, setState] = useState<CaptureState>('idle');
  const [resultDocId, setResultDocId] = useState('');
  const [errorMsg, setErrorMsg] = useState('');

  const set = (key: string, val: string) => setForm(f => ({ ...f, [key]: val }));
  const valid = form.expert_name.trim() && form.equipment_tag.trim() && form.free_text.trim().length >= 20;

  const handleSubmit = async () => {
    if (!valid) return;
    setState('capturing'); setErrorMsg(''); setResultDocId('');
    try {
      const res = await fetch('http://127.0.0.1:8000/api/capture-knowledge', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(form) });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail ?? 'Capture failed');
      setResultDocId(data.doc_id); setState('success');
    } catch (err: any) {
      setErrorMsg(err.message ?? 'Unknown error'); setState('error');
    }
  };

  const handleReset = () => { setState('idle'); setResultDocId(''); setErrorMsg(''); setForm({ expert_name: '', equipment_tag: '', knowledge_type: 'tribal_knowledge', free_text: '' }); };

  const onFocus = (e: React.FocusEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => { e.target.style.borderColor = 'var(--accent)'; e.target.style.boxShadow = '0 0 0 3px rgba(0,230,118,0.1)'; };
  const onBlur  = (e: React.FocusEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => { e.target.style.borderColor = 'var(--border-default)'; e.target.style.boxShadow = 'none'; };

  return (
    <div style={{ height: '100%', overflowY: 'auto', background: 'var(--bg-base)' }}>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', minHeight: '100%' }}>

        {/* LEFT panel */}
        <div style={{
          padding: '60px 56px',
          background: 'linear-gradient(145deg, #0d1225 0%, #080c18 100%)',
          borderRight: '1px solid var(--border-subtle)',
          display: 'flex', flexDirection: 'column', justifyContent: 'space-between',
        }}>
          <div>
            <p style={{ fontSize: '11px', fontWeight: 700, letterSpacing: '0.14em', textTransform: 'uppercase', color: 'var(--accent)', marginBottom: '16px' }}>Expert Knowledge</p>
            <h1 style={{ fontFamily: 'var(--font-display)', fontStyle: 'italic', fontSize: '56px', fontWeight: 700, color: 'var(--text-primary)', lineHeight: 1.0, marginBottom: '20px' }}>
              Capture it.
            </h1>
            <div style={{ width: '48px', height: '4px', background: 'var(--accent)', borderRadius: '999px', marginBottom: '24px' }} />
            <p style={{ color: 'var(--text-muted)', fontSize: '16px', lineHeight: 1.7, maxWidth: '380px' }}>
              Record tribal knowledge, undocumented procedures, or observed failure patterns. Once saved, the AI immediately incorporates it.
            </p>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {INFO_ITEMS.map(({ icon: Icon, label, desc }) => (
              <div key={label} style={{ display: 'flex', alignItems: 'flex-start', gap: '14px' }}>
                <div style={{ width: '36px', height: '36px', borderRadius: '10px', background: 'var(--accent-dim)', border: '1px solid rgba(0,230,118,0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                  <Icon size={16} color="var(--accent)" />
                </div>
                <div>
                  <p style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '2px' }}>{label}</p>
                  <p style={{ fontSize: '12px', color: 'var(--text-muted)', lineHeight: 1.5 }}>{desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* RIGHT — form */}
        <div style={{ padding: '60px 56px', overflowY: 'auto', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
          {state === 'success' ? (
            <div id="capture-success-panel" className="animate-fade-in-up" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '16px', textAlign: 'center' }}>
              <div style={{ width: '64px', height: '64px', borderRadius: '50%', background: 'var(--accent-dim)', border: '1px solid rgba(0,230,118,0.3)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <CheckCircle2 size={32} color="var(--accent)" />
              </div>
              <h2 style={{ fontFamily: 'var(--font-display)', fontStyle: 'italic', fontSize: '32px', color: 'var(--text-primary)' }}>Knowledge Captured!</h2>
              <p style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>
                Stored as <code style={{ color: 'var(--accent)', fontFamily: 'monospace' }}>{resultDocId}</code>
              </p>
              <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
                Ask the AI about <strong style={{ color: 'var(--text-secondary)' }}>{form.equipment_tag}</strong> — it will now cite this.
              </p>
              <button id="capture-again-btn" onClick={handleReset} style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '12px 28px', background: 'var(--accent)', border: 'none', borderRadius: 'var(--radius-md)', color: '#000', fontSize: '14px', fontWeight: 700, cursor: 'pointer', fontFamily: 'var(--font-body)' }}>
                <RotateCcw size={14} /> Capture Another
              </button>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '18px', maxWidth: '520px', width: '100%' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
                <div>
                  <label style={labelStyle}><User size={11} />Expert Name</label>
                  <input id="capture-expert-name" value={form.expert_name} onChange={e => set('expert_name', e.target.value)} placeholder="e.g. John Smith" style={inputStyle} onFocus={onFocus} onBlur={onBlur} />
                </div>
                <div>
                  <label style={labelStyle}><Tag size={11} />Equipment Tag</label>
                  <input id="capture-equipment-tag" value={form.equipment_tag} onChange={e => set('equipment_tag', e.target.value)} placeholder="e.g. PUMP-203" style={inputStyle} onFocus={onFocus} onBlur={onBlur} />
                </div>
              </div>
              <div>
                <label style={labelStyle}><BookOpen size={11} />Knowledge Type</label>
                <select id="capture-knowledge-type" value={form.knowledge_type} onChange={e => set('knowledge_type', e.target.value)} style={{ ...inputStyle, cursor: 'pointer' }} onFocus={onFocus} onBlur={onBlur}>
                  {KNOWLEDGE_TYPES.map(t => <option key={t.value} value={t.value} style={{ background: 'var(--bg-card)' }}>{t.label}</option>)}
                </select>
              </div>
              <div>
                <label style={labelStyle}><FileText size={11} />Knowledge Description</label>
                <textarea id="capture-free-text" value={form.free_text} onChange={e => set('free_text', e.target.value)} rows={7} placeholder="Describe the procedure, observation, or pattern in detail. Include equipment parameters, thresholds, and observed steps." style={{ ...inputStyle, resize: 'none' }} onFocus={onFocus} onBlur={onBlur} />
                <p style={{ fontSize: '11px', color: form.free_text.length >= 20 ? 'var(--accent)' : 'var(--text-muted)', marginTop: '4px' }}>
                  {form.free_text.length} / 20 min characters
                </p>
              </div>
              {state === 'error' && (
                <div id="capture-error-banner" className="animate-fade-in-up" style={{ padding: '12px 14px', background: 'var(--danger-dim)', border: '1px solid rgba(255,71,87,0.25)', borderRadius: 'var(--radius-md)', display: 'flex', gap: '8px' }}>
                  <AlertTriangle size={16} color="var(--danger)" style={{ flexShrink: 0 }} />
                  <p style={{ fontSize: '13px', color: 'var(--danger)' }}>{errorMsg}</p>
                </div>
              )}
              <button id="capture-submit-btn" onClick={handleSubmit} disabled={!valid || state === 'capturing'} style={{ width: '100%', padding: '15px', borderRadius: 'var(--radius-md)', border: 'none', cursor: !valid || state === 'capturing' ? 'not-allowed' : 'pointer', background: !valid || state === 'capturing' ? 'var(--bg-card)' : 'var(--accent)', color: !valid || state === 'capturing' ? 'var(--text-muted)' : '#000', fontSize: '15px', fontWeight: 700, fontFamily: 'var(--font-body)', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', transition: 'all 0.2s ease' }}>
                {state === 'capturing' ? <><Loader2 size={16} style={{ animation: 'spin 1s linear infinite' }} />Saving…</> : <><Brain size={16} />Save to Knowledge Base</>}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
