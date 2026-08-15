import { expect, vi } from 'vitest'

/**
 * Safety helper for the read-only contract (Issue #54 / requirement #6 & #16).
 *
 * Asserts that running `action` does not modify the real DOM by verifying two
 * things:
 *  1. A focused set of known mutation / event methods were never invoked
 *     (appendChild, setAttribute, remove, classList mutations, click,
 *     dispatchEvent, ...).
 *  2. The serialized document body is byte-for-byte identical before and after
 *     (any structural / attribute change would alter the serialized HTML).
 *
 * Spies are installed on the global prototypes only for the duration of `action`
 * and are always restored afterwards.
 */
export function expectNoDOMMutation(action: () => void): void {
  const setAttribute = vi.spyOn(Element.prototype, 'setAttribute')
  const setAttributeNS = vi.spyOn(Element.prototype, 'setAttributeNS')
  const removeElement = vi.spyOn(Element.prototype, 'remove')
  const replaceWith = vi.spyOn(Element.prototype, 'replaceWith')
  const appendChild = vi.spyOn(Node.prototype, 'appendChild')
  const removeChild = vi.spyOn(Node.prototype, 'removeChild')
  const replaceChild = vi.spyOn(Node.prototype, 'replaceChild')
  const classListAdd = vi.spyOn(DOMTokenList.prototype, 'add')
  const classListRemove = vi.spyOn(DOMTokenList.prototype, 'remove')
  const classListToggle = vi.spyOn(DOMTokenList.prototype, 'toggle')
  const click = vi.spyOn(HTMLElement.prototype, 'click')
  const dispatchEvent = vi.spyOn(EventTarget.prototype, 'dispatchEvent')

  const guards: Array<() => void> = [
    () => expect(setAttribute).not.toHaveBeenCalled(),
    () => expect(setAttributeNS).not.toHaveBeenCalled(),
    () => expect(removeElement).not.toHaveBeenCalled(),
    () => expect(replaceWith).not.toHaveBeenCalled(),
    () => expect(appendChild).not.toHaveBeenCalled(),
    () => expect(removeChild).not.toHaveBeenCalled(),
    () => expect(replaceChild).not.toHaveBeenCalled(),
    () => expect(classListAdd).not.toHaveBeenCalled(),
    () => expect(classListRemove).not.toHaveBeenCalled(),
    () => expect(classListToggle).not.toHaveBeenCalled(),
    () => expect(click).not.toHaveBeenCalled(),
    () => expect(dispatchEvent).not.toHaveBeenCalled(),
  ]

  const restore: Array<() => void> = [
    () => setAttribute.mockRestore(),
    () => setAttributeNS.mockRestore(),
    () => removeElement.mockRestore(),
    () => replaceWith.mockRestore(),
    () => appendChild.mockRestore(),
    () => removeChild.mockRestore(),
    () => replaceChild.mockRestore(),
    () => classListAdd.mockRestore(),
    () => classListRemove.mockRestore(),
    () => classListToggle.mockRestore(),
    () => click.mockRestore(),
    () => dispatchEvent.mockRestore(),
  ]

  const before = document.body.innerHTML
  try {
    action()
  } finally {
    try {
      for (const guard of guards) guard()
      expect(document.body.innerHTML).toBe(before)
    } finally {
      for (const fn of restore) fn()
    }
  }
}
