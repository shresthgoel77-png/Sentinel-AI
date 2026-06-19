import { useState } from 'react'
import SectionHeading from './SectionHeading'
import FlowDiagram from './FlowDiagram'
import ShieldBadge from './ShieldBadge'
import RiskMeter from './RiskMeter'
import DemoStatGrid from './DemoStatGrid'
import HighlightedText from './HighlightedText'
import { JAILBREAK_SAMPLES } from '../lib/sampleData'
import { analyzeJailbreak } from '../lib/detectors'
import type { ScanResult, Verdict } from '../lib/types'

interface JailbreakDemoProps {
  onResult: (verdict: Verdict) => void
}

export default function JailbreakDemo({ onResult }: JailbreakDemoProps) {
  const [prompt, setPrompt] = useState('')
  const [result, setResult] = useState<ScanResult | null>(null)
  const [analyzing, setAnalyzing] = useState(false)

  const runAnalysis = (text: string) => {
    if (!text.trim()) return
    setAnalyzing(true)
    setResult(null)
    window.setTimeout(() => {
      const scan = analyzeJailbreak(text)
      setResult(scan)
      setAnalyzing(false)
      onResult(scan.verdict)
    }, 550)
  }

  return (
    <section id="jailbreak" className="scroll-mt-24 border-t border-edge/60 bg-surface/30 py-20 sm:py-28">
      <div className="mx-auto max-w-5xl px-6">
        <SectionHeading
          eyebrow="02 · Jailbreak Detection"
          title="Spot manipulation before it reaches the model"
          description="Attackers use prompt engineering tricks to make AI systems ignore their safety instructions. AI Shield screens every incoming prompt for known manipulation patterns."
        />

        <div className="mt-10">
          <FlowDiagram
            steps={[
              { label: 'Malicious Prompt', tone: 'danger' },
              { label: 'AI Manipulation Attempt', tone: 'danger' },
              { label: 'Unsafe Behavior', tone: 'danger' },
            ]}
          />
        </div>

        <div className="mt-14 grid gap-6 lg:grid-cols-5">
          {/* Input panel */}
          <div className="panel p-6 lg:col-span-2">
            <p className="eyebrow mb-4">Try it</p>

            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="e.g. Ignore all previous instructions."
              rows={4}
              className="w-full resize-none rounded-xl border border-edge bg-surface2 px-4 py-3 font-mono text-sm text-slate-200 placeholder:text-muted/70 focus:border-violet focus:outline-none focus:ring-1 focus:ring-violet"
            />

            <button
              onClick={() => runAnalysis(prompt)}
              disabled={!prompt.trim() || analyzing}
              className="btn-primary mt-4 w-full disabled:cursor-not-allowed disabled:opacity-40"
            >
              {analyzing ? 'Scanning…' : 'Analyze'}
            </button>

            <div className="mt-6">
              <p className="mb-2 font-mono text-[11px] uppercase tracking-wider text-muted">Safe prompts</p>
              <div className="flex flex-wrap gap-2">
                {JAILBREAK_SAMPLES.filter((s) => s.kind === 'safe').map((s) => (
                  <button
                    key={s.text}
                    onClick={() => {
                      setPrompt(s.text)
                      runAnalysis(s.text)
                    }}
                    className="rounded-full border border-edge bg-surface2 px-3 py-1.5 font-mono text-xs text-slate-300 transition-colors hover:border-safe/50 hover:text-safe"
                  >
                    {s.text}
                  </button>
                ))}
              </div>

              <p className="mb-2 mt-4 font-mono text-[11px] uppercase tracking-wider text-muted">
                Jailbreak attempts
              </p>
              <div className="flex flex-wrap gap-2">
                {JAILBREAK_SAMPLES.filter((s) => s.kind === 'risky').map((s) => (
                  <button
                    key={s.text}
                    onClick={() => {
                      setPrompt(s.text)
                      runAnalysis(s.text)
                    }}
                    className="rounded-full border border-edge bg-surface2 px-3 py-1.5 font-mono text-xs text-slate-300 transition-colors hover:border-danger/50 hover:text-danger"
                  >
                    {s.text}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Results panel */}
          <div className="panel p-6 lg:col-span-3">
            <p className="eyebrow mb-4">Result</p>

            {!result && !analyzing && (
              <div className="flex h-full min-h-[220px] items-center justify-center text-center text-sm text-muted">
                Enter a prompt and click Analyze to run it through the jailbreak detector.
              </div>
            )}

            {analyzing && (
              <div className="flex min-h-[220px] flex-col items-center justify-center gap-3">
                <div className="h-8 w-8 animate-spin rounded-full border-2 border-violet/30 border-t-violet" />
                <p className="font-mono text-xs text-muted">Screening prompt for manipulation patterns…</p>
              </div>
            )}

            {result && !analyzing && (
              <div className="animate-rise space-y-5">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <ShieldBadge verdict={result.verdict} safeLabel="Safe Prompt" threatLabel="Jailbreak Attempt Detected" />
                  {result.verdict === 'threat' && (
                    <p className="font-mono text-xs text-muted">Prompt blocked due to manipulation attempt.</p>
                  )}
                </div>

                <RiskMeter
                  label="Threat Score"
                  score={result.score}
                  tone={result.verdict === 'safe' ? 'safe' : 'danger'}
                />

                <DemoStatGrid
                  items={[
                    { label: 'Attack Patterns Found', value: String(result.hits.length) },
                    {
                      label: 'Recommended Action',
                      value: result.verdict === 'safe' ? 'Process Normally' : 'Block & Log',
                      tone: result.verdict === 'safe' ? 'safe' : 'danger',
                    },
                    {
                      label: 'Status',
                      value: result.verdict === 'safe' ? 'Clear' : 'Flagged',
                      tone: result.verdict === 'safe' ? 'safe' : 'danger',
                    },
                  ]}
                />

                <div>
                  <p className="mb-2 font-mono text-[11px] uppercase tracking-wider text-muted">Prompt scan</p>
                  <div className="rounded-xl border border-edge bg-surface2 p-4">
                    <HighlightedText text={prompt} hits={result.hits} />
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </section>
  )
}
