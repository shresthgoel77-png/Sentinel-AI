import React, { useState, useRef } from 'react';

interface FileDropZoneProps {
  onFileAccepted: (file: File) => void;
  disabled: boolean;
}

export const FileDropZone: React.FC<FileDropZoneProps> = ({ onFileAccepted, disabled }) => {
  const [isDragActive, setIsDragActive] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (disabled) return;
    
    if (e.type === "dragenter" || e.type === "dragover") {
      setIsDragActive(true);
    } else if (e.type === "dragleave") {
      setIsDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);
    if (disabled) return;

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      onFileAccepted(e.dataTransfer.files[0]);
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      onFileAccepted(e.target.files[0]);
    }
  };

  return (
    <div
      onDragEnter={handleDrag}
      onDragOver={handleDrag}
      onDragLeave={handleDrag}
      onDrop={handleDrop}
      onClick={() => !disabled && fileInputRef.current?.click()}
      className={`relative group font-mono border border-dashed transition-all duration-300 ease-out p-8 text-center cursor-pointer
        ${isDragActive 
          ? 'border-emerald-500 bg-emerald-950/20 shadow-[0_0_15px_rgba(16,185,129,0.1)]' 
          : 'border-zinc-800 bg-zinc-950/40 hover:border-zinc-700 hover:bg-zinc-950/60'} 
        ${disabled ? 'opacity-40 cursor-not-allowed pointer-events-none' : ''}`}
    >
      <input
        ref={fileInputRef}
        type="file"
        className="hidden"
        onChange={handleFileInput}
        disabled={disabled}
        accept=".pdf,.doc,.docx,.txt,.json"
      />

      <div className="flex flex-col items-center justify-center space-y-3">
        <div className={`w-8 h-8 flex items-center justify-center border rounded-full transition-transform duration-500
          ${isDragActive ? 'border-emerald-400 rotate-180 text-emerald-400' : 'border-zinc-700 text-zinc-500 group-hover:text-zinc-400'}`}>
          ↓
        </div>
        <div className="text-xs uppercase tracking-widest text-zinc-400">
          {isDragActive ? "Release Vector to Stream" : "Drop Payload / Click to Select"}
        </div>
        <div className="text-[10px] text-zinc-600 max-w-xs">
          Supported inputs: Secure text streams, architectural maps, or standard data objects. Max 25MB.
        </div>
      </div>
    </div>
  );
};