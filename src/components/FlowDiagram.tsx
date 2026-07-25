interface FlowStep {
  label: string
  tone?: 'neutral' | 'danger'
}

interface FlowDiagramProps {
  steps: FlowStep[]
}

export default function FlowDiagram({ steps }: FlowDiagramProps) {
  return (
    <div className="flex flex-col items-stretch gap-3 sm:flex-row sm:items-center sm:gap-0">
      {steps.map((step, i) => (
        <div key={step.label} className="flex flex-1 items-center">
          <div
            className={`flex w-full items-center justify-center rounded-xl border px-4 py-3.5 text-center font-mono text-sm ${
              step.tone === 'danger'
                ? 'border-danger/40 bg-danger/10 text-danger'
                : 'border-edge bg-surface2 text-slate-200'
            }`}
          >
            {step.label}
          </div>
          {i < steps.length - 1 && (
            <div className="hidden shrink-0 px-3 sm:block">
              <svg width="28" height="14" viewBox="0 0 28 14" fill="none">
                <path d="M0 7H25" stroke="#7C5CFF" strokeWidth="1.5" />
                <path d="M20 2L26 7L20 12" stroke="#7C5CFF" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </div>
          )}
          {i < steps.length - 1 && (
            <div className="flex justify-center py-1 sm:hidden">
              <svg width="14" height="22" viewBox="0 0 14 22" fill="none">
                <path d="M7 0V18" stroke="#7C5CFF" strokeWidth="1.5" />
                <path d="M2 13L7 19L12 13" stroke="#7C5CFF" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
