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

const NAV_ITEMS = [
  { path: '/',           label: 'Ask AI',            icon: <MessageSquare size={14} /> },
  { path: '/upload',     label: 'Add Document',      icon: <UploadCloud size={14} /> },
  { path: '/capture',    label: 'Capture Knowledge', icon: <Brain size={14} /> },
  { path: '/compliance', label: 'Compliance',        icon: <Shield size={14} /> },
  { path: '/staleness',  label: 'Maintenance',       icon: <Clock size={14} /> },
  { path: '/field',      label: 'Field View',        icon: <Smartphone size={14} /> },
  { path: '/graph',      label: 'Knowledge Graph',   icon: <GitBranch size={14} /> },
];

function ChatView() {
  const [activeConflicts, setActiveConflicts] = useState<Conflict[]>([]);
  return (
    <div style={{ display: 'flex', flex: 1, minHeight: 0, width: '100%', height: '100%' }}>
      <main style={{ flex: 1, minWidth: 0, height: '100%', display: 'flex', flexDirection: 'column' }}>
        <ChatPanel onConflictsDetected={setActiveConflicts} />
      </main>
      <aside style={{ width: '340px', flexShrink: 0, borderLeft: '1px solid var(--border-subtle)', height: '100%', overflowY: 'auto' }}>
        <ConflictsPanel activeConflicts={activeConflicts} />
      </aside>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', background: 'var(--bg-base)', overflow: 'hidden' }}>
        {/* ── Top Navigation ── */}
        <nav style={{
          flexShrink: 0,
          display: 'flex',
          alignItems: 'center',
          gap: '4px',
          padding: '10px 20px',
          background: 'rgba(8, 12, 24, 0.95)',
          borderBottom: '1px solid var(--border-subtle)',
          backdropFilter: 'blur(20px)',
          zIndex: 50,
        }}>
          {/* Logo */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginRight: '20px' }}>
            <div style={{
              width: '28px', height: '28px',
              background: 'var(--accent)',
              borderRadius: '7px',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <span style={{ color: '#000', fontWeight: 800, fontSize: '13px', fontFamily: 'var(--font-body)' }}>O²</span>
            </div>
            <span style={{
              fontFamily: 'var(--font-body)',
              fontWeight: 700,
              fontSize: '15px',
              color: 'var(--text-primary)',
              letterSpacing: '-0.3px',
            }}>OpsBrain²</span>
          </div>

          {/* Nav Links */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '2px', overflowX: 'auto' }}>
            {NAV_ITEMS.map(item => (
              <NavLink
                key={item.path}
                to={item.path}
                end={item.path === '/'}
                style={({ isActive }) => ({
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '6px 12px',
                  borderRadius: '8px',
                  fontSize: '13px',
                  fontWeight: 500,
                  fontFamily: 'var(--font-body)',
                  textDecoration: 'none',
                  whiteSpace: 'nowrap',
                  transition: 'all 0.15s ease',
                  background: isActive ? 'var(--accent-dim)' : 'transparent',
                  color: isActive ? 'var(--accent)' : 'var(--text-secondary)',
                  border: isActive ? '1px solid rgba(0,230,118,0.2)' : '1px solid transparent',
                })}
              >
                {item.icon}
                {item.label}
              </NavLink>
            ))}
          </div>
        </nav>

        {/* ── Page Content ── */}
        <div style={{ display: 'flex', flex: 1, minHeight: 0, width: '100%' }}>
          <Routes>
            <Route path="/"           element={<div style={{ display: 'flex', width: '100%', height: '100%', minHeight: 0 }}><ChatView /></div>} />
            <Route path="/upload"     element={<div style={{ width: '100%', height: '100%', overflowY: 'auto' }}><UploadForm /></div>} />
            <Route path="/capture"    element={<div style={{ width: '100%', height: '100%', overflowY: 'auto' }}><KnowledgeCaptureForm /></div>} />
            <Route path="/compliance" element={<div style={{ width: '100%', height: '100%', overflowY: 'auto' }}><CompliancePanel /></div>} />
            <Route path="/staleness"  element={<div style={{ width: '100%', height: '100%', overflowY: 'auto' }}><StalenessDashboard /></div>} />
            <Route path="/field"      element={<div style={{ width: '100%', height: '100%', overflowY: 'auto' }}><FieldView /></div>} />
            <Route path="/graph"      element={<div style={{ width: '100%', height: '100%' }}><GraphView /></div>} />
          </Routes>
        </div>
      </div>
    </BrowserRouter>
  );
}
