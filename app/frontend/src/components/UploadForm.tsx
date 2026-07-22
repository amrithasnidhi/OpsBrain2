import { useState, useRef } from 'react';
import { UploadCloud, CheckCircle2, AlertTriangle, Loader2, FileText, X, Zap, Shield, Clock } from 'lucide-react';

type UploadState = 'idle' | 'uploading' | 'success' | 'error';
interface IngestResult { filename: string; chunks_ingested: number; conflict_count: number; }

const SUPPORTED = ['.pdf', '.xlsx', '.xls', '.png', '.jpg', '.jpeg', '.txt', '.docx'];

export function UploadForm() {
  const [file, setFile] = useState<File | null>(null);
  const [state, setState] = useState<UploadState>('idle');
  const [result, setResult] = useState<IngestResult | null>(null);
  const [errorMsg, setErrorMsg] = useState('');
  const [drag, setDrag] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = (f: File | null) => {
    if (!f) return;
    const ext = '.' + f.name.split('.').pop()?.toLowerCase();
    if (!SUPPORTED.includes(ext)) {
      setErrorMsg(`Unsupported file type "${ext}". Supported: ${SUPPORTED.join(', ')}`);
      setState('error'); return;
    }
    setFile(f); setState('idle'); setErrorMsg(''); setResult(null);
  };

  const handleIngest = async () => {
    if (!file) return;
    setState('uploading'); setResult(null); setErrorMsg('');
    const form = new FormData();
    form.append('file', file);
    try {
      const res = await fetch('http://127.0.0.1:8000/api/ingest', { method: 'POST', body: form });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail ?? 'Ingestion failed');
      setResult(data); setState('success');
    } catch (err: any) {
      setErrorMsg(err.message ?? 'Unknown error'); setState('error');
    }
  };

  const FEATURES = [
    { icon: Zap, title: 'Instant Embedding', desc: 'Chunks are vectorised and added to ChromaDB within seconds.' },
    { icon: Shield, title: 'Conflict Scanning', desc: 'System re-scans for contradictions the moment a doc is added.' },
    { icon: Clock, title: 'Idempotent Upserts', desc: 'Re-uploading the same file never creates duplicate entries.' },
  ];

  return (
    <div style={{ height: '100%', overflowY: 'auto', background: 'var(--bg-base)', display: 'flex', flexDirection: 'column' }}>
      {/* ── Two-column hero ── */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', flex: 1, minHeight: 0 }}>

        {/* LEFT — branding panel */}
        <div style={{
          padding: '60px 56px',
          background: 'linear-gradient(145deg, #0d1225 0%, #080c18 100%)',
          borderRight: '1px solid var(--border-subtle)',
          display: 'flex', flexDirection: 'column', justifyContent: 'space-between',
        }}>
          <div>
            <p style={{ fontSize: '11px', fontWeight: 700, letterSpacing: '0.14em', textTransform: 'uppercase', color: 'var(--accent)', marginBottom: '16px' }}>
              Knowledge Ingestion
            </p>
            <h1 style={{ fontFamily: 'var(--font-display)', fontStyle: 'italic', fontSize: '56px', fontWeight: 700, color: 'var(--text-primary)', lineHeight: 1.0, marginBottom: '20px' }}>
              Upload it.
            </h1>
            <div style={{ width: '48px', height: '4px', background: 'var(--accent)', borderRadius: '999px', marginBottom: '24px' }} />
            <p style={{ color: 'var(--text-muted)', fontSize: '16px', lineHeight: 1.7, maxWidth: '380px' }}>
              Add a manual, SOP, maintenance log, or incident report. The system will parse, embed, and immediately re-scan for contradictions.
            </p>
          </div>

          {/* Feature list */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {FEATURES.map(({ icon: Icon, title, desc }) => (
              <div key={title} style={{ display: 'flex', alignItems: 'flex-start', gap: '14px' }}>
                <div style={{ width: '36px', height: '36px', borderRadius: '10px', background: 'var(--accent-dim)', border: '1px solid rgba(0,230,118,0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                  <Icon size={16} color="var(--accent)" />
                </div>
                <div>
                  <p style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '2px' }}>{title}</p>
                  <p style={{ fontSize: '12px', color: 'var(--text-muted)', lineHeight: 1.5 }}>{desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* RIGHT — upload form */}
        <div style={{ padding: '60px 56px', display: 'flex', flexDirection: 'column', justifyContent: 'center', gap: '18px', overflowY: 'auto' }}>
          {state === 'success' && result ? (
            <div className="animate-fade-in-up" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '16px', textAlign: 'center', padding: '40px' }}>
              <div style={{ width: '64px', height: '64px', borderRadius: '50%', background: 'var(--accent-dim)', border: '1px solid rgba(0,230,118,0.3)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <CheckCircle2 size={32} color="var(--accent)" />
              </div>
              <h2 style={{ fontFamily: 'var(--font-display)', fontStyle: 'italic', fontSize: '32px', color: 'var(--text-primary)' }}>Success!</h2>
              <p style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>
                <strong style={{ color: 'var(--accent)' }}>{result.filename}</strong> — {result.chunks_ingested} chunks stored.
              </p>
              {result.conflict_count > 0 && (
                <p style={{ fontSize: '13px', color: 'var(--warning)', fontWeight: 600 }}>
                  ⚠ {result.conflict_count} conflicts now flagged in the system.
                </p>
              )}
              <button onClick={() => { setState('idle'); setFile(null); setResult(null); }} style={{ padding: '11px 28px', background: 'var(--accent)', border: 'none', borderRadius: 'var(--radius-md)', color: '#000', fontWeight: 700, fontSize: '14px', cursor: 'pointer', fontFamily: 'var(--font-body)' }}>
                Upload Another
              </button>
            </div>
          ) : (
            <>
              <div>
                <p style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '16px' }}>Drop or select a document</p>
                {/* Drop zone */}
                <div
                  id="upload-drop-zone"
                  onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
                  onDragLeave={() => setDrag(false)}
                  onDrop={(e) => { e.preventDefault(); setDrag(false); handleFile(e.dataTransfer.files[0] ?? null); }}
                  onClick={() => inputRef.current?.click()}
                  style={{
                    border: `2px dashed ${drag ? 'var(--accent)' : file ? 'rgba(0,230,118,0.35)' : 'var(--border-default)'}`,
                    borderRadius: 'var(--radius-xl)', padding: '52px 32px',
                    textAlign: 'center', cursor: 'pointer',
                    background: drag ? 'var(--accent-dim)' : file ? 'rgba(0,230,118,0.04)' : 'var(--bg-card)',
                    transition: 'all 0.2s ease',
                  }}
                >
                  <input ref={inputRef} id="upload-file-input" type="file" accept={SUPPORTED.join(',')} style={{ display: 'none' }} onChange={(e) => handleFile(e.target.files?.[0] ?? null)} />
                  {file ? (
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '12px' }}>
                      <div style={{ width: '52px', height: '52px', borderRadius: 'var(--radius-md)', background: 'var(--accent-dim)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        <FileText size={24} color="var(--accent)" />
                      </div>
                      <p style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '15px' }}>{file.name}</p>
                      <p style={{ color: 'var(--text-muted)', fontSize: '12px' }}>{(file.size / 1024).toFixed(1)} KB</p>
                      <button onClick={(e) => { e.stopPropagation(); setFile(null); setState('idle'); }} style={{ background: 'var(--danger-dim)', border: '1px solid rgba(255,71,87,0.25)', borderRadius: '999px', padding: '4px 12px', color: 'var(--danger)', fontSize: '11px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <X size={10} /> Remove
                      </button>
                    </div>
                  ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '12px' }}>
                      <div style={{ width: '56px', height: '56px', borderRadius: 'var(--radius-md)', background: 'var(--bg-surface)', border: '1px solid var(--border-default)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        <UploadCloud size={24} color="var(--text-muted)" />
                      </div>
                      <p style={{ color: 'var(--text-secondary)', fontSize: '15px' }}>
                        Drag & drop, or <span style={{ color: 'var(--accent)', fontWeight: 600 }}>click to browse</span>
                      </p>
                      <p style={{ color: 'var(--text-muted)', fontSize: '12px' }}>{SUPPORTED.join('  ·  ')}</p>
                    </div>
                  )}
                </div>
              </div>

              <button id="ingest-submit-btn" onClick={handleIngest} disabled={!file || state === 'uploading'} style={{
                width: '100%', padding: '16px', borderRadius: 'var(--radius-md)', border: 'none',
                cursor: !file || state === 'uploading' ? 'not-allowed' : 'pointer',
                background: !file || state === 'uploading' ? 'var(--bg-card)' : 'var(--accent)',
                color: !file || state === 'uploading' ? 'var(--text-muted)' : '#000',
                fontSize: '15px', fontWeight: 700, fontFamily: 'var(--font-body)',
                display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
                transition: 'all 0.2s ease',
              }}>
                {state === 'uploading' ? <><Loader2 size={16} style={{ animation: 'spin 1s linear infinite' }} /> Ingesting…</> : <><UploadCloud size={16} /> Ingest Document</>}
              </button>

              {state === 'error' && (
                <div id="upload-error-banner" className="animate-fade-in-up" style={{ padding: '14px 16px', background: 'var(--danger-dim)', border: '1px solid rgba(255,71,87,0.25)', borderRadius: 'var(--radius-md)', display: 'flex', gap: '10px' }}>
                  <AlertTriangle size={18} color="var(--danger)" style={{ flexShrink: 0 }} />
                  <p style={{ fontSize: '13px', color: 'var(--danger)' }}>{errorMsg}</p>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
