import React, { useState } from 'react';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import UploadZone from './components/UploadZone';
import PreviewPane from './components/PreviewPane';
import MergePane from './components/MergePane';
import SplitPane from './components/SplitPane';

const API_URL = "/api";

function App() {
  const [files, setFiles] = useState([]); // Tablica plików: { name, url, rawFile }
  const [translatedFileUrl, setTranslatedFileUrl] = useState(null);
  const [viewMode, setViewMode] = useState('split');
  const [status, setStatus] = useState('idle'); // 'idle' | 'uploading' | 'processing' | 'done' | 'error'
  const [processStep, setProcessStep] = useState('');
  const [activeTool, setActiveTool] = useState('translate'); // 'translate' | 'merge' | 'split'

  const primaryFile = files[0];

  // Wgrywanie plików (Drag & Drop lub Input)
  const handleFileSelect = async (selectedFiles) => {
    const filesArray = Array.isArray(selectedFiles) ? selectedFiles : [selectedFiles];
    
    const newFiles = filesArray.map(file => ({
        name: file.name,
        url: URL.createObjectURL(file),
        rawFile: file
    }));

    if (activeTool === 'merge') {
        setFiles(prev => [...prev, ...newFiles]);
    } else {
        setFiles(newFiles);
    }

    setTranslatedFileUrl(null);
    setStatus('uploading');

    try {
        for (const fileObj of newFiles) {
            const formData = new FormData();
            formData.append('file', fileObj.rawFile);
            const res = await fetch(`${API_URL}/upload`, { method: 'POST', body: formData });
            if (!res.ok) throw new Error(`Upload failed for ${fileObj.name}`);
        }
        setStatus('idle');
    } catch (err) {
        console.error(err);
        alert("Błąd wysyłania pliku na serwer");
        setStatus('error');
    }
  };

  // Dodawanie kolejnych plików (dla łączenia)
  const handleAddMoreFiles = (e) => {
    const selectedFiles = Array.from(e.target.files);
    if (selectedFiles.length > 0) {
      handleFileSelect(selectedFiles);
    }
    e.target.value = null; // Reset inputa
  };

  // Tłumaczenie
  const handleProcess = async (selectedLang) => {
    if (!primaryFile) return;
    setStatus('processing');
    setProcessStep(`Analiza struktury PDF... (Język: ${selectedLang.toUpperCase()})`);

    try {
        const timer = setInterval(() => {
             setProcessStep(prev => prev.startsWith('Analiza') ? 'Tłumaczenie AI (Google)...' : 'Rekonstrukcja dokumentu...');
        }, 2000);

        const res = await fetch(`${API_URL}/translate/${primaryFile.name}?target_lang=${selectedLang}`, {
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

  // Konwersja do Worda
  const handleConvertToWord = async () => {
    if (!primaryFile) return;
    setStatus('processing');
    setProcessStep('Konwersja PDF do DOCX...');

    try {
        const res = await fetch(`${API_URL}/convert/to-word/${primaryFile.name}`, { method: 'POST' });
        if (!res.ok) throw new Error("Conversion failed");
        const data = await res.json();

        const downloadLink = document.createElement('a');
        downloadLink.href = data.download_url;
        downloadLink.download = data.converted;
        document.body.appendChild(downloadLink);
        downloadLink.click();
        document.body.removeChild(downloadLink);

        setStatus('done');
        setProcessStep('Pobieranie rozpoczęte!');
        setTimeout(() => setStatus('idle'), 2000);
    } catch (err) {
        console.error(err);
        setStatus('error');
        setProcessStep('Błąd konwersji.');
    }
  };

  // Łączenie PDF (Stub dla backendu)
  const handleMergePDFs = async () => {
      if (files.length < 2) return alert("Wybierz co najmniej 2 pliki.");
      setStatus('processing');
      setProcessStep('Łączenie plików PDF...');
      
      try {
          console.log("Merging:", files.map(f => f.name));
          // TODO: Fetch na endpoint /merge
          setTimeout(() => {
              setStatus('done');
              setProcessStep('Połączono pomyślnie!');
          }, 2000);
      } catch (e) { setStatus('error'); }
  };

  // Dzielenie PDF (Stub dla backendu)
  const handleSplitPDF = async () => {
      if (!primaryFile) return;
      setStatus('processing');
      setProcessStep('Dzielenie pliku PDF...');
      
      try {
          console.log("Splitting:", primaryFile.name);
          // TODO: Fetch na endpoint /split
          setTimeout(() => {
              setStatus('done');
              setProcessStep('Plik został podzielony!');
          }, 2000);
      } catch (e) { setStatus('error'); }
  };

  const handleReset = () => {
     setFiles([]);
     setTranslatedFileUrl(null);
     setStatus('idle');
  };

  return (
    <div className="flex flex-col h-screen w-screen bg-zinc-950 text-zinc-300 font-sans overflow-hidden selection:bg-indigo-500/30">
      
      <Header 
        onUploadClick={handleReset}
        onAddMoreFiles={handleAddMoreFiles}
        onProcessClick={handleProcess}
        onConvertClick={handleConvertToWord}
        onMergeClick={handleMergePDFs}
        onSplitClick={handleSplitPDF}
        processingStatus={status}
        viewMode={viewMode}
        setViewMode={setViewMode}
        hasFile={files.length > 0}
        activeTool={activeTool}
        fileCount={files.length}
      />

      <div className="flex flex-1 overflow-hidden relative">
        <Sidebar activeTool={activeTool} setActiveTool={setActiveTool} onReset={handleReset} />

        <main className="flex-1 flex overflow-hidden bg-[#0c0c0e] relative">
          {files.length === 0 ? (
            <UploadZone onFileSelected={handleFileSelect} multiple={activeTool === 'merge'} />
          ) : (
            activeTool === 'translate' ? (
                <PreviewPane 
                  fileUrl={primaryFile?.url}
                  translatedFileUrl={translatedFileUrl} 
                  viewMode={viewMode}
                  processingStatus={status}
                  processStep={processStep}
                />
            ) : activeTool === 'merge' ? (
                <MergePane files={files} setFiles={setFiles} />
            ) : (
                <SplitPane file={primaryFile} />
            )
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