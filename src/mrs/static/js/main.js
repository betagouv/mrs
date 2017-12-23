import Cookie from 'js-cookie'
import ScrollReveal from 'scrollreveal'
import Form from './form'
import '../sass/main.sass'

(($) => {
  var form = document.querySelector('form#mrsrequest-wizard')
  var $form = $(form)

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
        $form.html(newform.html())
        var wizard = document.querySelector('form#mrsrequest-wizard')
        uploadsInit(wizard)
        var $wizard = $(wizard)
        Form.initForms($wizard)
        $form.fadeIn()
      },
    })
  })

  $('body').on('click', '[data-delete-url]', function() {
    var $a = $(this)
    $.ajax({
      method: 'DELETE',
      url: $(this).attr('data-delete-url'),
      error: function() {
        // console.log('error')
      },
      success: function() {
        $a.parents('li').slideUp()
      },
      beforeSend: function(xhr) {
        if (!this.crossDomain) {
          xhr.setRequestHeader('X-CSRFToken', Cookie.get('csrftoken'))
        }
      }
    })
  })

  var uploadsInit = function() {
    var formData = $form.serializeArray()
    formData.push({
      name: 'csrfmiddlewaretoken',
      value: Cookie.get('csrftoken')
    })

    $('[data-upload-url][type=file]').each(function() {
      var $file = $(this)
      var $target = $file.parents('.input-field').find('ul.files')
      $file.fileupload({
        url: $(this).attr('data-upload-url'),
        formData: formData,
        maxFileSize: Math.pow(10, 7),
        acceptFileTypes: /(\.|\/)(gif|jpe?g|png|pdf)$/i,
        add: function (e, data) {
          data.context = []
          for (var i in data.files) {
            var file = data.files[i]
            var template = `
              <li data-file-name="${file.name}">
                <span class="file-name">${file.name}</span>
                <progress max="${file.size}" value="0" class="progress-bar">
                </progress>
              </li>
            `
            data.context.push($(template).appendTo($target))
          }
          data.submit()
        },
        progressall: function () {
          // console.log('progressall', e, data)
        },
        progress: function (e, data) {
          for (var i in data.files) {
            var $li = data.context[i]
            $li.find('progress').val(data.loaded)
          }
        },
        done: function (e, data) {
          var result = JSON.parse(data.result)['files']
          for (var i in result) {
            var file = result[i]
            var $li = data.context[0]
            $(`
              <a data-delete-url="${file.deleteUrl}" class="delete-file">
                Éffacer
              </a>
            `).appendTo($li)
            $li.find('progress').fadeOut()
          }
        },
        fail: function (e, data) {
          for (var i in data.files) {
            var $li = data.context[i]
            var response = data.response()
            $(`<span class="error">${response.errorThrown}</span>`).appendTo($li)
            $li.find('progress').fadeOut()
          }
        }
      })
    })
  }

  var submitForm = function() {
    if ($.active) {
      if ($(form).find('.wait').length < 1) {
        $(`<div class="wait card-panel orange lighten-4">
              Merci de laisser le site ouvert pendant téléchargement complêt de vos documents
          </div>`).appendTo($(form))
      }
      return setTimeout(submitForm, 1000)
    }
    $(form).find('.wait').remove()

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
          $form.fadeIn()

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
  }

  form.addEventListener('submit', function (e) {
    e.preventDefault()

    submitForm()

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

  $form.fadeIn()

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

})(window.jQuery)
