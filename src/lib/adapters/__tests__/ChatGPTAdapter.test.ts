import { beforeEach, describe, expect, it } from 'vitest'
import { ChatGPTAdapter } from '../ChatGPTAdapter'
import { expectNoDOMMutation } from './testUtils'

beforeEach(() => {
  document.body.innerHTML = ''
})

describe('ChatGPTAdapter', () => {
  const adapter = new ChatGPTAdapter()

  it('exposes the common interface contract', () => {
    expect(adapter.name).toBe('ChatGPT')
    expect(typeof adapter.detectComposer).toBe('function')
    expect(typeof adapter.extractPrompt).toBe('function')
  })

  it('detects a valid composer via the primary (#composer) selector', () => {
    document.body.innerHTML =
      '<div id="composer"><div contenteditable="true">Hello ChatGPT</div></div>'
    const composer = adapter.detectComposer()
    expect(composer).not.toBeNull()
    expect(composer).toBe(document.querySelector('#composer [contenteditable="true"]'))
  })

  it('extracts and normalizes the prompt text', () => {
    document.body.innerHTML =
      '<div id="composer"><div contenteditable="true">  Hello\nChatGPT  </div></div>'
    expect(adapter.extractPrompt()).toBe('Hello ChatGPT')
  })

  it('returns null when the composer is absent', () => {
    document.body.innerHTML = '<div>some unrelated page content</div>'
    expect(adapter.detectComposer()).toBeNull()
    expect(adapter.extractPrompt()).toBe('')
  })

  it('returns an empty prompt for an empty composer', () => {
    document.body.innerHTML = '<div id="composer"><div contenteditable="true"></div></div>'
    expect(adapter.detectComposer()).not.toBeNull()
    expect(adapter.extractPrompt()).toBe('')
  })

  it('returns an empty prompt for a composer containing only a line break', () => {
    document.body.innerHTML = '<div id="composer"><div contenteditable="true"><br></div></div>'
    expect(adapter.extractPrompt()).toBe('')
  })

  it('falls back through the ordered selectors to the legacy textarea', () => {
    // Primary contenteditable selectors are absent; the legacy textarea wins.
    document.body.innerHTML = '<textarea id="prompt">Legacy prompt</textarea>'
    const composer = adapter.detectComposer()
    expect(composer).not.toBeNull()
    expect(composer).toBe(document.getElementById('prompt'))
    expect(adapter.extractPrompt()).toBe('Legacy prompt')
  })

  it('does not modify the DOM while detecting or extracting', () => {
    document.body.innerHTML =
      '<div id="composer"><div contenteditable="true">Read only please</div></div>'
    expectNoDOMMutation(() => {
      adapter.detectComposer()
      adapter.extractPrompt()
    })
  })
})
