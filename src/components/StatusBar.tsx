import type { ShieldStats } from '../lib/types'

interface StatusBarProps {
  stats: ShieldStats
}

const NAV_LINKS = [
  { href: '#data-leak', label: 'Data Leak' },
  { href: '#jailbreak', label: 'Jailbreak' },
  { href: '#dashboard', label: 'Dashboard' },
  { href: '#simulation', label: 'Simulation' },
  { href: '#architecture', label: 'Architecture' },
  { href: '#judges', label: 'Why It Matters' },
]

export default function StatusBar({ stats }: StatusBarProps) {
  const totalScanned = stats.dataLeaksBlocked + stats.jailbreaksDetected + stats.safeRequests

  return (
    <header className="sticky top-0 z-50 border-b border-edge/80 bg-void/85 backdrop-blur-md">
      <div className="mx-auto flex max-w-7xl items-center gap-4 px-6 py-3">
        <a href="#top" className="flex shrink-0 items-center gap-2">
          <svg viewBox="0 0 24 24" className="h-6 w-6 text-violet" fill="none">
            <path
              d="M12 2L20 5.5V11C20 16.2 16.7 20.3 12 22C7.3 20.3 4 16.2 4 11V5.5L12 2Z"
              fill="currentColor"
              fillOpacity="0.18"
              stroke="currentColor"
              strokeWidth="1.5"
            />
            <path d="M12 6.5L16 14.5H8L12 6.5Z" fill="#2DD4FF" />
          </svg>
          <span className="font-display text-sm font-semibold tracking-wide text-white">AI SHIELD</span>
        </a>

        <nav className="hidden flex-1 items-center justify-center gap-6 lg:flex">
          {NAV_LINKS.map((link) => (
            <a
              key={link.href}
              href={link.href}
              className="font-mono text-xs uppercase tracking-wider text-muted transition-colors hover:text-cyan"
            >
              {link.label}
            </a>
          ))}
        </nav>

        <div className="ml-auto flex items-center gap-4 font-mono text-[11px] text-muted sm:gap-5">
          <span className="hidden items-center gap-1.5 sm:flex">
            <span className="relative flex h-1.5 w-1.5">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-safe opacity-60" />
              <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-safe" />
            </span>
            LIVE
          </span>
          <span>
            Scanned <span className="text-white">{totalScanned}</span>
          </span>
          <span className="hidden sm:inline">
            Blocked{' '}
            <span className="text-danger">{stats.dataLeaksBlocked + stats.jailbreaksDetected}</span>
          </span>
        </div>
      </div>
    </header>
  )
}
