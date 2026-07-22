import { useEffect, useState, useRef, useCallback } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import type { Conflict } from '../types/schemas';
import { AlertTriangle, X } from 'lucide-react';

export default function GraphView() {
  const [graphData, setGraphData] = useState<{nodes: any[], links: any[]}>({ nodes: [], links: [] });
  const [conflicts, setConflicts] = useState<Conflict[]>([]);
  const [selectedConflict, setSelectedConflict] = useState<Conflict | null>(null);
  const [dimensions, setDimensions] = useState({ width: window.innerWidth, height: window.innerHeight - 60 });
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Fetch graph data
    fetch((import.meta.env.VITE_API_URL || 'http://localhost:8000') + '/api/graph')
      .then(res => res.json())
      .then(data => setGraphData(data))
      .catch(console.error);

    // Fetch all conflicts to match when an edge is clicked
    fetch((import.meta.env.VITE_API_URL || 'http://localhost:8000') + '/api/conflicts')
      .then(res => res.json())
      .then(data => setConflicts(data))
      .catch(console.error);
      
    const handleResize = () => {
      if (containerRef.current) {
        setDimensions({
          width: containerRef.current.clientWidth,
          height: containerRef.current.clientHeight
        });
      }
    };
    
    window.addEventListener('resize', handleResize);
    // Initial size
    handleResize();
    
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const handleLinkClick = useCallback((link: any) => {
    // If it's a conflict edge (red)
    if (link.color === '#ef4444') {
      const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
      const targetId = typeof link.target === 'object' ? link.target.id : link.target;
      
      // Try to find the matching conflict.
      // Usually, conflict entity is one of the nodes (e.g. equipment tag)
      const matchedConflict = conflicts.find(c => 
        c.entity === sourceId || 
        c.entity === targetId ||
        c.source_a.doc_id === sourceId || 
        c.source_b?.doc_id === targetId ||
        c.source_a.doc_id === targetId || 
        c.source_b?.doc_id === sourceId
      );
      
      if (matchedConflict) {
        setSelectedConflict(matchedConflict);
      } else {
        // Fallback if we can't perfectly match
        setSelectedConflict({
          entity: `${sourceId} / ${targetId}`,
          parameter: "Unknown",
          source_a: { doc_id: "Unknown", source_file: "Unknown", excerpt: "" },
          source_b: { doc_id: "Unknown", source_file: "Unknown", excerpt: "" },
          value_a: "Unknown",
          value_b: "Unknown",
          explanation: `A conflict exists between ${sourceId} and ${targetId}.`,
          severity: "medium",
          risk_type: "direct_contradiction"
        });
      }
    }
  }, [conflicts]);

  return (
    <div className="flex h-full w-full bg-slate-950 relative overflow-hidden" ref={containerRef}>
      <ForceGraph2D
        width={dimensions.width}
        height={dimensions.height}
        graphData={graphData}
        nodeLabel="label"
        nodeColor="color"
        linkColor="color"
        linkWidth={(link: any) => link.color === '#ef4444' ? 3 : 1}
        onLinkClick={handleLinkClick}
        linkDirectionalArrowLength={3.5}
        linkDirectionalArrowRelPos={1}
      />
      
      {/* Legend */}
      <div className="absolute top-4 left-4 bg-slate-900/80 p-4 rounded-lg border border-slate-800 backdrop-blur-sm pointer-events-none">
        <h3 className="text-white font-semibold mb-2">Knowledge Graph</h3>
        <div className="flex items-center gap-2 text-sm text-slate-300 mb-1">
          <div className="w-3 h-3 rounded-full bg-blue-500"></div> Equipment
        </div>
        <div className="flex items-center gap-2 text-sm text-slate-300 mb-1">
          <div className="w-3 h-3 rounded-full bg-gray-400"></div> Documents
        </div>
        <div className="flex items-center gap-2 text-sm text-slate-300">
          <div className="w-4 h-0.5 bg-red-500"></div> Conflicts
        </div>
      </div>
      
      {/* Conflict Modal */}
      {selectedConflict && (
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-[500px] bg-slate-900 border border-slate-700 rounded-xl shadow-2xl z-50 flex flex-col">
          <div className="flex justify-between items-center p-4 border-b border-slate-800">
            <div className="flex items-center gap-2 text-red-400">
              <AlertTriangle size={20} />
              <h2 className="font-bold text-lg">Conflict Detail</h2>
            </div>
            <button onClick={() => setSelectedConflict(null)} className="text-slate-400 hover:text-white transition-colors">
              <X size={20} />
            </button>
          </div>
          
          <div className="p-6 text-slate-300 space-y-4">
            <div className="flex justify-between">
              <div>
                <span className="text-xs text-slate-500 block mb-1">Entity</span>
                <span className="font-mono text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded">{selectedConflict.entity}</span>
              </div>
              <div>
                <span className="text-xs text-slate-500 block mb-1">Parameter</span>
                <span className="font-mono text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded">{selectedConflict.parameter}</span>
              </div>
            </div>
            
            <div className="bg-slate-950 p-4 rounded-lg border border-slate-800 text-sm leading-relaxed">
              {selectedConflict.explanation}
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 border-l-2 border-l-red-500">
                <span className="text-xs text-slate-500 block mb-1">Value A</span>
                <span className="font-bold">{selectedConflict.value_a}</span>
              </div>
              <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 border-l-2 border-l-amber-500">
                <span className="text-xs text-slate-500 block mb-1">Value B</span>
                <span className="font-bold">{selectedConflict.value_b}</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
