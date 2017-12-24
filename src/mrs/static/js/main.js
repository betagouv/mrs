/*global $ */

import Cookie from 'js-cookie'
import FileSelect from './upload'
import ScrollReveal from 'scrollreveal'
import Form from './form'
import '../sass/main.sass'


(($) => {
  /* Code for FileSelect, pending multi device support
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
          'error',
          parseInt(upload.getAttribute('data-max-files')) > 1,
          upload.getAttribute('data-mime-types').split(',')
        )
        var name = e.target.getAttribute('name')
        var fileData = new FormData(form).get(name)
        select.upload(fileData)
      })
    }
  }
  */

  var form = document.querySelector('form#mrsrequest-wizard')
  var $form = $(form)

  var uploadsInit = function(dom) {
    var formData = $form.serializeArray();
    formData.push({
      name: "csrfmiddlewaretoken",
      value: Cookie.get('csrftoken')
    });

    $('[data-upload-url][type=file]').each(function() {
      var $file = $(this)
      var $target = $file.parents('.input-field').find('ul.files')
      $file.fileupload({
        url: $(this).attr('data-upload-url'),
        formData: formData,
        maxFileSize: Math.pow(10, 7),
        acceptFileTypes: /(\.|\/)(gif|jpe?g|png|pdf)$/i,
        done: function (e, data) {
          $.each(JSON.parse(data.result)['files'], function (index, file) {
            var template = `
              <span class="file-name">${file.name}</span>
              <a data-delete-url="${file.deleteUrl}" class="delete-file">
                Éffacer
              </a>
            `
            var $li = $('<li />').append(template).appendTo($target);
            $li.on('click', '[data-delete-url]', function() {
              $.ajax({
                method: 'DELETE',
                url: $(this).attr('data-delete-url'),
                error: function() {
                  console.log('error')
                },
                success: function(data) {
                  $li.slideUp()
                },
                beforeSend: function(xhr) {
                  if (!this.crossDomain) {
                    xhr.setRequestHeader('X-CSRFToken', Cookie.get('csrftoken'))
                  }
                }
              })
            });
          });
        }
      })
    })
  }

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
})(window.jQuery)
