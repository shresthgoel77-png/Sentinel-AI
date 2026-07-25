import type { MatchHit } from '../lib/types'
import { highlightSegments } from '../lib/detectors'

interface HighlightedTextProps {
  text: string
  hits: MatchHit[]
  tone?: 'danger'
}

export default function HighlightedText({ text, hits }: HighlightedTextProps) {
  const segments = highlightSegments(text, hits)

  return (
    <p className="whitespace-pre-wrap font-mono text-[13px] leading-relaxed text-slate-300">
      {segments.map((seg, i) =>
        seg.highlighted ? (
          <mark key={i} title={seg.label} className="mark-leak">
            {seg.text}
          </mark>
        ) : (
          <span key={i}>{seg.text}</span>
        ),
      )}
    </p>
  )
}
