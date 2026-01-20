import React from 'react';
import { Layers, Upload, Play, Download, Settings, Split, Maximize, Loader2 } from 'lucide-react';

const Header = ({ 
  onUploadClick, 
  onProcessClick, 
  processingStatus, 
  viewMode, 
  setViewMode,
  hasFile 
}) => {
  return (
    <header className="h-16 bg-zinc-950 border-b border-zinc-800 flex items-center justify-between px-6 shrink-0 shadow-sm z-30">
      
      {/* LOGO */}
      <div className="flex items-center gap-3">
        <div className="bg-indigo-500/10 p-2 rounded-lg border border-indigo-500/20">
            <Layers className="w-5 h-5 text-indigo-500" />
        </div>
        <span className="text-white font-bold tracking-tight text-lg">
          DocTranslator <span className="text-indigo-500">AI</span>
        </span>
      </div>
      
      {/* ACTIONS CENTER */}
      <div className="flex items-center gap-2">
        <button onClick={onUploadClick} className="flex items-center gap-2 px-4 py-2 text-xs font-semibold bg-zinc-900 hover:bg-zinc-800 text-zinc-300 rounded-lg border border-zinc-800 transition-all hover:border-zinc-600">
          <Upload size={16} /> <span>Wgraj plik</span>
        </button>
        
        {hasFile && (
            <button 
                onClick={onProcessClick} 
                disabled={processingStatus === 'processing'}
                className={`flex items-center gap-2 px-6 py-2 text-xs font-bold rounded-lg shadow-lg transition-all border border-transparent
                ${processingStatus === 'processing' 
                    ? 'bg-zinc-800 text-zinc-500 cursor-not-allowed' 
                    : 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-indigo-900/20 hover:scale-105'}`}
            >
                {processingStatus === 'processing' ? <Loader2 size={16} className="animate-spin"/> : <Play size={16} fill="currentColor"/>}
                <span>{processingStatus === 'processing' ? 'PRZETWARZANIE...' : 'TŁUMACZ (AI)'}</span>
            </button>
        )}
      </div>

      {/* RIGHT CONTROLS */}
      <div className="flex items-center gap-4">
        {hasFile && (
            <div className="flex bg-zinc-900 p-1 rounded-lg border border-zinc-800">
                <button onClick={() => setViewMode('split')} className={`p-2 rounded-md transition-all ${viewMode === 'split' ? 'bg-zinc-700 text-white shadow-sm' : 'text-zinc-500 hover:text-zinc-300'}`} title="Split View"><Split size={16} /></button>
                <button onClick={() => setViewMode('single')} className={`p-2 rounded-md transition-all ${viewMode === 'single' ? 'bg-zinc-700 text-white shadow-sm' : 'text-zinc-500 hover:text-zinc-300'}`} title="Single View"><Maximize size={16} /></button>
            </div>
        )}
        
        <div className="h-6 w-px bg-zinc-800"></div>

        <button className="text-zinc-500 hover:text-zinc-300 transition-colors">
            <Settings size={20} />
        </button>
      </div>
    </header>
  );
};

export default Header;