import { h as React, render } from 'preact'

import Header from './components/Header.js'

(() => {
  render(<Header isFat={ true } />, document.getElementById('header'))
})()
