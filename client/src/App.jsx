import React, { useState } from 'react';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import UploadZone from './components/UploadZone';
import PreviewPane from './components/PreviewPane';

function App() {
  const [currentFile, setCurrentFile] = useState(null); // { name, url }
  const [viewMode, setViewMode] = useState('split');
  const [status, setStatus] = useState('idle'); // 'idle' | 'processing' | 'done'
  const [processStep, setProcessStep] = useState('');

  // Symulacja procesu AI
  const handleProcess = () => {
    setStatus('processing');
    
    // Symulacja kroków
    setProcessStep('Inicjalizacja OCR...');
    setTimeout(() => {
        setProcessStep('Analiza układu tabel (LayoutLM)...');
        setTimeout(() => {
            setProcessStep('Tłumaczenie tekstu (NLLB-200)...');
            setTimeout(() => {
                setProcessStep('Rekonstrukcja pliku PDF...');
                setTimeout(() => {
                    setStatus('done');
                    setProcessStep('');
                }, 1500);
            }, 2000);
        }, 1500);
    }, 1000);
  };

  const handleFileSelect = (file) => {
    const url = URL.createObjectURL(file);
    setCurrentFile({ name: file.name, url });
    setStatus('idle');
  };

  const handleReset = () => {
     setCurrentFile(null);
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
              fileUrl={currentFile.url}
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