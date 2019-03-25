import $ from 'jquery'
import Cookie from 'js-cookie'
import M from 'mrsmaterialize'
import SubmitUi from './submit-ui'

var submitUi = new SubmitUi(document.querySelector('body'))

var contactForm = function(form) {
  initForm(form)
  $(form).fadeIn()
}

var initForm = function (form) {
  for (let element of form.querySelectorAll('textarea')) {
    M.textareaAutoResize(element)
  }

  M.updateTextFields()

  form.addEventListener('submit', function (e) {
    e.preventDefault()
    submitForm(e.target)
    $(form).find(':input').each(function() {
      $(this).attr('disabled', 'disabled')
    })
  }, false)

  $('.captcha-refresh').click(function() {
    var $img = $(this).parents('.row').find('img.captcha')
    var $key = $(this).parents('.row').find('[type=hidden]')

    $.getJSON('/captcha/refresh/', function (result) {
      $img.attr('src', result['image_url'])
      $key.val(result['key'])
    })
  })
}

var submitForm = function(form) {
  submitUi.showSubmitLoading()

  $.post(
    {
      url: form.action,
      type: 'POST',
      data: $(form).serialize(),
      error: function() {
        submitUi.showSubmitError(
          'Une erreur inconnue est survenue. Veuillez reessayer dans quelques minutes, merci.',
          () => {
            $(form).find(':input').each(function() {
              $(this).removeAttr('disabled')
            })
            submitUi.hideOverlay()
          }
        )
      },
      success: function(data) {
        var newForm = $(data).find('form')
        $(form).html(newForm.html())
        M.AutoInit(form)
        submitUi.hideOverlay()

        var $error = $('.has-error')
        if ($error.length) {
          $('html, body').animate({
            scrollTop: $error.offset().top + 'px'
          }, 'fast')
        } else {
          $('html, body').animate({
            scrollTop: $(form).offset().top + 'px'
          }, 'fast')
        }
      },
      beforeSend: function(xhr) {
        if (!this.crossDomain) {
          xhr.setRequestHeader('X-CSRFToken', Cookie.get('csrftoken'))
        }
      }
    }
  )
};

(() => {
  var form = document.querySelector('form#contact')

  if(form)
    contactForm(form)
})(window.jQuery)

export default contactForm
