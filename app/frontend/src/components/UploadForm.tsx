import React, { useState, useRef } from 'react';
import { UploadCloud, CheckCircle, AlertTriangle, Loader2, FileText } from 'lucide-react';

type UploadState = 'idle' | 'uploading' | 'success' | 'error';

interface IngestResult {
  filename: string;
  chunks_ingested: number;
  conflict_count: number;
}

export function UploadForm() {
  const [file, setFile] = useState<File | null>(null);
  const [state, setState] = useState<UploadState>('idle');
  const [result, setResult] = useState<IngestResult | null>(null);
  const [errorMsg, setErrorMsg] = useState('');
  const [drag, setDrag] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const SUPPORTED = ['.pdf', '.xlsx', '.xls', '.png', '.jpg', '.jpeg', '.txt', '.docx'];

  const handleFile = (f: File | null) => {
    if (!f) return;
    const ext = '.' + f.name.split('.').pop()?.toLowerCase();
    if (!SUPPORTED.includes(ext)) {
      setErrorMsg(`Unsupported file type "${ext}". Supported: ${SUPPORTED.join(', ')}`);
      setState('error');
      return;
    }
    setFile(f);
    setState('idle');
    setErrorMsg('');
    setResult(null);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDrag(false);
    handleFile(e.dataTransfer.files[0] ?? null);
  };

  const handleIngest = async () => {
    if (!file) return;
    setState('uploading');
    setResult(null);
    setErrorMsg('');

    const form = new FormData();
    form.append('file', file);

    try {
      const res = await fetch((import.meta.env.VITE_API_URL || 'http://localhost:8000') + '/api/ingest', {
        method: 'POST',
        body: form,
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail ?? 'Ingestion failed');
      }
      setResult(data);
      setState('success');
    } catch (err: any) {
      setErrorMsg(err.message ?? 'Unknown error');
      setState('error');
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200 flex items-center justify-center p-6">
      <div className="w-full max-w-xl">
        <div className="mb-8 text-center">
          <div className="inline-flex items-center gap-2 text-cyan-400 mb-2">
            <UploadCloud size={28} />
            <span className="text-2xl font-bold tracking-tight">Add Document</span>
          </div>
          <p className="text-slate-400 text-sm">
            Upload a manual, SOP, maintenance log, or incident report.
            The system will ingest it and immediately re-scan for contradictions.
          </p>
        </div>

        {/* Drop Zone */}
        <div
          id="upload-drop-zone"
          onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
          onDragLeave={() => setDrag(false)}
          onDrop={handleDrop}
          onClick={() => inputRef.current?.click()}
          className={`
            border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-all duration-200
            ${drag ? 'border-cyan-400 bg-cyan-400/10' : 'border-slate-700 bg-slate-900 hover:border-slate-500'}
          `}
        >
          <input
            ref={inputRef}
            id="upload-file-input"
            type="file"
            accept={SUPPORTED.join(',')}
            className="hidden"
            onChange={(e) => handleFile(e.target.files?.[0] ?? null)}
          />
          {file ? (
            <div className="flex flex-col items-center gap-2">
              <FileText size={40} className="text-cyan-400" />
              <p className="font-semibold text-slate-200">{file.name}</p>
              <p className="text-sm text-slate-400">{(file.size / 1024).toFixed(1)} KB</p>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-2 text-slate-500">
              <UploadCloud size={40} />
              <p className="text-sm">Drag & drop a file here, or <span className="text-cyan-400 underline">click to browse</span></p>
              <p className="text-xs">{SUPPORTED.join(' · ')}</p>
            </div>
          )}
        </div>

        {/* Ingest Button */}
        <button
          id="ingest-submit-btn"
          onClick={handleIngest}
          disabled={!file || state === 'uploading'}
          className={`
            mt-4 w-full py-3 rounded-xl font-semibold text-sm flex items-center justify-center gap-2 transition-all
            ${!file || state === 'uploading'
              ? 'bg-slate-800 text-slate-500 cursor-not-allowed'
              : 'bg-cyan-500 hover:bg-cyan-400 text-slate-950 cursor-pointer'}
          `}
        >
          {state === 'uploading' ? (
            <><Loader2 size={16} className="animate-spin" /> Ingesting…</>
          ) : (
            <><UploadCloud size={16} /> Ingest Document</>
          )}
        </button>

        {/* Result */}
        {state === 'success' && result && (
          <div
            id="upload-success-banner"
            className="mt-4 p-4 rounded-xl bg-emerald-900/30 border border-emerald-700 flex items-start gap-3"
          >
            <CheckCircle size={20} className="text-emerald-400 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-emerald-300">Successfully Ingested</p>
              <p className="text-sm text-slate-300 mt-1">
                <span className="font-medium">{result.filename}</span> — {result.chunks_ingested} chunks stored.
              </p>
              <p className="text-sm text-amber-300 mt-1 font-medium">
                ⚠ {result.conflict_count} conflicts now known in the system.
              </p>
            </div>
          </div>
        )}

        {state === 'error' && (
          <div
            id="upload-error-banner"
            className="mt-4 p-4 rounded-xl bg-red-900/30 border border-red-700 flex items-start gap-3"
          >
            <AlertTriangle size={20} className="text-red-400 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-red-300">Ingestion Failed</p>
              <p className="text-sm text-slate-300 mt-1">{errorMsg}</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
