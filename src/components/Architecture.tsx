import SectionHeading from './SectionHeading'

interface NodeProps {
  title: string
  tooltip: string
  tone?: 'neutral' | 'accent'
}

function Node({ title, tooltip, tone = 'neutral' }: NodeProps) {
  return (
    <div className="group relative">
      <div
        className={`flex min-w-[180px] items-center justify-center rounded-xl border px-5 py-3.5 text-center font-mono text-sm transition-colors ${
          tone === 'accent'
            ? 'border-violet/50 bg-violet/10 text-violet-glow group-hover:border-violet'
            : 'border-edge bg-surface2 text-slate-200 group-hover:border-cyan/60'
        }`}
      >
        {title}
      </div>
      <div className="pointer-events-none absolute left-1/2 top-full z-10 mt-2 w-56 -translate-x-1/2 rounded-lg border border-edge bg-surface px-3 py-2 text-center font-body text-xs text-muted opacity-0 shadow-xl transition-opacity duration-150 group-hover:opacity-100">
        {tooltip}
      </div>
    </div>
  )
}

function VerticalArrow() {
  return (
    <svg width="14" height="28" viewBox="0 0 14 28" fill="none" className="my-1">
      <path d="M7 0V22" stroke="#2DD4FF" strokeWidth="1.5" />
      <path d="M2 17L7 23L12 17" stroke="#2DD4FF" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

export default function Architecture() {
  return (
    <section id="architecture" className="scroll-mt-24 border-t border-edge/60 bg-void py-20 sm:py-28">
      <div className="mx-auto max-w-4xl px-6">
        <SectionHeading
          align="center"
          eyebrow="System Architecture"
          title="How the layers fit together"
          description="Hover any node to see what it does. Both detectors run before the user ever sees a model response."
        />

        <div className="mt-14 flex flex-col items-center">
          <Node title="User" tooltip="The person or system sending a request to your AI assistant." />
          <VerticalArrow />

          <div className="w-full rounded-2xl border border-violet/30 bg-violet/5 p-6">
            <p className="mb-4 text-center font-mono text-[11px] uppercase tracking-wider text-violet-glow">
              AI Shield Layer
            </p>
            <div className="flex flex-col items-center justify-center gap-4 sm:flex-row">
              <Node
                tone="accent"
                title="Jailbreak Detector"
                tooltip="Screens incoming prompts for instruction-override and manipulation patterns."
              />
              <Node
                tone="accent"
                title="Data Leak Scanner"
                tooltip="Scans model output for API keys, passwords, tokens, and confidential phrases."
              />
            </div>
          </div>

          <VerticalArrow />
          <Node title="Protected AI Assistant" tooltip="The underlying model, now operating on filtered, vetted input." />
          <VerticalArrow />
          <Node title="Safe Output" tooltip="A response with no leaked secrets and no successful manipulation." />
        </div>
      </div>
    </section>
  )
}
