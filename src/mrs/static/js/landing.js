import ScrollReveal from 'scrollreveal'
import '../sass/landing.sass'
import mrsrequestForm from './mrsrequest'
import './contact'

(($) => {
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
        mrsrequestForm(form)
      },
    })
  })

  const sr = ScrollReveal()
  sr.reveal('.scroll-reveal')

})(window.jQuery)
