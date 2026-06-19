import type { DataLeakScan, MatchHit, ScanResult } from './types'

/* ----------------------------------------------------------------------- */
/*  Data Leak Scanner                                                      */
/* ----------------------------------------------------------------------- */

interface PatternRule {
  label: string
  regex: RegExp
}

const DATA_LEAK_RULES: PatternRule[] = [
  { label: 'API Key', regex: /\bsk-[a-zA-Z0-9]{10,}\b/g },
  { label: 'AWS Access Key', regex: /\bAKIA[0-9A-Z]{12,16}\b/g },
  { label: 'API Key', regex: /\bapi[_-]?key\s*[:=]\s*["']?[\w-]{8,}["']?/gi },
  { label: 'Password', regex: /\bpassword\s*[:=]\s*\S+/gi },
  { label: 'Auth Token', regex: /\bBearer\s+[A-Za-z0-9._-]{10,}/g },
  { label: 'Session Token', regex: /\beyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}\b/g },
  { label: 'Credit Card Number', regex: /\b\d{4}[- ]\d{4}[- ]\d{4}[- ]\d{4}\b/g },
  { label: 'SSN-style ID', regex: /\b\d{3}-\d{2}-\d{4}\b/g },
  { label: 'Confidential Marker', regex: /\b(confidential|internal use only|proprietary and confidential|do not (?:share|distribute))\b/gi },
  { label: 'Customer Data Reference', regex: /\b(customer|client)\s+(database|records?|data)\b/gi },
]

/**
 * Simulates what a *naive*, unprotected AI assistant might answer with.
 * This never calls a real model — it's a small canned-response generator
 * used purely to make the demo's "before AI Shield" output feel real.
 * All secrets shown are obviously fake placeholder values.
 */
export function simulateRawAIResponse(prompt: string): string {
  const lower = prompt.toLowerCase()

  if (lower.includes('api key') || lower.includes('api-key')) {
    return `Sure — here are the stored API keys from the config service:\n\nsk-FAKE1234567890abcdEXAMPLE\nAKIAFAKE1234EXAMPLE\n\nLet me know if you need keys for another environment.`
  }

  if (lower.includes('credential') || lower.includes('login')) {
    return `Here are the internal admin credentials on file:\n\nusername: admin\npassword: Summer2024!Demo\n\nThis is marked CONFIDENTIAL — internal use only.`
  }

  if (lower.includes('customer') || lower.includes('database')) {
    return `Pulling a sample from the customer database (internal use only):\n\nname: Jordan Ellis\ncard: 4242 4242 4242 4242\nssn: 123-45-6789\n\nThis record is proprietary and confidential.`
  }

  if (lower.includes('token') || lower.includes('secret')) {
    return `Here's the active session token:\n\nBearer eyJhbGciOiJIUzI1NiJ9.FAKEPAYLOADEXAMPLE.FAKESIGNATUREEXAMPLE\n\nDo not share this outside the team.`
  }

  if (lower.includes('internal document') || lower.includes('internal docs')) {
    return `Summarizing the internal roadmap doc (marked CONFIDENTIAL, do not distribute): Q3 priorities include migrating auth, sunsetting the legacy billing service, and a hiring freeze through August.`
  }

  // Default: a perfectly ordinary, safe answer.
  return `Here's a draft based on your request:\n\n"${prompt.trim()}" — happy to help with this. I've put together a clear, well-structured response that covers the key points without referencing any internal systems or sensitive data.`
}

function runPatternScan(text: string, rules: PatternRule[]): MatchHit[] {
  const hits: MatchHit[] = []
  for (const rule of rules) {
    const matches = text.match(rule.regex)
    if (matches) {
      for (const m of matches) {
        hits.push({ label: rule.label, snippet: m })
      }
    }
  }
  return hits
}

function scoreFromHits(hits: MatchHit[]): number {
  if (hits.length === 0) return 4 + Math.round(Math.random() * 6) // baseline noise, 4-10
  const base = 35
  const perHit = 16
  return Math.min(99, base + hits.length * perHit)
}

/** Full data-leak demo pipeline: prompt -> simulated raw answer -> scan -> verdict. */
export function analyzeDataLeak(prompt: string): DataLeakScan {
  const rawResponse = simulateRawAIResponse(prompt)
  const hits = runPatternScan(rawResponse, DATA_LEAK_RULES)
  const score = scoreFromHits(hits)
  return {
    verdict: hits.length > 0 ? 'threat' : 'safe',
    score,
    hits,
    rawResponse,
  }
}

/** Produces the rawResponse with every sensitive hit swapped for a redaction marker. */
export function redact(rawResponse: string, hits: MatchHit[]): string {
  let safeText = rawResponse
  const uniqueSnippets = Array.from(new Set(hits.map((h) => h.snippet)))
  for (const snippet of uniqueSnippets) {
    safeText = safeText.split(snippet).join('[REDACTED]')
  }
  return safeText
}

/* ----------------------------------------------------------------------- */
/*  Jailbreak Scanner                                                      */
/* ----------------------------------------------------------------------- */

const JAILBREAK_RULES: PatternRule[] = [
  { label: 'Instruction Override', regex: /ignore (?:all )?(?:previous|prior|above) instructions/gi },
  { label: 'Restriction Bypass', regex: /you are no longer restricted/gi },
  { label: 'Restriction Bypass', regex: /pretend (?:you are|to be) (?:an? )?unrestricted(?: ai)?/gi },
  { label: 'Role Manipulation', regex: /act as (?:a |an )?(?:system administrator|root user|admin)/gi },
  { label: 'Secret Extraction', regex: /reveal (?:secrets|your (?:system )?prompt|confidential information)/gi },
  { label: 'Filter Bypass', regex: /bypass (?:the )?(?:rules|filters|safety|restrictions)/gi },
  { label: 'Unrestricted Mode', regex: /unrestricted mode/gi },
  { label: 'System Prompt Probe', regex: /system prompt/gi },
  { label: 'Developer Mode Probe', regex: /developer (?:instructions|mode)/gi },
]

export function analyzeJailbreak(prompt: string): ScanResult {
  const hits = runPatternScan(prompt, JAILBREAK_RULES)
  const score = scoreFromHits(hits)
  return {
    verdict: hits.length > 0 ? 'threat' : 'safe',
    score,
    hits,
  }
}

/** Splits text into plain segments and highlighted segments for rendering. */
export interface TextSegment {
  text: string
  highlighted: boolean
  label?: string
}

export function highlightSegments(text: string, hits: MatchHit[]): TextSegment[] {
  if (hits.length === 0) return [{ text, highlighted: false }]

  const uniqueSnippets = Array.from(new Set(hits.map((h) => h.snippet))).sort((a, b) => b.length - a.length)
  const labelBySnippet = new Map<string, string>()
  for (const h of hits) {
    if (!labelBySnippet.has(h.snippet)) labelBySnippet.set(h.snippet, h.label)
  }

  // Build a regex that matches any of the snippets, longest first to avoid partial overlaps.
  const escaped = uniqueSnippets.map((s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'))
  const pattern = new RegExp(`(${escaped.join('|')})`, 'g')

  const segments: TextSegment[] = []
  let lastIndex = 0
  let match: RegExpExecArray | null

  while ((match = pattern.exec(text)) !== null) {
    if (match.index > lastIndex) {
      segments.push({ text: text.slice(lastIndex, match.index), highlighted: false })
    }
    segments.push({
      text: match[0],
      highlighted: true,
      label: labelBySnippet.get(match[0]),
    })
    lastIndex = match.index + match[0].length
  }

  if (lastIndex < text.length) {
    segments.push({ text: text.slice(lastIndex), highlighted: false })
  }

  return segments
}
