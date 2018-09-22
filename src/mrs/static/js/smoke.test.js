/* global describe, jest, test, expect, process */


import jsdom from 'jsdom'
const { JSDOM } = jsdom

var display = (dom, selector) => dom.window.document.querySelector(selector).style.display

var HOST = process.env.HOST || 'localhost:8000'

function fetch(url) {
  return JSDOM.fromURL(
    'http://' + HOST + url,
    {
      resources: 'usable',
      runScripts:'dangerously'
    }
  ).then(dom => {
    return new Promise(resolve => {
      dom.window.document.addEventListener('DOMContentLoaded', () => resolve(dom))
    })
  })
}

describe('smoke tests', () => {
  test('index should display contact and mrsrequest forms', () => {
    return fetch('/').then(dom => {
      let contact = display(dom, '#contact')
      dom.window.close()
      expect(contact).toEqual('')
    })
  })

  test('contact should display contact form', () => {
    return fetch('/contact').then(dom => {
      let contact = display(dom, '#contact')
      dom.window.close()
      expect(contact).toEqual('')
    })
  })

  test('demande page should show form', () => {
    return fetch('/demande').then(dom => {
      let mrsrequest = display(dom, '#mrsrequest-wizard')
      dom.window.close()
      expect(mrsrequest).toEqual('')
    })
  })

  test('institution iframe', () => {
    return fetch('/institution/310000000/mrsrequest/iframe/').then(dom => {
      let mrsrequest = display(dom, '#mrsrequest-wizard')
      dom.window.close()
      expect(mrsrequest).toEqual('')
    })
  })
})
