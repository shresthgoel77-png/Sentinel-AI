import { collectComposerText, queryFirstSelector } from './AISiteAdapter'
import type { AISiteAdapter } from './AISiteAdapter'

/**
 * Read-only adapter for the Gemini web UI (gemini.google.com / gemini.google).
 *
 * Gemini's composer is a `contenteditable` region, historically rooted under a
 * container with a stable id (`#chat-text-area` / `#chatTextarea`) or an
 * accessible `role="textbox"` element. Selectors are evaluated in priority order
 * (stable id → data-testid → aria/semantic → legacy textareas) and the first
 * match wins.
 *
 * @see AISiteAdapter
 */
const GEMINI_COMPOSER_SELECTORS = [
  '#chat-text-area [contenteditable="true"]', // stable container + contenteditable input
  '#chatTextarea', // stable id on the editable itself (container or control)
  '#chat-textarea-container [contenteditable="true"]', // alternate container id
  '[data-testid="chat-input-area"] [contenteditable="true"]', // annotated build
  'div[contenteditable="true"][role="textbox"]', // accessibility + contenteditable fallback
  'textarea[name="prompt"]', // legacy fallback
  'textarea#prompt', // legacy fallback
] as const

export class GeminiAdapter implements AISiteAdapter {
  readonly name = 'Gemini'

  detectComposer(): HTMLElement | null {
    return queryFirstSelector(document, GEMINI_COMPOSER_SELECTORS)
  }

  extractPrompt(): string {
    return collectComposerText(this.detectComposer())
  }
}
