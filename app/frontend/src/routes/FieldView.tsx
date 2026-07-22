import React, { useState, useEffect, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Mic, Send, AlertTriangle, Loader2, Zap } from 'lucide-react';
import type { QueryResult, Conflict } from '../types/schemas';

const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

export default function FieldView() {
  const [searchParams] = useSearchParams();
  const tag = searchParams.get('tag');

  const [input, setInput] = useState(tag ? `What is the status of ${tag}?` : '');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<QueryResult | null>(null);
  const [tagConflicts, setTagConflicts] = useState<Conflict[]>([]);
  const [isListening, setIsListening] = useState(false);
  const recognitionRef = useRef<any>(null);
  const supportsSpeech = !!SpeechRecognition;

  useEffect(() => {
    if (tag) {
      fetch('http://localhost:8000/api/conflicts')
        .then(r => r.json())
        .then((d: Conflict[]) => setTagConflicts(d.filter(c => c.entity === tag)))
        .catch(console.error);
    }
    if (supportsSpeech) {
      const rec = new SpeechRecognition();
      rec.continuous = false; rec.interimResults = false; rec.lang = 'en-US';
      rec.onstart = () => setIsListening(true);
      rec.onresult = (e: any) => { setInput(prev => prev ? `${prev} ${e.results[0][0].transcript}` : e.results[0][0].transcript); setIsListening(false); };
      rec.onerror = () => setIsListening(false);
      rec.onend = () => setIsListening(false);
      recognitionRef.current = rec;
    }
  }, [tag, supportsSpeech]);

  const handleSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!input.trim() || loading) return;
    setLoading(true); setResult(null);
    try {
      const res = await fetch('http://localhost:8000/api/query', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: input }),
      });
      if (!res.ok) throw new Error('API Error');
      setResult(await res.json());
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  };

  const conf = result?.confidence ?? 0;
  const confColor = conf >= 0.8 ? 'var(--accent)' : conf >= 0.5 ? 'var(--warning)' : 'var(--danger)';

  return (
    <div style={{
      height: '100%', display: 'flex', flexDirection: 'column',
      background: 'var(--bg-base)', maxWidth: '480px', margin: '0 auto',
      borderLeft: '1px solid var(--border-subtle)', borderRight: '1px solid var(--border-subtle)',
    }}>
      {/* Header */}
      <div style={{
        padding: '20px 20px 16px', flexShrink: 0,
        background: 'var(--bg-surface)', borderBottom: '1px solid var(--border-subtle)',
      }}>
        <p style={{ fontSize: '10px', fontWeight: 700, letterSpacing: '0.14em', textTransform: 'uppercase', color: 'var(--accent)', marginBottom: '4px' }}>
          Field Mode
        </p>
        <h1 style={{ fontFamily: 'var(--font-display)', fontStyle: 'italic', fontSize: '22px', fontWeight: 700, color: 'var(--text-primary)' }}>
          {tag ?? 'Ask it.'}
        </h1>
        {tag && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '5px', marginTop: '4px' }}>
            <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'var(--accent)' }} />
            <span style={{ fontFamily: 'monospace', fontSize: '12px', color: 'var(--accent)' }}>{tag}</span>
          </div>
        )}
      </div>

      {/* Conflict banner */}
      {tagConflicts.length > 0 && (
        <div style={{
          padding: '12px 20px', flexShrink: 0,
          background: 'var(--danger-dim)', borderBottom: '1px solid rgba(255,71,87,0.25)',
          display: 'flex', alignItems: 'center', gap: '10px',
        }}>
          <AlertTriangle size={18} color="var(--danger)" />
          <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--danger)' }}>
            {tagConflicts.length} known conflict{tagConflicts.length !== 1 ? 's' : ''} for this equipment
          </span>
        </div>
      )}

      {/* Answer area */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '20px', display: 'flex', flexDirection: 'column', justifyContent: 'flex-end', gap: '12px' }}>
        {!result && !loading && (
          <div style={{ textAlign: 'center', color: 'var(--text-muted)', paddingBottom: '20px' }}>
            <Zap size={28} style={{ margin: '0 auto 10px', opacity: 0.35 }} />
            <p style={{ fontSize: '13px' }}>Ask a question or use your voice</p>
          </div>
        )}
        {loading && (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', color: 'var(--accent)' }}>
            <Loader2 size={20} style={{ animation: 'spin 1s linear infinite' }} />
            <span style={{ fontSize: '13px' }}>Searching knowledge base…</span>
          </div>
        )}
        {result && (
          <div className="animate-fade-in-up" style={{
            padding: '18px', background: 'var(--bg-card)',
            borderRadius: 'var(--radius-lg)', border: '1px solid var(--border-subtle)',
            boxShadow: 'var(--shadow-card)',
          }}>
            <p style={{ fontSize: '15px', lineHeight: 1.65, color: 'var(--text-primary)', whiteSpace: 'pre-wrap', marginBottom: '14px' }}>
              {result.answer}
            </p>
            <div style={{ paddingTop: '10px', borderTop: '1px solid var(--border-subtle)', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{
                padding: '3px 10px', borderRadius: '999px', fontSize: '11px', fontWeight: 700,
                background: `${confColor}18`, color: confColor, border: `1px solid ${confColor}40`,
              }}>
                {Math.round(conf * 100)}% Confidence
              </span>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{result.citations.length} source{result.citations.length !== 1 ? 's' : ''}</span>
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      <div style={{ padding: '14px 16px 20px', background: 'var(--bg-surface)', borderTop: '1px solid var(--border-subtle)', flexShrink: 0 }}>
        <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '8px' }}>
          {supportsSpeech && (
            <button type="button" onClick={() => isListening ? recognitionRef.current?.stop() : recognitionRef.current?.start()} style={{
              width: '48px', height: '48px', borderRadius: 'var(--radius-md)', flexShrink: 0,
              cursor: 'pointer',
              background: isListening ? 'var(--danger)' : 'var(--bg-card)',
              outline: `1px solid ${isListening ? 'var(--danger)' : 'var(--border-default)'}`,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              transition: 'all 0.15s ease',
              animation: isListening ? 'pulse-green 1.5s ease-in-out infinite' : 'none',
            }}>
              <Mic size={20} color={isListening ? '#fff' : 'var(--text-muted)'} />
            </button>
          )}
          <input
            type="text" value={input} onChange={e => setInput(e.target.value)}
            placeholder="Ask or speak…"
            style={{
              flex: 1, background: 'var(--bg-card)', border: '1px solid var(--border-default)',
              borderRadius: 'var(--radius-md)', padding: '12px 16px', fontSize: '14px',
              color: 'var(--text-primary)', outline: 'none', fontFamily: 'var(--font-body)',
              transition: 'border-color 0.2s',
            }}
            onFocus={e => e.target.style.borderColor = 'var(--accent)'}
            onBlur={e => e.target.style.borderColor = 'var(--border-default)'}
          />
          <button type="submit" disabled={loading || !input.trim()} style={{
            width: '48px', height: '48px', borderRadius: 'var(--radius-md)', flexShrink: 0,
            cursor: 'pointer',
            background: input.trim() && !loading ? 'var(--accent)' : 'var(--bg-card)',
            outline: `1px solid ${input.trim() && !loading ? 'transparent' : 'var(--border-default)'}`,
            display: 'flex', alignItems: 'center', justifyContent: 'center', transition: 'all 0.15s ease',
          }}>
            <Send size={18} color={input.trim() && !loading ? '#000' : 'var(--text-muted)'} />
          </button>
        </form>
      </div>
    </div>
  );
}
