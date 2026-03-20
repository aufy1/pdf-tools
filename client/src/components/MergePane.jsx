import React, { useState } from 'react';
import { FileText, GripVertical, Trash2, Combine, AlertCircle } from 'lucide-react';

const MergePane = ({ files, setFiles }) => {
  const [draggedIndex, setDraggedIndex] = useState(null);

  const removeFile = (indexToRemove) => {
    setFiles(files.filter((_, index) => index !== indexToRemove));
  };

  const handleDragStart = (e, index) => {
    setDraggedIndex(index);
    e.dataTransfer.effectAllowed = 'move';
    // Transparentny obrazek drag-ghost, aby domyślny podgląd nie zasłaniał ekranu
    const img = new Image();
    img.src = 'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7';
    e.dataTransfer.setDragImage(img, 0, 0);
  };

  const handleDragEnter = (e, targetIndex) => {
    e.preventDefault();
    if (draggedIndex === null || draggedIndex === targetIndex) return;

    setFiles((prevFiles) => {
      const newFiles = [...prevFiles];
      const itemToMove = newFiles[draggedIndex];
      newFiles.splice(draggedIndex, 1);
      newFiles.splice(targetIndex, 0, itemToMove);
      return newFiles;
    });
    
    // draggedIndex do nowej pozycji, żeby śledzić element na bieżąco
    setDraggedIndex(targetIndex);
  };

  const handleDragOver = (e) => {
    e.preventDefault(); // Musi tu być, aby drop działał
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDraggedIndex(null); // Bezpieczne czyszczenie przy upuszczeniu
  };

  const handleDragEnd = () => {
    setDraggedIndex(null); // Główne czyszczenie
  };

  return (
    <div className="w-full h-full flex flex-col bg-[#0c0c0e] p-8 overflow-y-auto items-center animate-in fade-in zoom-in-95 duration-300">
      <div className="max-w-3xl w-full space-y-6">
        
        <div className="flex items-center gap-4 border-b border-zinc-800 pb-6">
          <div className="p-3 bg-emerald-500/10 rounded-xl border border-emerald-500/20">
            <Combine className="text-emerald-500 w-8 h-8" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-white">Kolejność łączenia</h2>
            <p className="text-zinc-500 text-sm">Złap i przeciągnij element, aby zmienić kolejność. Upewnij się, że masz co najmniej 2 pliki.</p>
          </div>
        </div>

        {files.length < 2 && (
            <div className="flex items-center gap-3 p-4 bg-amber-500/10 text-amber-500 border border-amber-500/20 rounded-xl text-sm font-medium">
                <AlertCircle size={18} />
                Dodaj jeszcze co najmniej jeden plik, aby móc je połączyć. Użyj przycisku "Dodaj kolejne" na górze.
            </div>
        )}

        <div 
          className="space-y-3 pb-20"
          onDragOver={handleDragOver}
          onDrop={handleDrop}
        >
          {files.map((file, index) => {
            const isDragging = draggedIndex === index;
            return (
              <div 
                  key={`${file.name}-${file.lastModified || index}`} // Bezpieczniejszy key
                  draggable
                  onDragStart={(e) => handleDragStart(e, index)}
                  onDragEnter={(e) => handleDragEnter(e, index)}
                  onDragEnd={handleDragEnd}
                  // Gdy podnosimy element, dajemy mu klasę opacity i zmieniamy kolor
                  className={`flex items-center bg-zinc-900 border 
                    ${isDragging ? 'border-emerald-500 bg-zinc-800/80 shadow-[0_0_15px_rgba(16,185,129,0.2)] opacity-80 scale-[1.02] z-50' : 'border-zinc-800 hover:border-zinc-700'} 
                    rounded-xl p-4 group transition-all duration-200 cursor-grab active:cursor-grabbing relative`}
              >
                <div className="text-zinc-600 group-hover:text-emerald-500 p-1 transition-colors">
                  <GripVertical size={20} />
                </div>
                
                <div className="w-10 h-10 bg-zinc-950 rounded-lg flex items-center justify-center mx-4 border border-zinc-800 shrink-0">
                  <FileText size={20} className="text-emerald-500" />
                </div>
                
                <div className="flex-1 min-w-0 pointer-events-none">
                  <p className={`font-medium truncate pr-4 ${isDragging ? 'text-emerald-400' : 'text-zinc-200'}`}>
                    {file.name}
                  </p>
                  <p className="text-zinc-500 text-xs mt-0.5 uppercase tracking-wider">
                    Plik PDF • #{index + 1}
                  </p>
                </div>

                <button 
                  onClick={(e) => {
                      e.stopPropagation(); 
                      removeFile(index);
                  }}
                  className="p-2 text-zinc-500 hover:text-rose-400 hover:bg-rose-400/10 rounded-lg transition-colors ml-4 cursor-pointer"
                  title="Usuń z listy"
                  disabled={isDragging} // Blokujemy usuwanie podczas przeciągania
                >
                  <Trash2 size={18} />
                </button>
              </div>
            );
          })}
        </div>

      </div>
    </div>
  );
};

export default MergePane;