import ScrollReveal from 'scrollreveal'
import '../sass/landing.sass'
import '../sass/form.sass'
import mrsrequest from './mrsrequest'
import './contact'

(($) => {
  const sr = ScrollReveal()
  sr.reveal('.scroll-reveal')

  mrsrequest(document.querySelector('form#mrsrequest-wizard'))

  $('body').on('click', '[data-load-in-form]', function() {
    $.ajax({
      method: 'GET',
      url: $(this).attr('data-load-in-form'),
      error: function() {
        // console.log('error')
      },
      success: function(data) {
        var dom = $(data)
        var newform = dom.find('form#mrsrequest-wizard')
        var form = document.querySelector('form#mrsrequest-wizard')
        $(form).html(newform.html())
        mrsrequest(form)
      },
    })
  })

  $('body').on('click', '[data-callback=scroll-to]', function() {
    var $target = $($(this).attr('data-target'))

    $('html, body').animate({
      scrollTop: $target.offset().top + 'px'
    }, 'fast')
  })
})(window.jQuery)
