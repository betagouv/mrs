import ScrollReveal from 'scrollreveal'
import '../sass/landing.sass'
import '../sass/form.sass'
import '../sass/animations.sass'
import './mrsrequest'
import './contact'

// Preact imports
import { h as React, render } from 'preact'
import Header from './components/Header.js'


(($) => {
  const sr = ScrollReveal()
  sr.reveal('.scroll-reveal')

  $('body').on('click', '[data-callback=scroll-to]', function() {
    var $target = $($(this).attr('data-target'))

    $('html, body').animate({
      scrollTop: $target.offset().top + 'px'
    }, 'fast')
  })

  render(<Header />, document.getElementById('header'))

})(window.jQuery)
