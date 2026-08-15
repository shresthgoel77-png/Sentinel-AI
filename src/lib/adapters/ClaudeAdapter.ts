import { collectComposerText, queryFirstSelector } from './AISiteAdapter'
import type { AISiteAdapter } from './AISiteAdapter'

/**
 * Read-only adapter for the Claude web UI (claude.ai).
 *
 * Claude's composer is a `contenteditable` region. Modern builds annotate it
 * with a `data-testid`, while the input is also identifiable by its accessible
 * `role="textbox"`. Selectors are evaluated in priority order
 * (data-testid → aria/semantic → legacy textarea) and the first match wins.
 *
 * @see AISiteAdapter
 */
const CLAUDE_COMPOSER_SELECTORS = [
  '[data-testid="chat-input-text-area"]', // Claude's annotated composer region
  '[data-testid="chat-input-area"] [contenteditable="true"]', // wrapper + contenteditable
  'form[aria-label] [contenteditable="true"]', // aria-scoped fallback
  'div[contenteditable="true"][role="textbox"]', // accessibility + contenteditable fallback
  'textarea#prompt', // legacy fallback
  'textarea[name="prompt"]', // legacy fallback
] as const

export class ClaudeAdapter implements AISiteAdapter {
  readonly name = 'Claude'

  detectComposer(): HTMLElement | null {
    return queryFirstSelector(document, CLAUDE_COMPOSER_SELECTORS)
  }

  extractPrompt(): string {
    return collectComposerText(this.detectComposer())
  }
}
