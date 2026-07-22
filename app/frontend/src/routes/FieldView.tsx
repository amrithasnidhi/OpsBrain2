import React, { useState, useEffect, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Mic, Send, AlertTriangle, Loader2 } from 'lucide-react';
import type { QueryResult, Conflict } from '../types/schemas';

// Web Speech API Types
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

  // Feature detection for Speech API
  const supportsSpeech = !!SpeechRecognition;

  useEffect(() => {
    if (tag) {
      // Fetch conflicts to see if this tag has any
      fetch((import.meta.env.VITE_API_URL || 'http://localhost:8000') + '/api/conflicts')
        .then(res => res.json())
        .then((data: Conflict[]) => {
          const matching = data.filter(c => c.entity === tag);
          setTagConflicts(matching);
        })
        .catch(console.error);
    }

    if (supportsSpeech) {
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.lang = 'en-US';

      recognition.onstart = () => setIsListening(true);
      recognition.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        setInput(prev => prev ? `${prev} ${transcript}` : transcript);
        setIsListening(false);
      };
      recognition.onerror = () => setIsListening(false);
      recognition.onend = () => setIsListening(false);
      
      recognitionRef.current = recognition;
    }
  }, [tag, supportsSpeech]);

  const toggleListen = () => {
    if (isListening) {
      recognitionRef.current?.stop();
    } else {
      recognitionRef.current?.start();
    }
  };

  const handleSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!input.trim() || loading) return;

    setLoading(true);
    setResult(null);

    try {
      const res = await fetch((import.meta.env.VITE_API_URL || 'http://localhost:8000') + '/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: input })
      });
      
      if (!res.ok) throw new Error('API Error');
      const data: QueryResult = await res.json();
      setResult(data);
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-slate-950 text-slate-200 overflow-hidden font-sans sm:max-w-md mx-auto border-x border-slate-900 shadow-2xl">
      {/* Header Banner */}
      <div className="bg-slate-900 p-4 border-b border-slate-800 text-center flex-shrink-0">
        <h1 className="text-xl font-bold text-white">Field View</h1>
        {tag && <p className="text-blue-400 text-sm font-mono mt-1">{tag}</p>}
      </div>

      {/* Warnings Banner */}
      {tagConflicts.length > 0 && (
        <div className="bg-red-500/20 border-b border-red-500/50 p-4 flex items-center gap-3 text-red-400 flex-shrink-0">
          <AlertTriangle className="shrink-0" size={24} />
          <span className="font-bold text-lg">⚠️ {tagConflicts.length} known conflicts for this equipment</span>
        </div>
      )}

      {/* Scrollable Answer Area */}
      <div className="flex-1 overflow-y-auto p-4 flex flex-col justify-end space-y-4">
        {result && (
          <div className="bg-slate-900 p-6 rounded-2xl border border-slate-800 shadow-lg mb-4">
            <p className="text-lg leading-relaxed whitespace-pre-wrap">{result.answer}</p>
          </div>
        )}
        {loading && (
          <div className="bg-slate-900 p-6 rounded-2xl border border-slate-800 shadow-lg mb-4 flex items-center justify-center text-blue-400">
            <Loader2 size={32} className="animate-spin" />
          </div>
        )}
      </div>

      {/* Input Area - Large Touch Targets */}
      <div className="p-4 bg-slate-900 border-t border-slate-800 flex-shrink-0">
        <form onSubmit={handleSubmit} className="flex gap-2">
          {supportsSpeech && (
            <button 
              type="button" 
              onClick={toggleListen}
              className={`p-4 rounded-xl shrink-0 transition-colors ${isListening ? 'bg-red-600 animate-pulse text-white' : 'bg-slate-800 text-slate-400 hover:bg-slate-700'}`}
              aria-label="Voice Input"
            >
              <Mic size={28} />
            </button>
          )}
          
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask or speak..."
            className="flex-1 bg-slate-950 border border-slate-700 rounded-xl px-4 text-lg focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
          />
          
          <button 
            type="submit" 
            disabled={loading || !input.trim()}
            className="bg-blue-600 hover:bg-blue-500 disabled:bg-slate-800 p-4 rounded-xl shrink-0 text-white transition-colors"
            aria-label="Send"
          >
            <Send size={28} />
          </button>
        </form>
      </div>
    </div>
  );
}
