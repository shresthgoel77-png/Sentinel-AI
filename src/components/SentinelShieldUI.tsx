import React from 'react';
import { FileDropZone } from './FileDropZone';
import { TerminalMonitor } from './TerminalMonitor';
import { useFileScanner } from '../hooks/useFileScanner';


export const SentinelShieldUI: React.FC = () => {
  const { processAndUploadFile, isScanning, logs, verdict, setLogs } = useFileScanner();

  const handleClearLogs = () => {
    setLogs(['[SYSTEM] Logs cleared. Terminal listener online.']);
  };

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 p-8 flex flex-col justify-center items-center">
      <div className="w-full max-w-4xl space-y-6">
        
        {/* Core Identity Branding */}
        <div className="flex flex-col space-y-1 font-mono">
          <h1 className="text-sm tracking-[0.35em] uppercase text-zinc-200 font-semibold">
            SENTINEL AI // UI SHIELD EXTENSION
          </h1>
          <p className="text-[11px] text-zinc-500 uppercase tracking-widest">
            Module: Operational Phase 4 Continuous Sandbox Scanner
          </p>
        </div>

        <hr className="border-zinc-900" />

        {/* Input Interface Zone */}
        <FileDropZone 
          onFileAccepted={processAndUploadFile} 
          disabled={isScanning} 
        />

        {/* Console / Monitoring Station */}
        <div className="space-y-2">
          <div className="flex items-center justify-between font-mono text-[10px] text-zinc-500 px-1">
            <span>TERMINAL BUS: ACTIVE // SECURE CONSOLE ENGINE</span>
            <button 
              onClick={handleClearLogs}
              disabled={isScanning}
              className="hover:text-zinc-300 transition-colors tracking-widest uppercase disabled:opacity-30 disabled:pointer-events-none"
            >
              [Clear Screen]
            </button>
          </div>
          <TerminalMonitor logs={logs} verdict={verdict} />
        </div>
        
      </div>
    </div>
  );
};