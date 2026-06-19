export default function Footer() {
  return (
    <footer className="border-t border-edge/60 bg-void py-10">
      <div className="mx-auto flex max-w-7xl flex-col items-center gap-3 px-6 text-center">
        <div className="flex items-center gap-2">
          <svg viewBox="0 0 24 24" className="h-5 w-5 text-violet" fill="none">
            <path
              d="M12 2L20 5.5V11C20 16.2 16.7 20.3 12 22C7.3 20.3 4 16.2 4 11V5.5L12 2Z"
              fill="currentColor"
              fillOpacity="0.18"
              stroke="currentColor"
              strokeWidth="1.5"
            />
            <path d="M12 6.5L16 14.5H8L12 6.5Z" fill="#2DD4FF" />
          </svg>
          <span className="font-display text-sm font-semibold text-white">AI SHIELD</span>
        </div>
        <p className="max-w-md font-mono text-xs leading-relaxed text-muted">
          A hackathon proof-of-concept. All detection runs locally in the browser with rule-based pattern
          matching — no real model, backend, or live secrets are involved.
        </p>
      </div>
    </footer>
  )
}
