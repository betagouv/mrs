/* global describe, jest, test, expect */


import jsdom from 'jsdom'

describe('smoke test', () => {
  test('should open a page', () => {
    const { JSDOM } = jsdom
    return JSDOM.fromURL(
      'http://localhost:8000',
      {
        resources: "usable",
        runScripts:'dangerously'
      }
    ).then(dom => {
      return new Promise(resolve => {
        dom.window.document.addEventListener('DOMContentLoaded', () => resolve(dom))
      })
    }).then(dom => {
      let display = dom.window.document.querySelector('#mrsrequest-wizard').style.display
      dom.window.close()
      expect(display).toEqual('')
    })
  })
})

