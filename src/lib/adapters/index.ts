import { ChatGPTAdapter } from './ChatGPTAdapter'
import { ClaudeAdapter } from './ClaudeAdapter'
import { GeminiAdapter } from './GeminiAdapter'
import type { AISiteAdapter } from './AISiteAdapter'

export type { AISiteAdapter } from './AISiteAdapter'
export { ChatGPTAdapter } from './ChatGPTAdapter'
export { ClaudeAdapter } from './ClaudeAdapter'
export { GeminiAdapter } from './GeminiAdapter'
export { collectComposerText, normalizeWhitespace, queryFirstSelector } from './AISiteAdapter'

/**
 * Centralized hostname → adapter routing table (Issue #54).
 *
 * Hostname logic lives ONLY here so it is never scattered across the codebase.
 * Each entry exposes a `match` predicate (operating on a normalized hostname) and
 * a `create` factory producing a fresh, stateless adapter instance.
 */
const HOSTNAME_ROUTING: ReadonlyArray<{
  match: (hostname: string) => boolean
  create: () => AISiteAdapter
}> = [
  {
    match: (host) => host === 'chatgpt.com' || host === 'chat.openai.com',
    create: () => new ChatGPTAdapter(),
  },
  {
    match: (host) => host === 'claude.ai',
    create: () => new ClaudeAdapter(),
  },
  {
    match: (host) =>
      host === 'gemini.google.com' ||
      host === 'gemini.google' ||
      host === 'bard.google.com',
    create: () => new GeminiAdapter(),
  },
]

/**
 * Normalizes a hostname for routing: trimmed, lower-cased, with a leading
 * `www.` stripped (e.g. `WWW.ChatGPT.com` → `chatgpt.com`).
 */
export function normalizeHostname(hostname: string): string {
  return hostname.trim().toLowerCase().replace(/^www\./, '')
}

/**
 * Selects the platform adapter appropriate for the given hostname.
 *
 * @param hostname Optional hostname override (mainly for testing). When omitted
 * the current `window.location.hostname` is used (guarded for non-browser
 * environments like SSR).
 * @returns the matching adapter instance, or `null` when the site is not one of
 * the supported AI assistants.
 *
 * hostname → adapter factory → AISiteAdapter → platform-specific implementation.
 */
export function getSiteAdapter(hostname?: string): AISiteAdapter | null {
  const host = hostname ?? (typeof window !== 'undefined' ? window.location.hostname : '')
  if (!host) return null

  const normalized = normalizeHostname(host)
  for (const entry of HOSTNAME_ROUTING) {
    if (entry.match(normalized)) return entry.create()
  }
  return null
}
