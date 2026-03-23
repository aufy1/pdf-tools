import React, { useState } from 'react';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import UploadZone from './components/UploadZone';
import PreviewPane from './components/PreviewPane';
import MergePane from './components/MergePane';
import SplitPane from './components/SplitPane';

const API_URL = "/api";

function App() {
  const [files, setFiles] = useState([]); // table of files { name, url, rawFile }
  const [translatedFileUrl, setTranslatedFileUrl] = useState(null);
  const [viewMode, setViewMode] = useState('split');
  const [status, setStatus] = useState('idle'); // 'idle' | 'uploading' | 'processing' | 'done' | 'error'
  const [processStep, setProcessStep] = useState('');
  const [activeTool, setActiveTool] = useState('translate'); // 'translate' | 'merge' | 'split'
  const [splitPagesRange, setSplitPagesRange] = useState('');

  const primaryFile = files[0];

  // drag and drop
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

  const handleAddMoreFiles = (e) => {
    const selectedFiles = Array.from(e.target.files);
    if (selectedFiles.length > 0) {
      handleFileSelect(selectedFiles);
    }
    e.target.value = null; // input reset
  };

  // translation
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

  // conversion
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

  // merge
const handleMergePDFs = async () => {
      if (files.length < 2) return alert("Wybierz co najmniej 2 pliki.");
      setStatus('processing');
      setProcessStep('Łączenie plików PDF...');
      
      try {
          const res = await fetch(`${API_URL}/merge`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ filenames: files.map(f => f.name) })
          });
          
          if (!res.ok) throw new Error("Merge failed");
          const data = await res.json();

          const downloadLink = document.createElement('a');
          downloadLink.href = data.download_url;
          downloadLink.download = data.converted;
          document.body.appendChild(downloadLink);
          downloadLink.click();
          document.body.removeChild(downloadLink);

          setStatus('done');
          setProcessStep('Połączono pomyślnie!');
          setTimeout(() => setStatus('idle'), 2000);
      } catch (e) { 
          console.error(e);
          setStatus('error'); 
          setProcessStep('Błąd łączenia plików.');
      }
  };

  // split
  const handleSplitPDF = async () => {
      if (!primaryFile) return;
      setStatus('processing');
      setProcessStep('Dzielenie pliku PDF...');
      
      try {
          const res = await fetch(`${API_URL}/split`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ 
                  filename: primaryFile.name,
                  pages: splitPagesRange
              })
          });

          if (!res.ok) throw new Error("Split failed");
          const data = await res.json();

          const downloadLink = document.createElement('a');
          downloadLink.href = data.download_url;
          downloadLink.download = data.converted;
          document.body.appendChild(downloadLink);
          downloadLink.click();
          document.body.removeChild(downloadLink);

          setStatus('done');
          setProcessStep('Plik został podzielony!');
          setTimeout(() => setStatus('idle'), 2000);
      } catch (e) { 
          console.error(e);
          setStatus('error'); 
          setProcessStep('Błąd cięcia pliku.');
      }
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
            (activeTool === 'translate' || activeTool === 'convert') ? (
                <PreviewPane 
                  fileUrl={primaryFile?.url}
                  translatedFileUrl={activeTool === 'translate' ? translatedFileUrl : null} 
                  viewMode={activeTool === 'convert' ? 'single' : viewMode}
                  processingStatus={status}
                  processStep={processStep}
                />
            ) : activeTool === 'merge' ? (
                <MergePane files={files} setFiles={setFiles} />
            ) : (
                <SplitPane 
                    file={primaryFile} 
                    pagesRange={splitPagesRange} 
                    setPagesRange={setSplitPagesRange} 
                />
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