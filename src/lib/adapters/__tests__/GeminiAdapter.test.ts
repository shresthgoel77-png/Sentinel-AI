import { beforeEach, describe, expect, it } from 'vitest'
import { GeminiAdapter } from '../GeminiAdapter'
import { expectNoDOMMutation } from './testUtils'

beforeEach(() => {
  document.body.innerHTML = ''
})

describe('GeminiAdapter', () => {
  const adapter = new GeminiAdapter()

  it('exposes the common interface contract', () => {
    expect(adapter.name).toBe('Gemini')
    expect(typeof adapter.detectComposer).toBe('function')
    expect(typeof adapter.extractPrompt).toBe('function')
  })

  it('detects a valid composer via the primary (#chat-text-area) selector', () => {
    document.body.innerHTML =
      '<div id="chat-text-area"><div contenteditable="true">Hello Gemini</div></div>'
    const composer = adapter.detectComposer()
    expect(composer).not.toBeNull()
    expect(composer).toBe(
      document.querySelector('#chat-text-area [contenteditable="true"]'),
    )
  })

  it('extracts and normalizes the prompt text', () => {
    document.body.innerHTML =
      '<div id="chat-text-area"><div contenteditable="true">  Hello\nGemini  </div></div>'
    expect(adapter.extractPrompt()).toBe('Hello Gemini')
  })

  it('returns null when the composer is absent', () => {
    document.body.innerHTML = '<div>some unrelated page content</div>'
    expect(adapter.detectComposer()).toBeNull()
    expect(adapter.extractPrompt()).toBe('')
  })

  it('returns an empty prompt for an empty composer', () => {
    document.body.innerHTML =
      '<div id="chat-text-area"><div contenteditable="true"></div></div>'
    expect(adapter.detectComposer()).not.toBeNull()
    expect(adapter.extractPrompt()).toBe('')
  })

  it('returns an empty prompt for a composer containing only a line break', () => {
    document.body.innerHTML =
      '<div id="chat-text-area"><div contenteditable="true"><br></div></div>'
    expect(adapter.extractPrompt()).toBe('')
  })

  it('falls back through the ordered selectors to a legacy textarea', () => {
    // The primary contenteditable/id selectors do not match; the legacy
    // textarea (last in the ordered list) wins, proving the fallback chain.
    document.body.innerHTML = '<textarea name="prompt">Gemini legacy prompt</textarea>'
    const composer = adapter.detectComposer()
    expect(composer).not.toBeNull()
    expect(composer).toBe(document.querySelector('textarea[name="prompt"]'))
    expect(adapter.extractPrompt()).toBe('Gemini legacy prompt')
  })

  it('does not modify the DOM while detecting or extracting', () => {
    document.body.innerHTML =
      '<div id="chat-text-area"><div contenteditable="true">Read only please</div></div>'
    expectNoDOMMutation(() => {
      adapter.detectComposer()
      adapter.extractPrompt()
    })
  })
})
