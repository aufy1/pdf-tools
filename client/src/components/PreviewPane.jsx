import React from 'react';
import { Loader2, ArrowRight } from 'lucide-react';

const PreviewPane = ({ fileUrl, viewMode, processingStatus, processStep }) => {
  return (
    <div className="w-full h-full flex relative bg-zinc-900">
      
      {/* LEWA STRONA: ORYGINAŁ */}
      <div className={`flex flex-col border-r border-zinc-800 transition-all duration-500 ease-in-out ${viewMode === 'split' ? 'w-1/2' : 'w-full'}`}>
        <div className="h-10 bg-zinc-950 border-b border-zinc-800 flex items-center justify-between px-4 shrink-0">
          <span className="text-xs font-bold text-zinc-500 tracking-wider flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-zinc-600"></div> ORYGINAŁ (PL)
          </span>
        </div>
        <div className="flex-1 bg-zinc-800/50 p-6 overflow-hidden relative">
             <iframe src={fileUrl} className="w-full h-full rounded-lg shadow-2xl border border-zinc-700 bg-white" title="Original" />
        </div>
      </div>

      {/* PRAWA STRONA: TŁUMACZENIE */}
      {(viewMode === 'split') && (
        <div className={`flex flex-col w-1/2 transition-all duration-500 ease-in-out`}>
           
           <div className="h-10 bg-zinc-950 border-b border-zinc-800 flex items-center justify-between px-4 shrink-0">
              <span className="text-xs font-bold text-indigo-400 tracking-wider flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-indigo-500 animate-pulse"></div> TŁUMACZENIE (UA)
              </span>
           </div>

           <div className="flex-1 bg-zinc-800/50 p-6 relative flex items-center justify-center overflow-hidden">
              
              {processingStatus === 'processing' ? (
                <div className="flex flex-col items-center gap-6 animate-in fade-in zoom-in duration-500">
                    <div className="relative">
                        <div className="w-20 h-20 border-4 border-zinc-800 rounded-full"></div>
                        <div className="w-20 h-20 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin absolute top-0 left-0"></div>
                        <div className="absolute inset-0 flex items-center justify-center font-mono font-bold text-indigo-500 text-lg">AI</div>
                    </div>
                    <div className="text-center space-y-2">
                        <h4 className="text-white font-medium text-lg">Przetwarzanie dokumentu...</h4>
                        <div className="px-3 py-1 bg-zinc-900 rounded-full border border-zinc-700 inline-block">
                             <p className="text-xs text-indigo-300 font-mono animate-pulse">{processStep}</p>
                        </div>
                    </div>
                </div>
              ) : processingStatus === 'done' ? (
                 /* Tutaj normalnie byłby iframe z przetłumaczonym PDF */
                 <div className="w-full h-full bg-white rounded-lg shadow-2xl border border-indigo-500/30 flex items-center justify-center text-zinc-800 relative overflow-hidden group">
                    <div className="absolute inset-0 bg-indigo-500/5 pointer-events-none"></div>
                    <div className="text-center p-8">
                        <h2 className="text-2xl font-bold text-indigo-900 mb-2">Інструкція користувача</h2>
                        <p className="text-sm text-zinc-500">Symulacja podglądu PDF po tłumaczeniu.</p>
                        <div className="mt-8 border-2 border-dashed border-zinc-300 p-4 rounded bg-zinc-50">
                            [TUTAJ POJAWI SIĘ WYGENEROWANY PDF]
                        </div>
                    </div>
                 </div>
              ) : (
                <div className="text-center opacity-30 flex flex-col items-center gap-4">
                    <ArrowRight size={48} className="text-zinc-600"/>
                    <p className="text-sm text-zinc-400 font-medium">Kliknij "TŁUMACZ", aby wygenerować podgląd</p>
                </div>
              )}

           </div>
        </div>
      )}
    </div>
  );
};

export default PreviewPane;