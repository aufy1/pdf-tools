import React, { useState, useRef, useEffect } from 'react';
import { Layers, Upload, Play, Settings, Split, Maximize, Loader2, FileType, Check } from 'lucide-react';

const LANGUAGES = [
  { code: 'uk', label: 'Ukraiński', flag: '🇺🇦' },
  { code: 'en', label: 'Angielski', flag: '🇬🇧' },
  { code: 'de', label: 'Niemiecki', flag: '🇩🇪' },
  { code: 'fr', label: 'Francuski', flag: '🇫🇷' },
  { code: 'es', label: 'Hiszpański', flag: '🇪🇸' },
];

const Header = ({ 
  onUploadClick, 
  onProcessClick, 
  onConvertClick,
  processingStatus, 
  viewMode, 
  setViewMode,
  hasFile 
}) => {
  const [selectedLang, setSelectedLang] = useState('uk');
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const settingsRef = useRef(null);

  // Zamknij menu po kliknięciu poza
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (settingsRef.current && !settingsRef.current.contains(event.target)) {
        setIsSettingsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <header className="h-16 bg-zinc-950 border-b border-zinc-800 flex items-center justify-between px-6 shrink-0 shadow-sm z-30 relative">
      
      {/* LOGO */}
      <div className="flex items-center gap-3">
        <div className="bg-indigo-500/10 p-2 rounded-lg border border-indigo-500/20">
            <Layers className="w-5 h-5 text-indigo-500" />
        </div>
        <span className="text-white font-bold tracking-tight text-xl">
          PDF <span className="text-indigo-500">Tools</span>   
        </span>
      </div>
      
      {/* ACTIONS CENTER */}
      <div className="flex items-center gap-2">
        <button onClick={onUploadClick} className="flex items-center gap-2 px-4 py-2 text-xs font-semibold bg-zinc-900 hover:bg-zinc-800 text-zinc-300 rounded-lg border border-zinc-800 transition-all hover:border-zinc-600">
          <Upload size={16} /> <span>Wgraj plik</span>
        </button>
        
        {hasFile && (
            <>
                <button 
                    onClick={() => onProcessClick(selectedLang)} 
                    disabled={processingStatus === 'processing'}
                    className={`flex items-center gap-2 px-6 py-2 text-xs font-bold rounded-lg shadow-lg transition-all border border-transparent
                    ${processingStatus === 'processing' 
                        ? 'bg-zinc-800 text-zinc-500 cursor-not-allowed' 
                        : 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-indigo-900/20 hover:scale-105'}`}
                >
                    {processingStatus === 'processing' ? <Loader2 size={16} className="animate-spin"/> : <Play size={16} fill="currentColor"/>}
                    <span>{processingStatus === 'processing' ? 'PRZETWARZANIE...' : `TŁUMACZ (${selectedLang.toUpperCase()})`}</span>
                </button>

                <button 
                    onClick={onConvertClick} 
                    disabled={processingStatus === 'processing'}
                    className={`flex items-center gap-2 px-4 py-2 text-xs font-bold rounded-lg transition-all border 
                    ${processingStatus === 'processing' 
                        ? 'bg-zinc-800 text-zinc-500 border-zinc-800 cursor-not-allowed' 
                        : 'bg-blue-600/10 hover:bg-blue-600/20 text-blue-400 border-blue-500/20 hover:border-blue-500/50'}`}
                >
                    <FileType size={16} />
                    <span>DOCX</span>
                </button>
            </>
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

        {/* SETTINGS WITH DROPDOWN */}
        <div className="relative" ref={settingsRef}>
            <button 
                onClick={() => setIsSettingsOpen(!isSettingsOpen)}
                className={`transition-colors ${isSettingsOpen ? 'text-indigo-400' : 'text-zinc-500 hover:text-zinc-300'}`}
            >
                <Settings size={20} className={processingStatus === 'processing' ? 'animate-spin-slow' : ''} />
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
      </div>
    </header>
  );
};

export default Header;