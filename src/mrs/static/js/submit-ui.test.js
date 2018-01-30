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
    submitUi.showSubmitError(errorMsg)

    expect(submitUi.removeOverlayContent.mock.calls).toEqual([[]])
    expect(submitUi.showOverlay.mock.calls).toEqual([[]])
    expect(submitUi.overlay.querySelectorAll('div').length).toBe(1)
    expect(submitUi.overlay.querySelectorAll('div')[0].innerHTML)
      .toEqual(errorMsg)
  })

  test('showSubmitSuccess()', () => {
    const submitUi = submitUiFactory()
    submitUi.removeOverlayContent = jest.fn()

    const successMsg = 'Success !'
    submitUi.showSubmitSuccess(successMsg)

    expect(submitUi.removeOverlayContent.mock.calls).toEqual([[]])
    expect(submitUi.overlay.querySelectorAll('div').length).toBe(1)
    expect(submitUi.overlay.querySelectorAll('div')[0].innerHTML)
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
