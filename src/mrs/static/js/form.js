/*global $ jQuery */
import Cookie from 'js-cookie'
import '../sass/form.sass'

var init = function(container) {
  uploadsInit(container)
  initForms($(container))
  $('form#mrsrequest-wizard').fadeIn()
}

var initForms = function ($container) {
  // Bills
  var $expense = $('[name=transportform-expense]')
  var $bills = $('#id_transportform-bills_container')
  var billsChange = function() {
    ($expense && parseInt($expense.val()) > 0) ? $bills.show() : $bills.hide()
  }
  $expense.on('change', billsChange)
  billsChange()

  // Formsets
  // https://bitbucket.org/ionata/django-formset-js
  $('.formset-field').formset({
    animateForms: true,
    newFormCallback: initForms
  })

  // Select
  // http://materializecss.com/forms.html#select
  $container
    .find('select')
    .not('.disabled')
    .not('.material-ignore')
    .select()

  var lang = jQuery( ':root' ).attr('lang')
  if(lang) {
    jQuery.datetimepicker.setLocale(lang.substr(0, 2))
  }

  // Date/DateTime/Time
  // https://github.com/xdan/datetimepicker
  $container
    .find('[data-form-control="date"]')
    .each(function () {
      $(this).datetimepicker({
        format: this.dataset.dateFormat,
        timepicker: false,
        mask: false,
        scrollInput: false
      })
    })
  $container
    .find('[data-form-control="time"]')
    .each(function () {
      $(this).datetimepicker({
        format: this.dataset.dateFormat,
        datepicker: false,
        timepicker: true,
        mask: false,
        scrollInput: false
      })
    })
  $container.find('[data-form-control="datetime"]').each(
    function () {
      $(this).datetimepicker({
        format: this.dataset.dateFormat,
        datepicker: true,
        timepicker: true,
        mask: false,
        scrollInput: false
      })
    })
}

/* to be implemented and used ...
var destroyForms = function ($container) {
  // Select
  $container
    .find('select')
    .not('.disabled')
    .not('.material-ignore')
    .select('destroy')

  // Date/DateTime/Time
  $container
    .find('[data-form-control="date"],[data-form-control="time"],[data-form-control="datetime"]')
    .datetimepicker('destroy')
}
*/

var uploadsInit = function() {
  var form = document.querySelector('form#mrsrequest-wizard')
  var $form = $(form)

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
  var form = document.querySelector('form#mrsrequest-wizard')
  var $form = $(form)

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
        init(wizard)

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

(($) => {
  var form = document.querySelector('form#mrsrequest-wizard')

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

  const wizard = document.querySelector('form#mrsrequest-wizard')
  init(wizard)

  /* Code for FileSelect, pending multi device support
  var uploadsInit = function(dom) {
    vaR uploads = dom.querySelectorAll('[data-upload-url]')
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

export default init
