import { collectComposerText, queryFirstSelector } from './AISiteAdapter'
import type { AISiteAdapter } from './AISiteAdapter'

/**
 * Read-only adapter for the ChatGPT web UI (chatgpt.com / chat.openai.com).
 *
 * ChatGPT's composer is a `contenteditable` region inside the stable `#composer`
 * container. Modern builds expose a `data-testid="composer"` annotation, while
 * older builds used a `<textarea id="prompt">`. Selectors are evaluated in
 * priority order (stable id → data-testid → aria/semantic → legacy textarea) and
 * the first match wins.
 *
 * @see AISiteAdapter
 */
const CHATGPT_COMPOSER_SELECTORS = [
  '#composer [contenteditable="true"]', // stable id + contenteditable input
  '[data-testid="composer"] [contenteditable="true"]', // modern annotated build
  'form[aria-label] [contenteditable="true"]', // aria-scoped fallback
  'textarea#prompt', // legacy textarea composer
  'textarea[name="prompt"]', // legacy fallback
] as const

export class ChatGPTAdapter implements AISiteAdapter {
  readonly name = 'ChatGPT'

  detectComposer(): HTMLElement | null {
    return queryFirstSelector(document, CHATGPT_COMPOSER_SELECTORS)
  }

  extractPrompt(): string {
    return collectComposerText(this.detectComposer())
  }
}
