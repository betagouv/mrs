/* global describe, jest, test, expect */

import jsdom from 'jsdom'
const { JSDOM } = jsdom
import SubmitUi from './submit-ui.js'

const domFixture = () => new JSDOM()
const submitUiFactory = () => new SubmitUi(
  domFixture().window.document.querySelector('body'))

describe('submit-ui dom tests', () => {
  test('showSubmitLoading', () => {
    const submitUi = submitUiFactory()
    submitUi.createOverlay()
    const overlay = submitUi.mountPoint.querySelectorAll('div')

    expect(overlay.length).toEqual(2)
    expect(overlay[0].style.position).toEqual('fixed')
  })

  test('showOverlay()', () => {
    const submitUi = submitUiFactory()
    submitUi.showOverlay()

    const overlay = submitUi.mountPoint.querySelectorAll('div')[0]
    expect(overlay.style.opacity).toBe('1')
    expect(overlay.style.pointerEvents).toBe('inherit')
  })

  test('hideOverlay()', () => {
    const submitUi = submitUiFactory()
    submitUi.hideOverlay()

    const overlay = submitUi.mountPoint.querySelectorAll('div')[0]
    expect(overlay.style.opacity).toBe('0')
    expect(overlay.style.pointerEvents).toBe('none')
  })

  test('showSubmitLoading()', () => {
    const submitUi = submitUiFactory()
    submitUi.removeOverlayContent = jest.fn()
    submitUi.showOverlay = jest.fn()

    submitUi.showSubmitLoading()

    expect(submitUi.removeOverlayContent.mock.calls).toEqual([[]])
    expect(submitUi.showOverlay.mock.calls).toEqual([[]])
    expect(submitUi.overlay.querySelectorAll('div').length).toBe(2)
  })

  test('showSubmitError()', () => {
    const submitUi = submitUiFactory()
    submitUi.removeOverlayContent = jest.fn()
    submitUi.showOverlay = jest.fn()

    const errorMsg = 'error'
    const mockCallback = jest.fn()
    submitUi.showSubmitError(errorMsg, mockCallback)

    expect(submitUi.removeOverlayContent.mock.calls).toEqual([[]])
    expect(submitUi.showOverlay.mock.calls).toEqual([[]])
    expect(submitUi.overlay.querySelectorAll('div').length).toBe(2)
    expect(submitUi.overlay.querySelectorAll('div')[0].innerHTML)
      .toEqual(errorMsg)

      // error button events
    const errorButton = submitUi.overlay
      .querySelector('#submit-ui-error-button')

    errorButton.onmouseenter()
    expect(errorButton.style.backgroundColor)
      .toEqual('rgba(0, 0, 0, 0.7)')

    errorButton.onmouseleave()
    expect(errorButton.style.backgroundColor)
      .toEqual('rgba(0, 0, 0, 0)')

    submitUi.hideOverlay = jest.fn()
    errorButton.onclick()
    expect(submitUi.hideOverlay.mock.calls)
      .toEqual([[]])
    expect(mockCallback.mock.calls)
      .toEqual([[]])
  })

  test('showSubmitSuccess()', () => {
    const submitUi = submitUiFactory()
    submitUi.removeOverlayContent = jest.fn()
    submitUi.showOverlay = jest.fn()

    const successMsg = 'Success !'
    submitUi.showSubmitSuccess(successMsg)

    expect(submitUi.removeOverlayContent.mock.calls).toEqual([[]])
    expect(submitUi.showOverlay.mock.calls).toEqual([[]])
    expect(submitUi.overlay.querySelectorAll('div').length).toBe(2)
    expect(submitUi.overlay.querySelectorAll('div')[1].innerHTML)
      .toEqual(successMsg)
  })

  test('removeOverlayContent', () => {
    const submitUi = submitUiFactory()

    // test when overlay is already empty
    submitUi.removeOverlayContent()

    expect(submitUi.overlay.querySelectorAll('div').length).toBe(0)

    // test when overlay has content
    submitUi.showSubmitLoading()
    submitUi.removeOverlayContent()

    expect(submitUi.overlay.querySelectorAll('div').length).toBe(0)
  })
})
