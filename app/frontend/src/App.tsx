/**
 * App.tsx - Thin shell with router.
 * Each person appends one NAV_ITEMS entry + one Route.
 */
import { BrowserRouter, Routes, Route, NavLink } from "react-router-dom";
import ChatView from "./routes/ChatView";
import StalenessDashboard from "./routes/StalenessDashboard";
import FieldView from "./routes/FieldView";
import GraphView from "./routes/GraphView";
import CompliancePanel from "./routes/CompliancePanel";

interface NavItem {
  path: string;
  label: string;
}

const NAV_ITEMS: NavItem[] = [
  { path: "/", label: "Chat" },
  // --- Person A (Risk/Compliance) ---
  { path: "/compliance", label: "Compliance" },
  // --- Person B (Ingestion/Reasoning) adds here ---
  // { path: "/reasoning", label: "Root Cause" },
  // --- Person C (Dashboards/UX) adds here ---
  { path: "/staleness", label: "Maintenance Health" },
  { path: "/field", label: "Field View" },
  { path: "/graph", label: "Knowledge Graph" },
];

export default function App() {
  return (
    <BrowserRouter>
      <div className="h-screen flex flex-col bg-slate-950">
        {/* Navigation - only show if more than one route */}
        {NAV_ITEMS.length > 1 && (
          <nav className="bg-slate-900 border-b border-slate-800 px-4 py-2 flex gap-4">
            {NAV_ITEMS.map(item => (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  `px-3 py-1 rounded text-sm font-medium transition-colors ${
                    isActive
                      ? "bg-blue-600 text-white"
                      : "text-slate-400 hover:text-slate-200 hover:bg-slate-800"
                  }`
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
        )}

        {/* Routes */}
        <div className="flex-1 overflow-hidden">
          <Routes>
            <Route path="/" element={<ChatView />} />
            {/* --- Person A (Risk/Compliance) --- */}
            <Route path="/compliance" element={<CompliancePanel />} />
            {/* --- Person B (Ingestion/Reasoning) adds here --- */}
            {/* <Route path="/reasoning" element={<ReasoningView />} /> */}
            {/* --- Person C adds Route here --- */}
            <Route path="/staleness" element={<StalenessDashboard />} />
            <Route path="/field" element={<FieldView />} />
            <Route path="/graph" element={<GraphView />} />
          </Routes>
        </div>
      </div>
    </BrowserRouter>
  );
}
