interface RiskMeterProps {
  label: string
  score: number
  tone: 'safe' | 'danger'
}


export default function RiskMeter({ label, score, tone }: RiskMeterProps) {
  return (
    <div>
      <div className="mb-1.5 flex items-center justify-between">
        <span className="font-mono text-[11px] uppercase tracking-wider text-muted">{label}</span>
        <span className={`font-mono text-sm font-semibold ${tone === 'safe' ? 'text-safe' : 'text-danger'}`}>
          {score}/100
        </span>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-surface2">
        <div
          className={`h-full rounded-full transition-all duration-700 ease-out ${
            tone === 'safe' ? 'bg-safe' : 'bg-danger'
          }`}
          style={{ width: `${score}%` }}
        />
      </div>
    </div>
  )
}
