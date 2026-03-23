import React from 'react';
import { FileText, Scissors } from 'lucide-react';

const SplitPane = ({ file, pagesRange, setPagesRange }) => {
  return (
    <div className="w-full h-full flex flex-col bg-[#0c0c0e] p-8 items-center justify-center animate-in fade-in zoom-in-95 duration-300">
      <div className="max-w-xl w-full bg-zinc-900 border border-zinc-800 rounded-3xl p-8 relative overflow-hidden shadow-2xl">
        
        <div className="absolute top-0 right-0 w-64 h-64 bg-rose-500/5 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2 pointer-events-none"></div>

        <div className="flex flex-col items-center text-center space-y-6 relative z-10">
          
          <div className="relative">
             <div className="w-24 h-32 bg-zinc-950 rounded-xl border-2 border-zinc-800 flex flex-col items-center justify-center shadow-lg transform -rotate-6">
                <FileText size={32} className="text-zinc-600 mb-2" />
                <span className="text-[10px] text-zinc-600 font-bold uppercase tracking-widest">PDF</span>
             </div>
             <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-32 h-1 bg-rose-500/50 rotate-12 shadow-[0_0_15px_rgba(244,63,94,0.5)]"></div>
             <div className="absolute -bottom-4 -right-4 p-4 bg-rose-500 text-white rounded-full shadow-lg shadow-rose-900/50">
                <Scissors size={24} />
             </div>
          </div>

          <div className="space-y-2 mt-4">
            <h2 className="text-2xl font-bold text-white tracking-tight">Gotowy do cięcia</h2>
            <p className="text-zinc-400 text-sm break-all px-4">{file?.name}</p>
          </div>

          <div className="w-full pt-6 border-t border-zinc-800/50 text-left space-y-4">
             <label className="block">
                <span className="block text-xs font-bold text-zinc-500 uppercase tracking-wider mb-2">Zakres stron (opcjonalnie)</span>
                <input 
                    type="text" 
                    value={pagesRange}
                    onChange={(e) => setPagesRange(e.target.value)}
                    placeholder="np. 1-5, 8, 11-13" 
                    className="w-full bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3 text-white text-sm focus:outline-none focus:border-rose-500/50 focus:ring-1 focus:ring-rose-500/50 transition-all placeholder:text-zinc-700"
                />
             </label>
             <p className="text-[10px] text-zinc-500">Zostaw puste, aby podzielić na osobne strony, lub wpisz konkretne zakresy, by wydzielić z nich dokument.</p>
          </div>

        </div>
      </div>
    </div>
  );
};

export default SplitPane;