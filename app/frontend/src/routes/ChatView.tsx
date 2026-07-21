import { useState } from 'react';
import { ChatPanel } from '../components/ChatPanel';
import { ConflictsPanel } from '../components/ConflictsPanel';
import type { Conflict } from '../types/schemas';

export default function ChatView() {
  const [activeConflicts, setActiveConflicts] = useState<Conflict[]>([]);

  return (
    <div className="flex h-full bg-slate-950 text-slate-200 overflow-hidden font-sans">
      <main className="flex-1 min-w-0">
        <ChatPanel onConflictsDetected={setActiveConflicts} />
      </main>
      <aside className="w-1/3 min-w-[400px] border-l border-slate-800 bg-slate-900 flex-shrink-0">
        <ConflictsPanel activeConflicts={activeConflicts} />
      </aside>
    </div>
  );
}
