import React, { useState, useRef, useEffect } from 'react';
import type { QueryResult, Conflict } from '../types/schemas';
import { LessonsLearned } from './LessonsLearned';
import { Send, FileText, ChevronDown, ChevronUp, Bot, User, AlertTriangle } from 'lucide-react';

interface Props {
  onConflictsDetected: (conflicts: Conflict[]) => void;
}

interface Message {
  role: 'user' | 'assistant';
  content: string;
  result?: QueryResult;
  error?: string;
}

export const ChatPanel: React.FC<Props> = ({ onConflictsDetected }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const query = input;
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: query }]);
    setLoading(true);

    try {
      const res = await fetch('http://localhost:8000/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: query })
      });
      
      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || 'API Error');
      }

      const data: QueryResult = await res.json();
      setMessages(prev => [...prev, { role: 'assistant', content: data.answer, result: data }]);
      
      if (data.conflicts && data.conflicts.length > 0) {
        onConflictsDetected(data.conflicts);
      }
    } catch (err: any) {
      setMessages(prev => [...prev, { role: 'assistant', content: '', error: err.message }]);
    } finally {
      setLoading(false);
    }
  };

  const renderConfidenceBadge = (confidence: number) => {
    let colorClass = 'bg-red-500/20 text-red-400 border-red-500/30';
    if (confidence >= 0.8) colorClass = 'bg-green-500/20 text-green-400 border-green-500/30';
    else if (confidence >= 0.5) colorClass = 'bg-amber-500/20 text-amber-400 border-amber-500/30';

    return (
      <div className={`px-2 py-0.5 rounded text-xs font-bold border ${colorClass}`}>
        {Math.round(confidence * 100)}% Confidence
      </div>
    );
  };

  return (
    <div className="flex flex-col h-full bg-slate-950 text-slate-200">
      <div className="flex-1 overflow-y-auto p-6 space-y-6" ref={scrollRef}>
        {messages.length === 0 && (
          <div className="h-full flex flex-col items-center justify-center text-slate-500 space-y-4">
            <div className="w-16 h-16 bg-slate-900 rounded-full flex items-center justify-center border border-slate-800">
              <Bot size={32} className="text-blue-500" />
            </div>
            <h2 className="text-xl font-bold text-slate-300">Industrial Knowledge Brain</h2>
            <p className="max-w-md text-center">Ask a question about maintenance manuals, equipment status, or SOPs. I will cite my sources and flag any contradictions.</p>
          </div>
        )}

        {messages.map((msg, idx) => (
          <div key={idx} className={`flex gap-4 ${msg.role === 'user' ? 'justify-end' : ''}`}>
            {msg.role === 'assistant' && (
              <div className="w-8 h-8 rounded bg-blue-900/50 flex items-center justify-center shrink-0 border border-blue-500/30">
                <Bot size={18} className="text-blue-400" />
              </div>
            )}
            
            <div className={`max-w-[80%] rounded-2xl p-4 ${msg.role === 'user' ? 'bg-blue-600 text-white rounded-tr-sm' : 'bg-slate-900 border border-slate-800 rounded-tl-sm shadow-xl'}`}>
              {msg.role === 'user' ? (
                <p>{msg.content}</p>
              ) : msg.error ? (
                <p className="text-red-400 flex items-center gap-2"><AlertTriangle size={16} /> Error: {msg.error}</p>
              ) : (
                <div className="space-y-4">
                  <div className="flex justify-between items-start gap-4">
                    <p className="leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                  </div>
                  
                  {msg.result && (
                    <div className="pt-3 border-t border-slate-800 flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        {renderConfidenceBadge(msg.result.confidence)}
                        <span className="text-xs text-slate-500">{msg.result.citations.length} Citations</span>
                      </div>
                    </div>
                  )}

                  {msg.result?.citations && msg.result.citations.length > 0 && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2 mt-4">
                      {msg.result.citations.map((cit, cIdx) => (
                        <div key={cIdx} className="bg-slate-950 p-3 rounded border border-slate-800/50 text-sm">
                          <div className="flex items-center gap-2 text-slate-400 mb-1">
                            <FileText size={14} />
                            <span className="font-mono text-xs font-semibold">{cit.source_file}</span>
                            {cit.page_or_row && <span className="text-xs">({cit.page_or_row})</span>}
                          </div>
                          <p className="text-slate-500 text-xs italic line-clamp-3 hover:line-clamp-none transition-all">"{cit.excerpt}"</p>
                        </div>
                      ))}
                    </div>
                  )}

                  <LessonsLearned incidents={msg.result?.lessons_learned || []} />
                </div>
              )}
            </div>

            {msg.role === 'user' && (
              <div className="w-8 h-8 rounded bg-slate-800 flex items-center justify-center shrink-0">
                <User size={18} className="text-slate-400" />
              </div>
            )}
          </div>
        ))}
        {loading && (
          <div className="flex gap-4">
             <div className="w-8 h-8 rounded bg-blue-900/50 flex items-center justify-center shrink-0 border border-blue-500/30 animate-pulse">
                <Bot size={18} className="text-blue-400" />
              </div>
              <div className="bg-slate-900 border border-slate-800 rounded-2xl rounded-tl-sm p-4 text-slate-400 animate-pulse flex items-center gap-2">
                <div className="w-2 h-2 bg-slate-500 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-slate-500 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                <div className="w-2 h-2 bg-slate-500 rounded-full animate-bounce" style={{animationDelay: '0.4s'}}></div>
              </div>
          </div>
        )}
      </div>

      <div className="p-4 bg-slate-950 border-t border-slate-900">
        <form onSubmit={handleSubmit} className="relative max-w-4xl mx-auto">
          <input
            type="text"
            value={input}
            onChange={e => setInput(e.target.value)}
            disabled={loading}
            placeholder="Ask about equipment or procedures..."
            className="w-full bg-slate-900 border border-slate-700 rounded-full py-4 pl-6 pr-14 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all placeholder:text-slate-500"
          />
          <button 
            type="submit" 
            disabled={loading || !input.trim()}
            className="absolute right-2 top-2 bottom-2 aspect-square bg-blue-600 hover:bg-blue-500 disabled:bg-slate-800 rounded-full flex items-center justify-center transition-colors"
          >
            <Send size={18} className={loading || !input.trim() ? 'text-slate-500' : 'text-white'} />
          </button>
        </form>
      </div>
    </div>
  );
};
