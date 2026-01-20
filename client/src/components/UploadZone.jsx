import React from 'react';
import { UploadCloud, FileType, Zap } from 'lucide-react';

const UploadZone = ({ onFileSelected }) => {
  
  const handleDrop = (e) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file && file.type === 'application/pdf') {
      onFileSelected(file);
    }
  };

  const handleChange = (e) => {
    const file = e.target.files[0];
    if (file) onFileSelected(file);
  };

  return (
    <div 
      className="w-full h-full flex flex-col items-center justify-center p-8 animate-in fade-in zoom-in duration-300"
      onDragOver={(e) => e.preventDefault()}
      onDrop={handleDrop}
    >
      <div className="max-w-xl w-full bg-zinc-900/30 border-2 border-dashed border-zinc-800 rounded-3xl p-16 flex flex-col items-center gap-8 hover:border-indigo-500/50 hover:bg-zinc-900/80 transition-all group cursor-pointer text-center relative overflow-hidden backdrop-blur-sm">
        
        {/* Glow effect */}
        <div className="absolute inset-0 bg-gradient-to-tr from-indigo-500/5 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none"></div>
        
        <div className="w-24 h-24 bg-zinc-950 rounded-3xl flex items-center justify-center shadow-2xl group-hover:scale-110 group-hover:-rotate-3 transition-transform duration-500 border border-zinc-800 z-10">
          <UploadCloud size={48} className="text-indigo-500" />
        </div>
        
        <div className="space-y-3 z-10">
          <h3 className="text-3xl font-bold text-white tracking-tight">Wgraj instrukcję</h3>
          <p className="text-zinc-500 text-sm max-w-xs mx-auto">Obsługuje tylko pliki PDF</p>
        </div>

        <label className="z-10 mt-2 px-10 py-4 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-sm font-bold shadow-xl shadow-indigo-900/20 transition-all hover:-translate-y-1 cursor-pointer">
          Wybierz plik z dysku
          <input type="file" className="hidden" accept=".pdf" onChange={handleChange} />
        </label>

        {/* Footer icons */}
        <div className="flex gap-8 mt-4 pt-8 border-t border-zinc-800/50 w-full justify-center opacity-60">
            <div className="flex flex-col items-center gap-2 text-zinc-500">
                <FileType size={18}/>
                <span className="text-[10px] uppercase font-bold tracking-widest">PDF</span>
            </div>
            <div className="flex flex-col items-center gap-2 text-zinc-500">
                <Zap size={18}/>
                <span className="text-[10px] uppercase font-bold tracking-widest">AI Powered</span>
            </div>
        </div>
      </div>
    </div>
  );
};

export default UploadZone;