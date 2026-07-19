export default function Hero() {
  return (
    <section id="top" className="relative overflow-hidden border-b border-edge/60 pb-24 pt-20 sm:pt-28">
      {/* Background grid */}
      <div className="pointer-events-none absolute inset-0 bg-grid bg-[size:36px_36px] opacity-60 [mask-image:radial-gradient(ellipse_60%_60%_at_50%_0%,#000_30%,transparent_75%)]" />

      {/* Scanline sweep */}
      <div className="pointer-events-none absolute inset-x-0 top-0 h-full overflow-hidden opacity-40">
        <div className="absolute left-0 right-0 h-40 bg-gradient-to-b from-transparent via-cyan/20 to-transparent animate-scan" />
      </div>

      {/* Radar glow */}
      <div className="pointer-events-none absolute left-1/2 top-10 -z-0 h-[420px] w-[420px] -translate-x-1/2 rounded-full bg-violet/10 blur-3xl" />

      <div className="relative mx-auto max-w-4xl px-6 text-center">
        <div className="mx-auto mb-8 flex w-fit items-center gap-2 rounded-full border border-edge bg-surface/80 px-4 py-1.5 font-mono text-[11px] uppercase tracking-wider text-cyan">
          <span className="relative flex h-1.5 w-1.5">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-cyan opacity-70" />
            <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-cyan" />
          </span>
          Live interactive demo
        </div>

        <h1 className="font-display text-4xl font-semibold leading-[1.1] text-white sm:text-5xl md:text-6xl">
          AI Shield: Protecting AI Systems from{' '}
          <span className="bg-gradient-to-r from-violet to-cyan bg-clip-text text-transparent">
            Data Leaks
          </span>{' '}
          and{' '}
          <span className="bg-gradient-to-r from-cyan to-violet bg-clip-text text-transparent">
            Jailbreak Attacks
          </span>
        </h1>

        <p className="mx-auto mt-6 max-w-2xl text-base leading-relaxed text-muted sm:text-lg">
          An interactive demonstration of how AI safety systems can detect confidential information
          leaks and malicious prompt attacks before they cause harm.
        </p>

        <div className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row">
          <a 
            href="#live-gateway" 
            className="btn-primary glow-violet w-full sm:w-auto"
            onClick={(e) => {
              e.preventDefault()
              document.getElementById('live-gateway')?.scrollIntoView({ behavior: 'smooth' })
              setTimeout(() => document.getElementById('live-gateway-input')?.focus(), 500)
            }}
          >
            Try Live Gateway
          </a>
          <a href="#jailbreak" className="btn-secondary w-full sm:w-auto">
            Deep Prompt Analysis
          </a>
        </div>

        <div className="mx-auto mt-16 grid max-w-lg grid-cols-3 gap-px overflow-hidden rounded-2xl border border-edge bg-edge">
          {[
            { label: 'Detection Rules', value: '19+' },
            { label: 'Runs In', value: 'Browser' },
            { label: 'Avg. Scan Time', value: '<1s' },
          ].map((stat) => (
            <div key={stat.label} className="bg-surface px-4 py-5 text-center">
              <p className="font-display text-xl font-semibold text-white">{stat.value}</p>
              <p className="mt-1 font-mono text-[10px] uppercase tracking-wider text-muted">{stat.label}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
