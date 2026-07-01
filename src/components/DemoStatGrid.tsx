interface StatItem {
  label: string
  value: string
  tone?: 'safe' | 'danger' | 'neutral'
}

interface DemoStatGridProps {
  items: StatItem[]
}

export default function DemoStatGrid({ items }: DemoStatGridProps) {
  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
      {items.map((item) => (
        <div key={item.label} className="rounded-xl border border-edge bg-surface2 px-4 py-3">
          <p className="font-mono text-[11px] uppercase tracking-wider text-muted">{item.label}</p>
          <p
            className={`mt-1.5 font-display text-xl font-semibold ${
              item.tone === 'safe' ? 'text-safe' : item.tone === 'danger' ? 'text-danger' : 'text-white'
            }`}
          >
            {item.value}
          </p>
        </div>
      ))}
    </div>
  )
}

