import React from 'react';
import { Languages, Combine, Scissors, Clock, ChevronRight, FileText, FileType } from 'lucide-react';

const Sidebar = ({ activeTool, setActiveTool, onReset }) => {
  // Mock data historii
  const history = [
    { id: 1, name: 'raport_Q3.pdf', action: 'Tłumaczenie', status: 'done' },
    { id: 2, name: 'faktury_merge.pdf', action: 'Łączenie', status: 'done' },
  ];

  const tools = [
    { id: 'translate', icon: Languages, label: 'Tłumacz (AI)' },
    { id: 'convert', icon: FileType, label: 'Konwertuj (DOCX)' },
    { id: 'merge', icon: Combine, label: 'Łącz PDF' },
    { id: 'split', icon: Scissors, label: 'Dziel PDF' },
  ];

  const handleToolChange = (toolId) => {
      setActiveTool(toolId);
      onReset(); // Czyścimy obecny widok przy zmianie narzędzia
  };

  return (
    <aside className="w-64 bg-zinc-950 border-r border-zinc-800 flex flex-col shrink-0 z-20">
      
      {/* MENU NARZĘDZI */}
      <div className="p-4 border-b border-zinc-800">
        <h3 className="text-xs font-bold text-zinc-500 uppercase tracking-wider mb-3">Narzędzia</h3>
        <div className="space-y-1">
            {tools.map(tool => {
                const Icon = tool.icon;
                const isActive = activeTool === tool.id;
                return (
                    <button 
                        key={tool.id}
                        onClick={() => handleToolChange(tool.id)}
                        className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-all text-sm font-medium
                        ${isActive ? 'bg-indigo-600/10 text-indigo-400 border border-indigo-500/20' : 'text-zinc-400 hover:bg-zinc-900 hover:text-zinc-200 border border-transparent'}`}
                    >
                        <Icon size={18} />
                        {tool.label}
                    </button>
                )
            })}
        </div>
      </div>

      {/* HISTORIA */}
      <div className="p-4 border-b border-zinc-800 flex-shrink-0">
        <h3 className="text-xs font-bold text-zinc-500 uppercase tracking-wider flex items-center gap-2">
            <Clock size={12}/> Ostatnie akcje
        </h3>
      </div>
      
      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        {history.map(file => (
            <div key={file.id} className="group flex items-center gap-3 p-3 rounded-xl cursor-pointer hover:bg-zinc-900 transition-colors border border-transparent hover:border-zinc-800">
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${file.status === 'done' ? 'bg-indigo-500/10 text-indigo-500' : 'bg-red-500/10 text-red-500'}`}>
                    <FileText size={16} />
                </div>
                <div className="overflow-hidden">
                    <p className="text-sm text-zinc-300 font-medium truncate">{file.name}</p>
                    <p className="text-[10px] text-zinc-600">{file.action}</p>
                </div>
                <ChevronRight size={14} className="ml-auto text-zinc-700 opacity-0 group-hover:opacity-100 transition-opacity"/>
            </div>
        ))}
      </div>
    </aside>
  );
};

export default Sidebar;