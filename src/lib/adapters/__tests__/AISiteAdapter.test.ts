import { beforeEach, describe, expect, it } from 'vitest'
import {
  AISiteAdapter,
  ChatGPTAdapter,
  ClaudeAdapter,
  GeminiAdapter,
  collectComposerText,
  getSiteAdapter,
  normalizeHostname,
  normalizeWhitespace,
  queryFirstSelector,
} from '../index'
import { expectNoDOMMutation } from './testUtils'

beforeEach(() => {
  document.body.innerHTML = ''
})

/* ----------------------------------------------------------------------- *
 * Compile-time guarantee: every adapter is assignable to the common
 * interface. If any adapter drifts from the contract, `tsc` (run by the build)
 * fails to compile these assignments.
 * ----------------------------------------------------------------------- */
const _chat: AISiteAdapter = new ChatGPTAdapter()
const _claude: AISiteAdapter = new ClaudeAdapter()
const _gemini: AISiteAdapter = new GeminiAdapter()
void [_chat, _claude, _gemini]

describe('AISiteAdapter interface', () => {
  const adapters = [new ChatGPTAdapter(), new ClaudeAdapter(), new GeminiAdapter()]

  it('every adapter exposes the common interface contract', () => {
    for (const adapter of adapters) {
      expect(typeof adapter.name).toBe('string')
      expect(adapter.name.length).toBeGreaterThan(0)
      expect(typeof adapter.detectComposer).toBe('function')
      expect(typeof adapter.extractPrompt).toBe('function')
    }
  })

  it('detectComposer() returns an element when the composer exists', () => {
    document.body.innerHTML =
      '<div id="composer"><div contenteditable="true">Hello ChatGPT</div></div>'
    const adapter = new ChatGPTAdapter()
    expect(adapter.detectComposer()).not.toBeNull()
  })

  it('detectComposer() returns null when the composer does not exist', () => {
    document.body.innerHTML = '<div>nothing here</div>'
    const adapter = new ChatGPTAdapter()
    expect(adapter.detectComposer()).toBeNull()
  })

  it('extractPrompt() returns a normalized string', () => {
    document.body.innerHTML =
      '<div id="composer"><div contenteditable="true">  Hello\nChatGPT  </div></div>'
    const adapter = new ChatGPTAdapter()
    const prompt = adapter.extractPrompt()
    expect(typeof prompt).toBe('string')
    expect(prompt).toBe('Hello ChatGPT')
  })

  it('empty/missing composer yields an empty prompt string (never null/undefined)', () => {
    document.body.innerHTML = ''
    const adapter = new ChatGPTAdapter()
    expect(adapter.extractPrompt()).toBe('')
    expect(adapter.extractPrompt()).not.toBeNull()
    expect(adapter.extractPrompt()).not.toBeUndefined()
  })

  it('adapter execution does not mutate the DOM', () => {
    document.body.innerHTML =
      '<div id="composer"><div contenteditable="true">Read only please</div></div>'
    const adapter = new ChatGPTAdapter()
    expectNoDOMMutation(() => {
      adapter.detectComposer()
      adapter.extractPrompt()
    })
  })
})

describe('normalizeWhitespace', () => {
  it('collapses whitespace runs and trims', () => {
    expect(normalizeWhitespace('  hello   world  ')).toBe('hello world')
  })

  it('collapses newlines and tabs', () => {
    expect(normalizeWhitespace('line1\nline2\tindented')).toBe('line1 line2 indented')
  })

  it('coerces null / undefined / empty to an empty string', () => {
    expect(normalizeWhitespace(null)).toBe('')
    expect(normalizeWhitespace(undefined)).toBe('')
    expect(normalizeWhitespace('')).toBe('')
    expect(normalizeWhitespace('   ')).toBe('')
  })
})

describe('collectComposerText', () => {
  it('reads the value of a textarea', () => {
    document.body.innerHTML = '<textarea>  Prompt text  </textarea>'
    const el = document.querySelector('textarea') as HTMLElement
    expect(collectComposerText(el)).toBe('Prompt text')
  })

  it('reads text from a contenteditable element', () => {
    document.body.innerHTML = '<div contenteditable="true">Hello World</div>'
    const el = document.querySelector('[contenteditable="true"]') as HTMLElement
    expect(collectComposerText(el)).toBe('Hello World')
  })

  it('treats <br> as a newline then normalizes it', () => {
    document.body.innerHTML = '<div contenteditable="true">Hello<br>World</div>'
    const el = document.querySelector('[contenteditable="true"]') as HTMLElement
    expect(collectComposerText(el)).toBe('Hello World')
  })

  it('skips aria-hidden placeholder subtrees', () => {
    document.body.innerHTML =
      '<div contenteditable="true"><div aria-hidden="true">Placeholder hint</div><div>Real prompt</div></div>'
    const el = document.querySelector('[contenteditable="true"]') as HTMLElement
    expect(collectComposerText(el)).toBe('Real prompt')
  })

  it('returns an empty string for null', () => {
    expect(collectComposerText(null)).toBe('')
  })
})

describe('queryFirstSelector', () => {
  it('returns the element matched by the first applicable selector', () => {
    document.body.innerHTML =
      '<div id="composer"><div contenteditable="true">A</div></div>'
    const match = queryFirstSelector(document, [
      '#composer [contenteditable="true"]',
      'textarea#prompt',
    ])
    expect(match).not.toBeNull()
    expect(match).toBe(document.querySelector('#composer [contenteditable="true"]'))
  })

  it('falls through to the next selector in order', () => {
    document.body.innerHTML = '<textarea id="prompt">B</textarea>'
    const match = queryFirstSelector(document, [
      '#composer [contenteditable="true"]',
      'textarea#prompt',
    ])
    expect(match).toBe(document.getElementById('prompt'))
  })

  it('returns null when no selector matches', () => {
    document.body.innerHTML = '<div>other</div>'
    expect(queryFirstSelector(document, ['#composer', 'textarea#prompt'])).toBeNull()
  })
})

describe('getSiteAdapter (factory)', () => {
  it.each([
    ['chatgpt.com', ChatGPTAdapter],
    ['www.chatgpt.com', ChatGPTAdapter],
    ['chat.openai.com', ChatGPTAdapter],
    ['claude.ai', ClaudeAdapter],
    ['www.claude.ai', ClaudeAdapter],
    ['gemini.google.com', GeminiAdapter],
    ['gemini.google', GeminiAdapter],
    ['bard.google.com', GeminiAdapter],
  ])('returns the %s adapter for hostname %s', (host, expected) => {
    const adapter = getSiteAdapter(host)
    expect(adapter).not.toBeNull()
    expect(adapter).toBeInstanceOf(expected)
  })

  it('returns null for unsupported hostnames', () => {
    expect(getSiteAdapter('google.com')).toBeNull()
    expect(getSiteAdapter('example.com')).toBeNull()
  })

  it('returns null for an empty/blank hostname', () => {
    expect(getSiteAdapter('')).toBeNull()
    expect(getSiteAdapter('   ')).toBeNull()
  })
})

describe('normalizeHostname', () => {
  it('lower-cases, trims, and strips a leading www.', () => {
    expect(normalizeHostname('  WWW.ChatGPT.com  ')).toBe('chatgpt.com')
    expect(normalizeHostname('BARD.google.com')).toBe('bard.google.com')
  })

  it('leaves other hostnames untouched (besides normalization)', () => {
    expect(normalizeHostname('claude.ai')).toBe('claude.ai')
  })
})

