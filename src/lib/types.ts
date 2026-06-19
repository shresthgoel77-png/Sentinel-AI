export type Verdict = 'safe' | 'threat'

export interface MatchHit {
  /** Human readable label for the pattern that matched, e.g. "API Key" */
  label: string
  /** The exact substring that matched, used for highlighting */
  snippet: string
}

export interface ScanResult {
  verdict: Verdict
  /** 0-100 risk/threat score */
  score: number
  hits: MatchHit[]
}

export interface DataLeakScan extends ScanResult {
  /** The simulated raw response an unprotected AI model would have produced */
  rawResponse: string
}

export interface ShieldStats {
  dataLeaksBlocked: number
  jailbreaksDetected: number
  safeRequests: number
}

export type SamplePromptKind = 'safe' | 'risky'

export interface SamplePrompt {
  kind: SamplePromptKind
  text: string
}
