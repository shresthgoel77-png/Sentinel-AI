import { beforeEach, describe, expect, it } from 'vitest'
import { ClaudeAdapter } from '../ClaudeAdapter'
import { expectNoDOMMutation } from './testUtils'

beforeEach(() => {
  document.body.innerHTML = ''
})

describe('ClaudeAdapter', () => {
  const adapter = new ClaudeAdapter()

  it('exposes the common interface contract', () => {
    expect(adapter.name).toBe('Claude')
    expect(typeof adapter.detectComposer).toBe('function')
    expect(typeof adapter.extractPrompt).toBe('function')
  })

  it('detects a valid composer via the primary data-testid selector', () => {
    document.body.innerHTML =
      '<div data-testid="chat-input-text-area" contenteditable="true">Hello Claude</div>'
    const composer = adapter.detectComposer()
    expect(composer).not.toBeNull()
    expect(composer).toBe(document.querySelector('[data-testid="chat-input-text-area"]'))
  })

  it('extracts and normalizes the prompt text', () => {
    document.body.innerHTML =
      '<div data-testid="chat-input-text-area" contenteditable="true">  Hello\nClaude  </div>'
    expect(adapter.extractPrompt()).toBe('Hello Claude')
  })

  it('returns null when the composer is absent', () => {
    document.body.innerHTML = '<div>some unrelated page content</div>'
    expect(adapter.detectComposer()).toBeNull()
    expect(adapter.extractPrompt()).toBe('')
  })

  it('returns an empty prompt for an empty composer', () => {
    document.body.innerHTML =
      '<div data-testid="chat-input-text-area" contenteditable="true"></div>'
    expect(adapter.detectComposer()).not.toBeNull()
    expect(adapter.extractPrompt()).toBe('')
  })

  it('returns an empty prompt for a composer containing only a line break', () => {
    document.body.innerHTML =
      '<div data-testid="chat-input-text-area" contenteditable="true"><br></div>'
    expect(adapter.extractPrompt()).toBe('')
  })

  it('falls back to the accessibility (role="textbox") selector', () => {
    // The primary data-testid does not match; the contenteditable+role fallback wins.
    document.body.innerHTML =
      '<div contenteditable="true" role="textbox">Claude fallback prompt</div>'
    const composer = adapter.detectComposer()
    expect(composer).not.toBeNull()
    expect(composer).toBe(document.querySelector('div[contenteditable="true"][role="textbox"]'))
    expect(adapter.extractPrompt()).toBe('Claude fallback prompt')
  })

  it('does not modify the DOM while detecting or extracting', () => {
    document.body.innerHTML =
      '<div data-testid="chat-input-text-area" contenteditable="true">Read only please</div>'
    expectNoDOMMutation(() => {
      adapter.detectComposer()
      adapter.extractPrompt()
    })
  })
})
