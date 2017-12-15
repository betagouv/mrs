import ScrollReveal from 'scrollreveal'
import $ from 'jquery'

(() => {
  // datepicker needs jquery names `jQuery` in window global namespace
  window.jQuery = $
  // Materialize needs jquery names `$` in window global namespace
  window.$ = $

  const sr = ScrollReveal()
  sr.reveal('.scroll-reveal')
})()
