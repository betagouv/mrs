/*global $ */

import Cookie from 'js-cookie'
import FileSelect from './upload'
import ScrollReveal from 'scrollreveal'
import Form from './form'

(() => {
  var uploadsInit = function(dom) {
    var uploads = dom.querySelectorAll('[data-upload-url]')
    for (var upload of uploads) {
      var file = upload.parentElement.parentElement.querySelector('input[type=file]')
      file.addEventListener('change', function (e) {
        var upload = e.target.parentElement.parentElement.querySelector('[data-upload-url]')
        var select = new FileSelect(
          upload.getAttribute('data-upload-url'),
          Cookie.get('csrftoken'),
          e.target,
        )
        var name = e.target.getAttribute('name')
        var fileData = new FormData(form).get(name)
        select.upload(fileData)
      })
    }
  }

  var form = document.querySelector('form#mrsrequest-wizard')
  var $form = $(form)
  form.addEventListener('submit', function (e) {
    e.preventDefault()

    $.post(
      {
        url: document.location.href,
        type: 'POST',
        data: $(form).serialize(),
        error: function() {
          $(form).find(':input').each(function() {
            $(this).removeAttr('disabled')
          })
        },
        success: function(data) {
          var dom = $(data)
          var newform = dom.find('form#mrsrequest-wizard')
          $form.html(newform.html())
          var wizard = document.querySelector('form#mrsrequest-wizard')
          uploadsInit(wizard)
          var $wizard = $(wizard)
          Form.initForms($wizard)
        },
        beforeSend: function(xhr) {
          if (!this.crossDomain) {
            xhr.setRequestHeader('X-CSRFToken', Cookie.get('csrftoken'))
          }
        }
      }
    )

    $(form).find(':input').each(function() {
      $(this).attr('disabled', 'disabled')
    })
  }, false)

  $('body').on('click', '[data-callback=scroll-to]', function() {
    var $target = $($(this).attr('data-target'))

    $('html, body').animate({
      scrollTop: $target.offset().top + 'px'
    }, 'fast')
  })

  const sr = ScrollReveal()
  sr.reveal('.scroll-reveal')

  const wizard = document.querySelector('form#mrsrequest-wizard')
  uploadsInit(wizard)
  const $wizard = $(wizard)
  Form.initForms($wizard)
})()
