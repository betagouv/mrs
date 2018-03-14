import ScrollReveal from 'scrollreveal'
import '../sass/base.sass'
import '../sass/landing.sass'
import '../sass/base.sass'
import '../sass/form.sass'
import '../sass/animations.sass'
import './mrsrequest'
import './contact'
import initStatistics from './statistics.js'

// Preact imports
import { h as React, render } from 'preact'
import Header from './components/Header.js'


(($) => {
  let body = document.querySelector('body')

  const renderHeader = isFat => render(<Header isFat={ isFat } />, document.getElementById('header'))

  // show correct header based on path
  if(body.classList.contains('index')) {
    const sr = ScrollReveal()
    sr.reveal('.scroll-reveal')

    $('body').on('click', '[data-callback=scroll-to]', function() {
      var $target = $($(this).attr('data-target'))

      $('html, body').animate({
        scrollTop: $target.offset().top + 'px'
      }, 'fast')
    })

    // comment for now
    renderHeader(false)
  } else {
    renderHeader(true)
  }

  // use bodyclass to detect statistics
  if(body.classList.contains('statistics')) {
    initStatistics()
  }

})(window.jQuery)
