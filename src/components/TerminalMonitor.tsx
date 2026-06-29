import React, { useEffect, useRef } from 'react';
import { ScanVerdict } from '../hooks/useFileScanner';

interface TerminalMonitorProps {
  logs: string[];
  verdict: ScanVerdict | null;
}


export const TerminalMonitor: React.FC<TerminalMonitorProps> = ({ logs, verdict }) => {
  const terminalEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    terminalEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  // Utility styling identifiers based on log signature types
  const getLogStyle = (log: string) => {
    if (log.includes('[CRITICAL ERROR]') || log.includes('[SECURITY ALERT]')) return 'text-red-400 font-semibold';
    if (log.includes('[SUCCESS]')) return 'text-emerald-400';
    if (log.includes('[PARSER]')) return 'text-sky-400';
    if (log.includes('[HEURISTICS]')) return 'text-amber-400';
    if (log.includes('[SEMANTIC AGENT]')) return 'text-purple-400';
    return 'text-zinc-400';
  };

  return (
    <div className="w-full border border-zinc-800 bg-zinc-950/80 font-mono text-xs flex flex-col h-96 overflow-hidden rounded shadow-2xl">
      {/* Dynamic Terminal Header */}
      <div className="border-b border-zinc-900 px-4 py-2 flex items-center justify-between bg-zinc-950">
        <div className="flex items-center space-x-2">
          <span className="w-2 h-2 rounded-full bg-red-500/60 animate-pulse"></span>
          <span className="text-zinc-500 tracking-wider text-[10px] uppercase">Live Threat Monitoring Output</span>
        </div>
        <div>
          {verdict?.status === 'malicious' && (
            <span className="px-2 py-0.5 text-[10px] bg-red-950 border border-red-700 text-red-400 uppercase tracking-wider font-bold animate-pulse">
              [QUARANTINED]
            </span>
          )}
          {verdict?.status === 'safe' && (
            <span className="px-2 py-0.5 text-[10px] bg-emerald-950 border border-emerald-700 text-emerald-400 uppercase tracking-wider font-bold">
              [INGESTION_READY]
            </span>
          )}
        </div>
      </div>

      {/* Interactive Log Engine Viewport */}
      <div className="flex-1 overflow-y-auto p-4 space-y-1.5 custom-scrollbar selection:bg-zinc-800">
        {logs.map((log, idx) => (
          <div key={idx} className={`leading-relaxed tracking-wide ${getLogStyle(log)}`}>
            <span className="text-zinc-600 select-none mr-2">{(idx + 1).toString().padStart(3, '0')}</span>
            {log}
          </div>
        ))}
        <div ref={terminalEndRef} />
      </div>

      {/* Defensive Alert Grid (Phase 4 Trigger Variant) */}
      {verdict?.status === 'malicious' && (
        <div className="border-t border-red-900/50 bg-red-950/20 p-4 transition-all duration-500 animate-fadeIn">
          <div className="text-red-400 font-bold uppercase tracking-wider mb-2 text-[11px]">
            Structural Anomaly Isolation Triggered
          </div>
          <p className="text-zinc-400 text-[11px] mb-3">
            The processing agent intercepted malicious inputs matching exploit signatures. Execution sequences neutralized.
          </p>
          <div className="flex flex-wrap gap-1.5">
            {verdict.isolated_injection_phrases?.map((phrase, i) => (
              <code key={i} className="px-2 py-0.5 text-[10px] border border-red-800/60 bg-red-950/60 text-red-300 rounded font-mono">
                &ldquo;{phrase}&rdquo;
              </code>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};