import type { Verdict } from '../lib/types'

interface ShieldBadgeProps {
  verdict: Verdict
  safeLabel?: string
  threatLabel?: string
}

export default function ShieldBadge({
  verdict,
  safeLabel = 'Safe',
  threatLabel = 'Threat Detected',
}: ShieldBadgeProps) {
  const isSafe = verdict === 'safe'

  return (
    <div
      className={`inline-flex items-center gap-2.5 rounded-full border px-4 py-2 font-display text-sm font-medium ${
        isSafe ? 'border-safe/40 bg-safe/10 text-safe' : 'border-danger/40 bg-danger/10 text-danger'
      }`}
    >
      <svg viewBox="0 0 24 24" className="h-4 w-4 shrink-0" fill="none">
        <path
          d="M12 2.5L20 6V12C20 17 16.5 20.8 12 22C7.5 20.8 4 17 4 12V6L12 2.5Z"
          fill="currentColor"
          fillOpacity="0.15"
          stroke="currentColor"
          strokeWidth="1.6"
        />
        {isSafe ? (
          <path d="M8.5 12.2L11 14.7L15.5 9.7" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
        ) : (
          <path d="M9.5 9L14.5 14M14.5 9L9.5 14" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
        )}
      </svg>
      {isSafe ? safeLabel : threatLabel}
    </div>
  )
}
