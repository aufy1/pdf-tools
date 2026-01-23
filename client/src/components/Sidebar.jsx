import React from 'react';
import { FileText, Clock, ChevronRight } from 'lucide-react';

const Sidebar = () => {
  // Mock data
  const history = [
    { id: 1, name: 'to nie dziala.pdf', date: '10 min temu', status: 'done' },
    { id: 2, name: 'jeszcze.pdf', date: '2 godz. temu', status: 'done' },
    { id: 3, name: 'ale będzie.pdf', date: 'Wczoraj', status: 'error' },
  ];

  return (
    <aside className="w-64 bg-zinc-950 border-r border-zinc-800 flex flex-col shrink-0 z-20">
      <div className="p-4 border-b border-zinc-800">
        <h3 className="text-xs font-bold text-zinc-500 uppercase tracking-wider flex items-center gap-2">
            <Clock size={12}/> Ostatnie pliki
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
                    <p className="text-[10px] text-zinc-600">{file.date}</p>
                </div>
                <ChevronRight size={14} className="ml-auto text-zinc-700 opacity-0 group-hover:opacity-100 transition-opacity"/>
            </div>
        ))}
      </div>
    </aside>
  );
};

export default Sidebar;