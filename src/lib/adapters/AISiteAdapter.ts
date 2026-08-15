/**
 * AI Site Adapters — common abstraction for detecting and reading the prompt
 * composer on supported AI assistant sites (ChatGPT, Claude, Gemini).
 *
 * Issue #54 goal: standardize prompt/composer detection across the supported
 * AI websites behind a single, platform-independent interface so that consumers
 * never need platform-specific logic.
 *
 * Design rules enforced by every adapter in this folder:
 *  - READ-ONLY: adapters may query and read the DOM but MUST NEVER mutate it
 *    (no append/prepend/remove, no class/style/attribute changes, no event
 *    dispatch or simulated clicks/submits).
 *  - RESILIENT: no single fragile CSS class is relied upon. Each adapter tries
 *    an ordered list of stable selectors (stable ids → data-testid →
 *    aria/semantic → contenteditable → legacy <textarea>) and the first match
 *    wins.
 *  - NORMALIZED: extracted text is collapsed, trimmed, and returned as a plain
 *    string for every platform.
 *  - STATELESS: adapters hold no state and never persist, log, or transmit the
 *    user's prompt.
 *
 * Consumers should depend only on the {@link AISiteAdapter} interface and the
 * {@link getSiteAdapter} factory; platform-specific DOM details live behind the
 * adapter classes (see ChatGPTAdapter / ClaudeAdapter / GeminiAdapter).
 */

/**
 * A platform adapter locates and reads the prompt composer for one AI assistant
 * site. The contract is intentionally minimal:
 *
 * detectComposer()  -> HTMLElement | null   (null when the UI can't be found)
 * extractPrompt()   -> string               (always a string; "" when none)
 *
 * Implementations MUST be side-effect free with respect to the DOM.
 */
export interface AISiteAdapter {
  /** Stable, human-readable platform identifier, e.g. "ChatGPT". */
  readonly name: string

  /**
   * Locates the prompt composer element for this platform.
   *
   * @returns the composer element, or `null` when it cannot be found (e.g. the
   * site's UI has changed or the page is not the supported site). Performs only
   * read-only `querySelector` calls.
   */
  detectComposer(): HTMLElement | null

  /**
   * Extracts the current prompt text from the detected composer.
   *
   * @returns a normalized, trimmed plain string. Returns `""` when no composer
   * is present or no prompt text could be read. Never returns `null`/`undefined`.
   */
  extractPrompt(): string
}

/**
 * Normalizes whitespace consistently across all platforms:
 *  - collapses every run of whitespace (spaces, tabs, newlines) into a single
 *    space
 *  - strips leading/trailing whitespace
 *  - coerces `null` / `undefined` to an empty string
 *
 * @returns a plain string (never `null` / `undefined`).
 */
export function normalizeWhitespace(text: string | null | undefined): string {
  return (text ?? '').replace(/\s+/g, ' ').trim()
}

/**
 * Reads the textual value of a composer element WITHOUT mutating it.
 *
 * Behavior:
 *  - `<textarea>` / `<input>`: returns the control's current `.value`.
 *  - anything else (typically a `contenteditable` region): performs a read-only
 *    walk of the subtree collecting text nodes, treating `<br>` as a newline,
 *    and **skipping** subtrees marked `aria-hidden="true"` so that CSS-only
 *    placeholder/hint text is never reported as user input.
 *
 * The DOM is never modified: this is a purely read-only traversal.
 *
 * @returns a normalized plain string.
 */
export function collectComposerText(el: HTMLElement | null): string {
  if (!el) return ''

  // Form controls expose their current text via the `value` IDL attribute.
  if (el instanceof HTMLTextAreaElement || el instanceof HTMLInputElement) {
    return normalizeWhitespace(el.value ?? '')
  }

  // contenteditable / generic element: walk the subtree (read-only).
  const parts: string[] = []

  const visit = (node: Node): void => {
    if (node.nodeType === Node.TEXT_NODE) {
      parts.push(node.textContent ?? '')
      return
    }
    if (node.nodeType !== Node.ELEMENT_NODE) return

    const element = node as Element
    // Skip decorative/placeholder subtrees hidden from assistive tech.
    if (element.getAttribute('aria-hidden') === 'true') return
    if (element.nodeName.toUpperCase() === 'BR') {
      parts.push('\n')
      return
    }

    // If a nested form control exists, prefer its current value.
    if (element instanceof HTMLTextAreaElement || element instanceof HTMLInputElement) {
      parts.push(element.value ?? '')
      return
    }

    for (const child of Array.from(element.childNodes)) visit(child)
  }

  visit(el)
  return normalizeWhitespace(parts.join(''))
}

/**
 * Returns the first element matching the first selector (in order) that yields a
 * match. This is the backbone of each adapter's fallback strategy.
 *
 * Performs only read-only `querySelector` calls — safe to use against
 * `document` or any element root.
 *
 * @param root      `document` (or any element) to scope the search.
 * @param selectors Ordered list of CSS selectors evaluated strictly in order.
 * @returns the first matching element as an `HTMLElement`, or `null`.
 */
export function queryFirstSelector(
  root: Document | HTMLElement,
  selectors: readonly string[],
): HTMLElement | null {
  for (const selector of selectors) {
    const match = root.querySelector(selector)
    if (match) return match as HTMLElement
  }
  return null
}
