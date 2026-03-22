import React, { useState, useRef, useEffect } from 'react';
import { Layers, Upload, Play, Settings, Split, Maximize, Loader2, FileType, Check, Combine, Scissors, Plus } from 'lucide-react';

const LANGUAGES = [
  { code: 'uk', label: 'Ukraiński', flag: '🇺🇦' },
  { code: 'en', label: 'Angielski', flag: '🇬🇧' },
  { code: 'de', label: 'Niemiecki', flag: '🇩🇪' },
  { code: 'fr', label: 'Francuski', flag: '🇫🇷' },
  { code: 'es', label: 'Hiszpański', flag: '🇪🇸' },
];

const Header = ({ 
  onUploadClick, 
  onAddMoreFiles,
  onProcessClick, 
  onConvertClick,
  onMergeClick,
  onSplitClick,
  processingStatus, 
  viewMode, 
  setViewMode,
  hasFile,
  activeTool,
  fileCount
}) => {
  const [selectedLang, setSelectedLang] = useState('uk');
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const settingsRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (settingsRef.current && !settingsRef.current.contains(event.target)) setIsSettingsOpen(false);
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const isProcessing = processingStatus === 'processing';

  return (
    <header className="h-16 bg-zinc-950 border-b border-zinc-800 flex items-center justify-between px-6 shrink-0 shadow-sm z-30 relative">
      
      <div className="flex items-center gap-3">
        <div className="bg-indigo-500/10 p-2 rounded-lg border border-indigo-500/20">
            <Layers className="w-5 h-5 text-indigo-500" />
        </div>
        <span className="text-white font-bold tracking-tight text-xl">
          PDF <span className="text-indigo-500">Tools</span>   
        </span>
      </div>
      
      <div className="flex items-center gap-2">
        {/* Przycisk Uploadu */}
        {activeTool === 'merge' && hasFile ? (
            <label className="flex items-center gap-2 px-4 py-2 text-xs font-semibold bg-emerald-900/20 hover:bg-emerald-800/40 text-emerald-400 rounded-lg border border-emerald-800/50 transition-all cursor-pointer">
                <Plus size={16} /> <span>Dodaj kolejne</span>
                <input type="file" multiple accept=".pdf" className="hidden" onChange={onAddMoreFiles} />
            </label>
        ) : (
            <button onClick={onUploadClick} className="flex items-center gap-2 px-4 py-2 text-xs font-semibold bg-zinc-900 hover:bg-zinc-800 text-zinc-300 rounded-lg border border-zinc-800 transition-all hover:border-zinc-600">
                <Upload size={16} /> <span>{hasFile ? 'Zacznij od nowa' : 'Wgraj plik'}</span>
            </button>
        )}
        
        {/* Przyciski Tłumaczenia */}
        {hasFile && activeTool === 'translate' && (
            <button onClick={() => onProcessClick(selectedLang)} disabled={isProcessing}
                className={`flex items-center gap-2 px-6 py-2 text-xs font-bold rounded-lg shadow-lg transition-all border border-transparent
                ${isProcessing ? 'bg-zinc-800 text-zinc-500 cursor-not-allowed' : 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-indigo-900/20 hover:scale-105'}`}>
                {isProcessing ? <Loader2 size={16} className="animate-spin"/> : <Play size={16} fill="currentColor"/>}
                <span>{isProcessing ? 'PRZETWARZANIE...' : `TŁUMACZ (${selectedLang.toUpperCase()})`}</span>
            </button>
        )}

        {/* Przycisk Konwersji DOCX (NOWY WIDOK) */}
        {hasFile && activeTool === 'convert' && (
             <button onClick={onConvertClick} disabled={isProcessing}
                className={`flex items-center gap-2 px-6 py-2 text-xs font-bold rounded-lg shadow-lg transition-all border border-transparent
                ${isProcessing ? 'bg-zinc-800 text-zinc-500 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-500 text-white shadow-blue-900/20 hover:scale-105'}`}>
                {isProcessing ? <Loader2 size={16} className="animate-spin"/> : <FileType size={16} />}
                <span>{isProcessing ? 'KONWERSJA...' : `KONWERTUJ DO DOCX`}</span>
            </button>
        )}

        {/* Przycisk Merge */}
        {hasFile && activeTool === 'merge' && (
             <button onClick={onMergeClick} disabled={isProcessing || fileCount < 2}
                className={`flex items-center gap-2 px-6 py-2 text-xs font-bold rounded-lg shadow-lg transition-all border border-transparent
                ${isProcessing || fileCount < 2 ? 'bg-zinc-800 text-zinc-500 cursor-not-allowed' : 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-emerald-900/20 hover:scale-105'}`}>
                {isProcessing ? <Loader2 size={16} className="animate-spin"/> : <Combine size={16} />}
                <span>{isProcessing ? 'ŁĄCZENIE...' : `POŁĄCZ ${fileCount} PLIKI`}</span>
            </button>
        )}

        {/* Przycisk Split */}
        {hasFile && activeTool === 'split' && (
             <button onClick={onSplitClick} disabled={isProcessing}
                className={`flex items-center gap-2 px-6 py-2 text-xs font-bold rounded-lg shadow-lg transition-all border border-transparent
                ${isProcessing ? 'bg-zinc-800 text-zinc-500 cursor-not-allowed' : 'bg-rose-600 hover:bg-rose-500 text-white shadow-rose-900/20 hover:scale-105'}`}>
                {isProcessing ? <Loader2 size={16} className="animate-spin"/> : <Scissors size={16} />}
                <span>{isProcessing ? 'DZIELENIE...' : `PODZIEL PDF`}</span>
            </button>
        )}
      </div>

      <div className="flex items-center gap-4">
        {hasFile && activeTool === 'translate' && (
            <div className="flex bg-zinc-900 p-1 rounded-lg border border-zinc-800">
                <button onClick={() => setViewMode('split')} className={`p-2 rounded-md transition-all ${viewMode === 'split' ? 'bg-zinc-700 text-white shadow-sm' : 'text-zinc-500 hover:text-zinc-300'}`}><Split size={16} /></button>
                <button onClick={() => setViewMode('single')} className={`p-2 rounded-md transition-all ${viewMode === 'single' ? 'bg-zinc-700 text-white shadow-sm' : 'text-zinc-500 hover:text-zinc-300'}`}><Maximize size={16} /></button>
            </div>
        )}
        
        {/* Ukrywamy separator, jeśli nie ma widocznych narzędzi po prawej stronie */}
        {activeTool === 'translate' && (
            <>
                <div className="h-6 w-px bg-zinc-800"></div>

                <div className="relative" ref={settingsRef}>
                    <button onClick={() => setIsSettingsOpen(!isSettingsOpen)} className={`transition-colors ${isSettingsOpen ? 'text-indigo-400' : 'text-zinc-500 hover:text-zinc-300'}`}>
                        <Settings size={20} className={isProcessing ? 'animate-spin-slow' : ''} />
                    </button>

                    {isSettingsOpen && (
                        <div className="absolute right-0 mt-3 w-48 bg-zinc-900 border border-zinc-800 rounded-xl shadow-2xl p-2 z-50 animate-in fade-in zoom-in duration-150">
                            <div className="px-3 py-2 text-[10px] font-bold text-zinc-500 uppercase tracking-wider">Język docelowy</div>
                            {LANGUAGES.map((lang) => (
                                <button
                                    key={lang.code}
                                    onClick={() => {
                                        setSelectedLang(lang.code);
                                        setIsSettingsOpen(false);
                                    }}
                                    className="w-full flex items-center justify-between px-3 py-2 rounded-lg hover:bg-zinc-800 transition-colors text-sm text-zinc-300 hover:text-white"
                                >
                                    <span className="flex items-center gap-2">
                                        <span>{lang.flag}</span>
                                        {lang.label}
                                    </span>
                                    {selectedLang === lang.code && <Check size={14} className="text-indigo-500" />}
                                </button>
                            ))}
                        </div>
                    )}
                </div>
            </>
        )}
      </div>
    </header>
  );
};

export default Header;