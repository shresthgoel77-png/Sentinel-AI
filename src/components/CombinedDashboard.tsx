import type { ShieldStats } from '../lib/types';

interface CombinedDashboardProps {
  stats: ShieldStats;
}

export default function CombinedDashboard({ stats }: CombinedDashboardProps) {
  const threatPercentage = stats.totalScans === 0 
    ? 0 
    : Math.round((stats.threatsBlocked / stats.totalScans) * 100);

  return (
    <section className="mx-auto max-w-6xl px-6 py-12">
      <div className="panel p-8 glow-violet">
        <h3 className="eyebrow mb-6 text-violet-400">System Analytics</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Threats Blocked Metric */}
          <div className="rounded-xl bg-void border border-edge p-6">
            <div className="text-slate-500 font-mono text-sm mb-2">Threats Neutralized</div>
            <div className="text-4xl font-display font-bold text-danger">
              {stats.threatsBlocked}
            </div>
          </div>

          {/* Safe Requests Metric */}
          <div className="rounded-xl bg-void border border-edge p-6">
            <div className="text-slate-500 font-mono text-sm mb-2">Verified Safe</div>
            <div className="text-4xl font-display font-bold text-safe">
              {stats.safeRequests}
            </div>
          </div>

          {/* Threat Ratio Metric */}
          <div className="rounded-xl bg-void border border-edge p-6">
            <div className="text-slate-500 font-mono text-sm mb-2">Threat Ratio</div>
            <div className="flex items-baseline gap-2">
              <div className="text-4xl font-display font-bold text-violet-400">
                {threatPercentage}%
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}