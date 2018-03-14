/*global $ */
import Cookie from 'js-cookie'

var contactForm = function(form) {
  initForm(form)
  $(form).fadeIn()
}

var initForm = function (form) {
  form.addEventListener('submit', function (e) {
    e.preventDefault()
    submitForm(e.target)
    $(form).find(':input').each(function() {
      $(this).attr('disabled', 'disabled')
    })
  }, false)
}

var submitForm = function(form) {
  $.post(
    {
      url: form.action,
      type: 'POST',
      data: $(form).serialize(),
      error: function() {
        $(form).find(':input').each(function() {
          $(this).removeAttr('disabled')
        })
      },
      success: function(data) {
        $(form).html($(data).find('form').html())

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

