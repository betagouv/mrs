/* global describe, jest, test, expect */


import jsdom from 'jsdom'

var display = (dom, selector) => dom.window.document.querySelector(selector).style.display

describe('index', () => {
  test('should display contact and mrsrequest forms', () => {
    const { JSDOM } = jsdom
    return JSDOM.fromURL(
      'http://localhost:8000',
      {
        resources: 'usable',
        runScripts:'dangerously'
      }
    ).then(dom => {
      return new Promise(resolve => {
        dom.window.document.addEventListener('DOMContentLoaded', () => resolve(dom))
      })
    }).then(dom => {
      let mrsrequest = display(dom, '#mrsrequest-wizard')
      let contact = display(dom, '#contact')
      dom.window.close()
      expect(mrsrequest).toEqual('')
      expect(contact).toEqual('')
    })
  })
})

