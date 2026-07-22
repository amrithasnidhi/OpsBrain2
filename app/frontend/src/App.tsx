import { useState } from 'react';
import { ChatPanel } from './components/ChatPanel';
import { ConflictsPanel } from './components/ConflictsPanel';
import { UploadForm } from './components/UploadForm';
import { KnowledgeCaptureForm } from './components/KnowledgeCaptureForm';
import type { Conflict } from './types/schemas';
import { MessageSquare, UploadCloud, Brain } from 'lucide-react';

type Page = 'chat' | 'upload' | 'capture';

const NAV_ITEMS: { id: Page; label: string; icon: React.ReactNode }[] = [
  { id: 'chat',    label: 'Ask AI',          icon: <MessageSquare size={15} /> },
  { id: 'upload',  label: 'Add Document',    icon: <UploadCloud size={15} /> },
  { id: 'capture', label: 'Capture Knowledge', icon: <Brain size={15} /> },
];

function App() {
  const [page, setPage] = useState<Page>('chat');
  const [activeConflicts, setActiveConflicts] = useState<Conflict[]>([]);

  return (
    <div className="flex flex-col h-screen bg-slate-950 text-slate-200 overflow-hidden font-sans">
      {/* Top Nav Bar */}
      <nav className="flex-shrink-0 flex items-center gap-1 px-4 py-2 bg-slate-900 border-b border-slate-800 z-10">
        <span className="text-sm font-bold text-cyan-400 mr-4 tracking-tight">OpsBrain²</span>
        {NAV_ITEMS.map(item => (
          <button
            key={item.id}
            id={`nav-${item.id}`}
            onClick={() => setPage(item.id)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
              page === item.id
                ? 'bg-slate-700 text-slate-100'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
            }`}
          >
            {item.icon}
            {item.label}
          </button>
        ))}
      </nav>

      {/* Page Content */}
      <div className="flex flex-1 min-h-0">
        {page === 'chat' && (
          <>
            <main className="flex-1 min-w-0">
              <ChatPanel onConflictsDetected={setActiveConflicts} />
            </main>
            <aside className="w-1/3 min-w-[400px] border-l border-slate-800 bg-slate-900 flex-shrink-0">
              <ConflictsPanel activeConflicts={activeConflicts} />
            </aside>
          </>
        )}
        {page === 'upload'  && <UploadForm />}
        {page === 'capture' && <KnowledgeCaptureForm />}
      </div>
    </div>
  );
}

export default App;
