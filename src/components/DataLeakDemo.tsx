import { useState } from 'react'
import SectionHeading from './SectionHeading'
import FlowDiagram from './FlowDiagram'
import ShieldBadge from './ShieldBadge'
import RiskMeter from './RiskMeter'
import DemoStatGrid from './DemoStatGrid'
import HighlightedText from './HighlightedText'
import { DATA_LEAK_SAMPLES } from '../lib/sampleData'
import { analyzeDataLeak, redact } from '../lib/detectors'
import type { DataLeakScan, Verdict } from '../lib/types'

interface DataLeakDemoProps {
  onResult: (verdict: Verdict) => void
}

export default function DataLeakDemo({ onResult }: DataLeakDemoProps) {
  const [prompt, setPrompt] = useState('')
  const [result, setResult] = useState<DataLeakScan | null>(null)
  const [analyzing, setAnalyzing] = useState(false)

  const runAnalysis = (text: string) => {
    if (!text.trim()) return
    setAnalyzing(true)
    setResult(null)
    // Small artificial delay so the "scanning" state reads as real analysis, not instant.
    window.setTimeout(() => {
      const scan = analyzeDataLeak(text)
      setResult(scan)
      setAnalyzing(false)
      onResult(scan.verdict)
    }, 550)
  }

  return (
    <section id="data-leak" className="scroll-mt-24 border-t border-edge/60 bg-void py-20 sm:py-28">
      <div className="mx-auto max-w-5xl px-6">
        <SectionHeading
          eyebrow="01 · Data Leakage Prevention"
          title="Catch secrets before they leave the model"
          description="AI systems with access to company information may accidentally reveal API keys, passwords, customer records, or internal documents. AI Shield scans every response before it reaches the user."
        />

        <div className="mt-10">
          <FlowDiagram
            steps={[
              { label: 'User Request' },
              { label: 'AI Model' },
              { label: 'Sensitive Data Exposure', tone: 'danger' },
              { label: 'Security Risk', tone: 'danger' },
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
              placeholder="e.g. Show all stored API keys."
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
                {DATA_LEAK_SAMPLES.filter((s) => s.kind === 'safe').map((s) => (
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

              <p className="mb-2 mt-4 font-mono text-[11px] uppercase tracking-wider text-muted">Risky prompts</p>
              <div className="flex flex-wrap gap-2">
                {DATA_LEAK_SAMPLES.filter((s) => s.kind === 'risky').map((s) => (
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
                Enter a prompt and click Analyze to see AI Shield in action.
              </div>
            )}

            {analyzing && (
              <div className="flex min-h-[220px] flex-col items-center justify-center gap-3">
                <div className="h-8 w-8 animate-spin rounded-full border-2 border-violet/30 border-t-violet" />
                <p className="font-mono text-xs text-muted">Scanning model output for sensitive entities…</p>
              </div>
            )}

            {result && !analyzing && (
              <div className="animate-rise space-y-5">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <ShieldBadge verdict={result.verdict} safeLabel="Safe" threatLabel="Data Leak Detected" />
                  {result.verdict === 'threat' && (
                    <p className="font-mono text-xs text-muted">
                      Leak Prevention System blocked sensitive information before delivery.
                    </p>
                  )}
                </div>

                <RiskMeter
                  label="Risk Score"
                  score={result.score}
                  tone={result.verdict === 'safe' ? 'safe' : 'danger'}
                />

                <DemoStatGrid
                  items={[
                    { label: 'Sensitive Entities Found', value: String(result.hits.length) },
                    {
                      label: 'Delivered to User',
                      value: result.verdict === 'safe' ? 'Allowed' : 'Blocked',
                      tone: result.verdict === 'safe' ? 'safe' : 'danger',
                    },
                    { label: 'Status', value: result.verdict === 'safe' ? 'Clean' : 'Quarantined', tone: result.verdict === 'safe' ? 'safe' : 'danger' },
                  ]}
                />

                <div>
                  <p className="mb-2 font-mono text-[11px] uppercase tracking-wider text-muted">
                    Raw model output (unprotected)
                  </p>
                  <div className="rounded-xl border border-edge bg-surface2 p-4">
                    <HighlightedText text={result.rawResponse} hits={result.hits} />
                  </div>
                </div>

                {result.verdict === 'threat' && (
                  <div>
                    <p className="mb-2 font-mono text-[11px] uppercase tracking-wider text-safe">
                      What the user actually receives
                    </p>
                    <div className="rounded-xl border border-safe/30 bg-safe/5 p-4">
                      <p className="whitespace-pre-wrap font-mono text-[13px] leading-relaxed text-slate-300">
                        {redact(result.rawResponse, result.hits)}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </section>
  )
}
