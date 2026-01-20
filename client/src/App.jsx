import React, { useState } from 'react';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import UploadZone from './components/UploadZone';
import PreviewPane from './components/PreviewPane';


const API_URL = "/api";

function App() {
  const [currentFile, setCurrentFile] = useState(null); // { name, url, rawFile }
  const [translatedFileUrl, setTranslatedFileUrl] = useState(null);
  const [viewMode, setViewMode] = useState('split');
  const [status, setStatus] = useState('idle'); // 'idle' | 'uploading' | 'processing' | 'done' | 'error'
  const [processStep, setProcessStep] = useState('');

  // 1. Obsługa wgrania pliku
  const handleFileSelect = async (file) => {
    // Lokalny podgląd
    const url = URL.createObjectURL(file);
    setCurrentFile({ name: file.name, url, rawFile: file });
    setTranslatedFileUrl(null);
    setStatus('uploading');

    // Wysyłka na serwer
    const formData = new FormData();
    formData.append('file', file);

    try {
        const res = await fetch(`${API_URL}/upload`, {
            method: 'POST',
            body: formData,
        });
        if (!res.ok) throw new Error("Upload failed");
        setStatus('idle');
    } catch (err) {
        console.error(err);
        alert("Błąd wysyłania pliku na serwer");
        setStatus('error');
    }
  };

  // 2. Obsługa procesu tłumaczenia
  const handleProcess = async () => {
    if (!currentFile) return;
    
    setStatus('processing');
    setProcessStep('Analiza struktury PDF...');

    try {
        // Symulacja kroków dla UX (bo backend jest synchroniczny w MVP)
        const timer = setInterval(() => {
             setProcessStep(prev => prev === 'Analiza struktury PDF...' ? 'Tłumaczenie AI (Google)...' : 'Rekonstrukcja dokumentu...');
        }, 2000);

        const res = await fetch(`${API_URL}/translate/${currentFile.name}`, {
            method: 'POST'
        });

        clearInterval(timer);

        if (!res.ok) throw new Error("Translation failed");
        
        const data = await res.json();
        
        // Ustawiamy URL do pobrania przetłumaczonego pliku
        // Dodajemy timestamp, żeby uniknąć cache'owania przeglądarki
        setTranslatedFileUrl(`${data.download_url}?t=${Date.now()}`);
        
        setStatus('done');
        setProcessStep('Gotowe!');

    } catch (err) {
        console.error(err);
        setStatus('error');
        setProcessStep('Błąd przetwarzania.');
        alert("Błąd podczas tłumaczenia. Sprawdź logi backendu.");
    }
  };

  const handleReset = () => {
     setCurrentFile(null);
     setTranslatedFileUrl(null);
     setStatus('idle');
  };

  return (
    <div className="flex flex-col h-screen w-screen bg-zinc-950 text-zinc-300 font-sans overflow-hidden selection:bg-indigo-500/30">
      
      <Header 
        onUploadClick={handleReset}
        onProcessClick={handleProcess}
        processingStatus={status}
        viewMode={viewMode}
        setViewMode={setViewMode}
        hasFile={!!currentFile}
      />

      <div className="flex flex-1 overflow-hidden relative">
        <Sidebar />

        <main className="flex-1 flex overflow-hidden bg-[#0c0c0e] relative">
          {!currentFile ? (
            <UploadZone onFileSelected={handleFileSelect} />
          ) : (
            <PreviewPane 
              // Lewa strona: Oryginał
              fileUrl={currentFile.url}
              
              // Prawa strona: Jeśli gotowe, pokaż wynik z serwera, inaczej nic
              translatedFileUrl={translatedFileUrl} 
              
              viewMode={viewMode}
              processingStatus={status}
              processStep={processStep}
            />
          )}
        </main>
      </div>
    </div>
  );
}

export default App;