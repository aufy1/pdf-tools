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
    const url = URL.createObjectURL(file);
    setCurrentFile({ name: file.name, url, rawFile: file });
    setTranslatedFileUrl(null);
    setStatus('uploading');

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
        const timer = setInterval(() => {
             setProcessStep(prev => prev === 'Analiza struktury PDF...' ? 'Tłumaczenie AI (Google)...' : 'Rekonstrukcja dokumentu...');
        }, 2000);

        const res = await fetch(`${API_URL}/translate/${currentFile.name}`, {
            method: 'POST'
        });

        clearInterval(timer);

        if (!res.ok) throw new Error("Translation failed");
        
        const data = await res.json();
        
        setTranslatedFileUrl(`${data.download_url}?t=${Date.now()}`);
        setStatus('done');
        setProcessStep('Gotowe!');

    } catch (err) {
        console.error(err);
        setStatus('error');
        setProcessStep('Błąd przetwarzania.');
        alert("Błąd podczas tłumaczenia.");
    }
  };

  // 3. NOWA FUNKCJA: Obsługa konwersji do Worda
  const handleConvertToWord = async () => {
    if (!currentFile) return;

    setStatus('processing');
    setProcessStep('Konwersja PDF do DOCX...');

    try {
        const res = await fetch(`${API_URL}/convert/to-word/${currentFile.name}`, {
            method: 'POST'
        });

        if (!res.ok) throw new Error("Conversion failed");

        const data = await res.json();

        // Wymuszenie pobierania pliku
        const downloadLink = document.createElement('a');
        downloadLink.href = data.download_url; // Endpoint z Nginx
        downloadLink.download = data.converted; // Sugerowana nazwa pliku
        document.body.appendChild(downloadLink);
        downloadLink.click();
        document.body.removeChild(downloadLink);

        setStatus('done');
        setProcessStep('Pobieranie rozpoczęte!');
        
        // Po chwili wróć do idle, żeby można było coś jeszcze zrobić
        setTimeout(() => setStatus('idle'), 2000);

    } catch (err) {
        console.error(err);
        setStatus('error');
        setProcessStep('Błąd konwersji.');
        alert("Błąd podczas konwersji do Worda.");
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
        onConvertClick={handleConvertToWord} // <--- Przekazujemy funkcję
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
              fileUrl={currentFile.url}
              translatedFileUrl={translatedFileUrl} 
              viewMode={viewMode}
              processingStatus={status}
              processStep={processStep}
            />
          )}
        </main>
      </div>
      <footer className="h-6 bg-zinc-950 border-t border-zinc-800 flex items-center justify-center shrink-0 z-50">
        <p className="text-[10px] text-zinc-600 font-medium tracking-wide uppercase">
          Designed and developed by <span className="text-zinc-400">Szymon Zdanowicz</span> • <a href="mailto:kontakt@aufy.pl" className="hover:text-indigo-400 transition-colors">kontakt@aufy.pl</a>
        </p>
      </footer>
    </div>
  );
}

export default App;