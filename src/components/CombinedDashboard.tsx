import type { ShieldStats } from '../lib/types';

interface CombinedDashboardProps {
  stats: any;
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
          
          {/* Avg Latency Metric */}
          <div className="rounded-xl bg-void border border-edge p-6">
            <div className="text-slate-500 font-mono text-sm mb-2">Avg Execution Latency</div>
            <div className="flex items-baseline gap-2">
              <div className="text-4xl font-display font-bold text-cyan">
                {stats.averageLatencyMs || 0}
              </div>
              <span className="text-slate-500 font-mono text-sm">ms</span>
            </div>
          </div>
          
          {/* Global Risk Index */}
          <div className="rounded-xl bg-void border border-edge p-6">
            <div className="text-slate-500 font-mono text-sm mb-2">Global Risk Index</div>
            <div className="flex items-baseline gap-2">
              <div className="text-4xl font-display font-bold text-orange-400">
                {stats.averageRiskScore || 0}
              </div>
            </div>
          </div>
          
          {/* Total Tokens Protected */}
          <div className="rounded-xl bg-void border border-edge p-6">
            <div className="text-slate-500 font-mono text-sm mb-2">Tokens Processed</div>
            <div className="text-4xl font-display font-bold text-emerald-400">
              {stats.totalTokens || 0}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}