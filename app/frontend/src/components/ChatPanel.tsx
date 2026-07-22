import React, { useState, useRef, useEffect } from 'react';
import type { QueryResult, Conflict } from '../types/schemas';
import { LessonsLearned } from './LessonsLearned';
import { ConfidenceBreakdownPanel } from './ConfidenceBreakdownPanel';
import { RootCausePanel } from './RootCausePanel';
import { Send, FileText, Bot, User, AlertTriangle, Brain } from 'lucide-react';

interface Props { onConflictsDetected: (conflicts: Conflict[]) => void; }
interface Message { role: 'user' | 'assistant'; content: string; result?: QueryResult; error?: string; }

const SUGGESTIONS = [
  'What is the relief pressure for PSV-101?',
  'How often should HX-301 be cleaned?',
  'What are PUMP-203 maintenance requirements?',
  'Summarize all known equipment conflicts',
];

export const ChatPanel: React.FC<Props> = ({ onConflictsDetected }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [messages]);

  const handleSubmit = async (e?: React.FormEvent, overrideQuery?: string) => {
    if (e) e.preventDefault();
    const query = overrideQuery ?? input;
    if (!query.trim() || loading) return;
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: query }]);
    setLoading(true);
    try {
      const res = await fetch('http://localhost:8000/api/query', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: query }),
      });
      if (!res.ok) { const e = await res.json(); throw new Error(e.detail || 'API Error'); }
      const data: QueryResult = await res.json();
      setMessages(prev => [...prev, { role: 'assistant', content: data.answer, result: data }]);
      if (data.conflicts?.length) onConflictsDetected(data.conflicts);
    } catch (err: any) {
      setMessages(prev => [...prev, { role: 'assistant', content: '', error: err.message }]);
    } finally { setLoading(false); }
  };

  const confBadge = (confidence: number) => {
    const pct = Math.round(confidence * 100);
    const color = confidence >= 0.8 ? '#00e676' : confidence >= 0.5 ? '#ffa502' : '#ff4757';
    return (
      <span style={{ padding: '4px 12px', borderRadius: '999px', fontSize: '12px', fontWeight: 700, background: `${color}18`, color, border: `1px solid ${color}40` }}>
        {pct}% Confidence
      </span>
    );
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', width: '100%', background: 'var(--bg-base)' }}>

      {/* ── Message list ── */}
      <div ref={scrollRef} style={{ flex: 1, overflowY: 'auto', padding: '40px 48px', display: 'flex', flexDirection: 'column', gap: '28px' }}>

        {/* ── Empty / Hero state ── */}
        {messages.length === 0 && (
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '36px', paddingBottom: '80px' }}>
            {/* Glowing orb */}
            <div style={{
              width: '96px', height: '96px', borderRadius: '50%',
              background: 'radial-gradient(circle at 38% 35%, rgba(0,230,118,0.35) 0%, rgba(0,230,118,0.05) 65%, transparent 100%)',
              border: '1px solid rgba(0,230,118,0.3)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              boxShadow: '0 0 60px rgba(0,230,118,0.18), inset 0 0 30px rgba(0,230,118,0.08)',
            }}>
              <Brain size={40} color="var(--accent)" />
            </div>

            <div style={{ textAlign: 'center' }}>
              <h1 style={{
                fontFamily: 'var(--font-display)', fontStyle: 'italic',
                fontSize: '56px', fontWeight: 700,
                color: 'var(--text-primary)', lineHeight: 1.0, marginBottom: '14px',
              }}>
                Ask it.
              </h1>
              <p style={{ color: 'var(--text-muted)', fontSize: '17px', maxWidth: '480px', lineHeight: 1.65, margin: '0 auto' }}>
                Query maintenance manuals, SOPs, and incident reports.
                <br />Sources cited. Contradictions flagged.
              </p>
            </div>

            {/* Suggestion chips */}
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px', justifyContent: 'center', maxWidth: '640px' }}>
              {SUGGESTIONS.map(s => (
                <button key={s} onClick={() => handleSubmit(undefined, s)} style={{
                  padding: '10px 20px', borderRadius: '999px', fontSize: '14px', fontWeight: 500,
                  background: 'var(--bg-card)', border: '1px solid var(--border-default)',
                  color: 'var(--text-secondary)', cursor: 'pointer',
                  transition: 'all 0.15s ease', fontFamily: 'var(--font-body)',
                }}
                onMouseEnter={e => { const b = e.target as HTMLButtonElement; b.style.borderColor = 'var(--accent)'; b.style.color = 'var(--accent)'; b.style.background = 'var(--accent-dim)'; }}
                onMouseLeave={e => { const b = e.target as HTMLButtonElement; b.style.borderColor = 'var(--border-default)'; b.style.color = 'var(--text-secondary)'; b.style.background = 'var(--bg-card)'; }}>
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* ── Messages ── */}
        {messages.map((msg, idx) => (
          <div key={idx} className="animate-fade-in-up" style={{ display: 'flex', gap: '16px', justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start', width: '100%' }}>

            {/* Bot avatar */}
            {msg.role === 'assistant' && (
              <div style={{ width: '40px', height: '40px', borderRadius: '10px', flexShrink: 0, background: 'var(--accent-dim)', border: '1px solid rgba(0,230,118,0.25)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Bot size={20} color="var(--accent)" />
              </div>
            )}

            {/* Bubble */}
            <div style={{
              maxWidth: '72%',
              padding: msg.role === 'user' ? '14px 20px' : '20px 24px',
              borderRadius: msg.role === 'user' ? '22px 4px 22px 22px' : '4px 22px 22px 22px',
              background: msg.role === 'user' ? 'var(--accent-dark)' : 'var(--bg-card)',
              border: msg.role === 'user' ? 'none' : '1px solid var(--border-subtle)',
              color: msg.role === 'user' ? '#000' : 'var(--text-primary)',
              fontWeight: msg.role === 'user' ? 600 : 400,
              fontSize: '15px', lineHeight: 1.7,
              boxShadow: msg.role === 'user' ? 'none' : 'var(--shadow-card)',
            }}>
              {msg.role === 'user' ? (
                <p>{msg.content}</p>
              ) : msg.error ? (
                <p style={{ color: 'var(--danger)', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '15px' }}>
                  <AlertTriangle size={16} /> {msg.error}
                </p>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  <p style={{ whiteSpace: 'pre-wrap', fontSize: '15px' }}>{msg.content}</p>

                  {msg.result && (
                    <div style={{ paddingTop: '14px', borderTop: '1px solid var(--border-subtle)', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        {confBadge(msg.result.confidence)}
                        <span style={{ color: 'var(--text-muted)', fontSize: '12px' }}>
                          {msg.result.citations.length} source{msg.result.citations.length !== 1 ? 's' : ''}
                        </span>
                      </div>
                      {msg.result.confidence_breakdown && (
                        <ConfidenceBreakdownPanel breakdown={msg.result.confidence_breakdown} />
                      )}
                    </div>
                  )}

                  {/* Citations */}
                  {msg.result?.citations && msg.result.citations.length > 0 && (
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: '10px' }}>
                      {msg.result.citations.map((cit, cIdx) => (
                        <div key={cIdx} style={{ background: 'var(--bg-surface)', padding: '12px 14px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)', fontSize: '12px' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--text-muted)', marginBottom: '6px' }}>
                            <FileText size={12} />
                            <span style={{ fontFamily: 'monospace', fontSize: '12px', fontWeight: 600, color: 'var(--accent)', opacity: 0.85, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                              {cit.source_file}
                            </span>
                            {cit.page_or_row && <span style={{ opacity: 0.55, flexShrink: 0 }}>· {cit.page_or_row}</span>}
                          </div>
                          <p style={{ color: 'var(--text-muted)', fontStyle: 'italic', fontSize: '12px', overflow: 'hidden', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical' }}>
                            "{cit.excerpt}"
                          </p>
                        </div>
                      ))}
                    </div>
                  )}

                  <LessonsLearned incidents={msg.result?.lessons_learned || []} />
                  {msg.result?.root_cause_chain && <RootCausePanel chain={msg.result.root_cause_chain} />}
                </div>
              )}
            </div>

            {/* User avatar */}
            {msg.role === 'user' && (
              <div style={{ width: '40px', height: '40px', borderRadius: '10px', flexShrink: 0, background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <User size={20} color="var(--text-muted)" />
              </div>
            )}
          </div>
        ))}

        {/* ── Typing indicator ── */}
        {loading && (
          <div style={{ display: 'flex', gap: '16px' }}>
            <div style={{ width: '40px', height: '40px', borderRadius: '10px', flexShrink: 0, background: 'var(--accent-dim)', border: '1px solid rgba(0,230,118,0.25)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Bot size={20} color="var(--accent)" />
            </div>
            <div style={{ padding: '20px 24px', borderRadius: '4px 22px 22px 22px', background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', display: 'flex', alignItems: 'center', gap: '8px' }}>
              {[0, 0.22, 0.44].map((d, i) => (
                <div key={i} style={{ width: '9px', height: '9px', borderRadius: '50%', background: 'var(--accent)', animation: `pulse-green 1.2s ease-in-out ${d}s infinite` }} />
              ))}
            </div>
          </div>
        )}
      </div>

      {/* ── Input bar ── */}
      <div style={{
        padding: '20px 48px 28px', flexShrink: 0,
        background: 'rgba(8,12,24,0.95)',
        borderTop: '1px solid var(--border-subtle)',
        backdropFilter: 'blur(20px)',
      }}>
        <form onSubmit={handleSubmit} style={{ position: 'relative', maxWidth: '860px', margin: '0 auto' }}>
          <input
            type="text" value={input}
            onChange={e => setInput(e.target.value)}
            disabled={loading}
            placeholder="Ask about equipment, SOPs, or maintenance records…"
            style={{
              width: '100%', background: 'var(--bg-card)',
              border: '1px solid var(--border-default)',
              borderRadius: '999px', padding: '16px 62px 16px 26px',
              fontSize: '15px', color: 'var(--text-primary)',
              outline: 'none', fontFamily: 'var(--font-body)',
              transition: 'border-color 0.2s, box-shadow 0.2s',
            }}
            onFocus={e => { e.target.style.borderColor = 'var(--accent)'; e.target.style.boxShadow = '0 0 0 4px rgba(0,230,118,0.1)'; }}
            onBlur={e => { e.target.style.borderColor = 'var(--border-default)'; e.target.style.boxShadow = 'none'; }}
          />
          <button type="submit" disabled={loading || !input.trim()} style={{
            position: 'absolute', right: '8px', top: '8px', bottom: '8px',
            aspectRatio: '1', background: input.trim() && !loading ? 'var(--accent)' : 'var(--bg-surface)',
            border: 'none', borderRadius: '50%', cursor: input.trim() && !loading ? 'pointer' : 'default',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            transition: 'all 0.2s ease',
          }}>
            <Send size={17} color={input.trim() && !loading ? '#000' : 'var(--text-muted)'} />
          </button>
        </form>
        <p style={{ textAlign: 'center', marginTop: '8px', fontSize: '11px', color: 'var(--text-muted)', opacity: 0.7 }}>
          Answers grounded in ingested documents · Sources always cited
        </p>
      </div>
    </div>
  );
};
