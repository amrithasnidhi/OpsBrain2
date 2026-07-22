import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom';
import { useState } from 'react';
import { ChatPanel } from './components/ChatPanel';
import { ConflictsPanel } from './components/ConflictsPanel';
import { UploadForm } from './components/UploadForm';
import { KnowledgeCaptureForm } from './components/KnowledgeCaptureForm';
import CompliancePanel from './routes/CompliancePanel';
import StalenessDashboard from './routes/StalenessDashboard';
import FieldView from './routes/FieldView';
import GraphView from './routes/GraphView';
import type { Conflict } from './types/schemas';
import {
  MessageSquare,
  UploadCloud,
  Brain,
  Shield,
  Clock,
  Smartphone,
  GitBranch
} from 'lucide-react';

interface NavItem {
  path: string;
  label: string;
  icon: React.ReactNode;
}

const NAV_ITEMS: NavItem[] = [
  { path: '/',           label: 'Ask AI',           icon: <MessageSquare size={15} /> },
  { path: '/upload',     label: 'Add Document',     icon: <UploadCloud size={15} /> },
  { path: '/capture',    label: 'Capture Knowledge', icon: <Brain size={15} /> },
  { path: '/compliance', label: 'Compliance',       icon: <Shield size={15} /> },
  { path: '/staleness',  label: 'Maintenance Health', icon: <Clock size={15} /> },
  { path: '/field',      label: 'Field View',       icon: <Smartphone size={15} /> },
  { path: '/graph',      label: 'Knowledge Graph',  icon: <GitBranch size={15} /> },
];

// Chat view with conflicts sidebar
function ChatView() {
  const [activeConflicts, setActiveConflicts] = useState<Conflict[]>([]);

  return (
    <div className="flex flex-1 min-h-0">
      <main className="flex-1 min-w-0">
        <ChatPanel onConflictsDetected={setActiveConflicts} />
      </main>
      <aside className="w-1/3 min-w-[400px] border-l border-slate-800 bg-slate-900 flex-shrink-0">
        <ConflictsPanel activeConflicts={activeConflicts} />
      </aside>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <div className="flex flex-col h-screen bg-slate-950 text-slate-200 overflow-hidden font-sans">
        {/* Top Nav Bar */}
        <nav className="flex-shrink-0 flex items-center gap-1 px-4 py-2 bg-slate-900 border-b border-slate-800 z-10 overflow-x-auto">
          <span className="text-sm font-bold text-cyan-400 mr-4 tracking-tight whitespace-nowrap">OpsBrain²</span>
          {NAV_ITEMS.map(item => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-all whitespace-nowrap ${
                  isActive
                    ? 'bg-slate-700 text-slate-100'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
                }`
              }
            >
              {item.icon}
              {item.label}
            </NavLink>
          ))}
        </nav>

        {/* Page Content */}
        <div className="flex flex-1 min-h-0">
          <Routes>
            <Route path="/" element={<ChatView />} />
            <Route path="/upload" element={<UploadForm />} />
            <Route path="/capture" element={<KnowledgeCaptureForm />} />
            <Route path="/compliance" element={<CompliancePanel />} />
            <Route path="/staleness" element={<StalenessDashboard />} />
            <Route path="/field" element={<FieldView />} />
            <Route path="/graph" element={<GraphView />} />
          </Routes>
        </div>
      </div>
    </BrowserRouter>
  );
}

export default App;
