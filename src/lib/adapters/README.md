# AI Site Adapters

A small, read-only abstraction for detecting and reading the prompt composer on
the supported AI assistant sites (ChatGPT, Claude, Gemini). See
`AISiteAdapter.ts` and `Issue #54`.

## Common interface

Every adapter implements `AISiteAdapter`:

```ts
export interface AISiteAdapter {
  readonly name: string
  detectComposer(): HTMLElement | null   // null when not found
  extractPrompt(): string                // always a string; "" when none
}
```

The rest of the extension should depend **only** on this interface and the
`getSiteAdapter` factory — never on a platform-specific class.

## Supported platforms

| Platform  | Module            | Hostnames                          |
| --------- | ----------------- | ---------------------------------- |
| ChatGPT   | `ChatGPTAdapter`  | `chatgpt.com`, `chat.openai.com`   |
| Claude    | `ClaudeAdapter`   | `claude.ai`                        |
| Gemini    | `GeminiAdapter`   | `gemini.google.com`, `gemini.google`, `bard.google.com` |

## Selecting an adapter

Selection is centralized in `getSiteAdapter(hostname?)` (see `index.ts`) so
hostname checks are never scattered. It reads `window.location.hostname` by
default and returns the matching adapter instance, or `null` for unsupported
sites.

```
hostname → getSiteAdapter → AISiteAdapter → concrete adapter
```

## Selector fallback strategy

No single fragile CSS class is relied upon. Each adapter keeps an ordered list
of selectors evaluated strictly in order; the first match wins:

1. **Stable element identifiers** (`id`, `data-testid`).
2. **Accessibility / semantic attributes** (`role`, `aria-label`, `aria-hidden`,
   `contenteditable`).
3. **`contenteditable` fallbacks** (the real input element on modern UIs).
4. **Legacy `<textarea>` / `<input>` fallbacks** (older builds).

Because selectors are best-effort (the live DOM cannot be verified at compile
time), the fallback chain itself is the resilience mechanism.

## Read-only DOM requirement

Adapters are strictly read-only. They may **query** and **read** the DOM
(`querySelector`, `.value`, `.textContent`, attribute reads) but must **never**
mutate it: no `appendChild`/`append`/`prepend`/`remove`/`removeChild/`
`replaceWith`, no `classList`/`style`/`setAttribute` changes, no
`dispatchEvent` or `click()`. The shared helpers (`collectComposerText`,
`queryFirstSelector`, `normalizeWhitespace`) uphold this by construction, and the
test suite asserts it explicitly.

## Prompt normalization

All platforms normalize extracted text the same way (`normalizeWhitespace`):
whitespace runs (spaces, tabs, newlines) collapse to a single space, leading
and trailing whitespace is trimmed, and `null`/`undefined` coerce to `""`.
`aria-hidden="true"` subtrees are excluded during extraction so placeholder/hint
text is never reported as the user's prompt.
