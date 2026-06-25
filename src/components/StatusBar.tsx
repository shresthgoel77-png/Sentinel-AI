import type { ShieldStats } from '../lib/types';

interface StatusBarProps {
  stats: ShieldStats;
}

export default function StatusBar({ stats }: StatusBarProps) {
  return (
    <div className="sticky top-0 z-50 border-b border-edge bg-surface/80 backdrop-blur-md">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-3">
        <div className="flex items-center gap-3">
          <div className="h-2 w-2 rounded-full bg-safe animate-pulse shadow-[0_0_8px_rgba(45,212,255,0.8)]" />
          <span className="font-mono text-sm tracking-wide text-slate-300">
            SENTINEL CORE ONLINE
          </span>
        </div>

        <div className="flex gap-8 font-mono text-sm hidden md:flex">
          <div className="flex flex-col items-end">
            <span className="text-slate-500 text-xs uppercase tracking-wider">Total Scans</span>
            <span className="text-cyan">{stats.totalScans}</span>
          </div>
          <div className="flex flex-col items-end">
            <span className="text-slate-500 text-xs uppercase tracking-wider">Safe Requests</span>
            <span className="text-safe">{stats.safeRequests}</span>
          </div>
          <div className="flex flex-col items-end">
            <span className="text-slate-500 text-xs uppercase tracking-wider">Threats Blocked</span>
            <span className="text-danger">{stats.threatsBlocked}</span>
          </div>
        </div>
      </div>
    </div>
  );
}