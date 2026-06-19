import { useCountUp } from '../hooks/useCountUp'
import SectionHeading from './SectionHeading'
import type { ShieldStats } from '../lib/types'

interface CombinedDashboardProps {
  stats: ShieldStats
}

function StatCard({ label, value, accent }: { label: string; value: number; accent: string }) {
  const display = useCountUp(value)
  return (
    <div className="panel relative overflow-hidden p-6">
      <div className={`absolute inset-x-0 top-0 h-0.5 ${accent}`} />
      <p className="font-mono text-[11px] uppercase tracking-wider text-muted">{label}</p>
      <p className="mt-3 font-display text-4xl font-semibold text-white tabular-nums">{display}</p>
    </div>
  )
}

export default function CombinedDashboard({ stats }: CombinedDashboardProps) {
  const total = stats.dataLeaksBlocked + stats.jailbreaksDetected + stats.safeRequests
  const protectionScore = total === 0 ? 100 : Math.round((stats.safeRequests / total) * 40 + 60)

  return (
    <section id="dashboard" className="scroll-mt-24 border-t border-edge/60 bg-void py-20 sm:py-28">
      <div className="mx-auto max-w-5xl px-6">
        <SectionHeading
          eyebrow="Security Overview"
          title="One console, both threat types"
          description="Every prompt you've analyzed above feeds this live monitoring screen — the same view a security team would watch in production."
        />

        <div className="mt-12 grid grid-cols-2 gap-4 lg:grid-cols-4">
          <StatCard label="Data Leak Attempts Blocked" value={stats.dataLeaksBlocked} accent="bg-danger" />
          <StatCard label="Jailbreak Attempts Detected" value={stats.jailbreaksDetected} accent="bg-violet" />
          <StatCard label="Safe Requests Processed" value={stats.safeRequests} accent="bg-safe" />
          <StatCard label="Overall Protection Score" value={protectionScore} accent="bg-cyan" />
        </div>

        {total === 0 && (
          <p className="mt-6 text-center font-mono text-xs text-muted">
            Run the demos above to see these numbers move in real time.
          </p>
        )}
      </div>
    </section>
  )
}
