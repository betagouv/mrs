import ScrollReveal from 'scrollreveal'
import '../sass/landing.sass'
import '../sass/form.sass'
import '../sass/animations.sass'
import './mrsrequest'
import './contact'
import foo from './preact-test.js'

(($) => {
  const sr = ScrollReveal()
  sr.reveal('.scroll-reveal')

  $('body').on('click', '[data-callback=scroll-to]', function() {
    var $target = $($(this).attr('data-target'))

    $('html, body').animate({
      scrollTop: $target.offset().top + 'px'
    }, 'fast')
  })

  foo()
})(window.jQuery)
