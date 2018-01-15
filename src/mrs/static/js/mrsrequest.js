/*global $ */
import Cookie from 'js-cookie'
import mrsattachment from './mrsattachment'

var listen = false

var formInit = function (form) {
  // Make form ajax
  if (listen == false) {
    form.addEventListener('submit', function (e) {
      e.preventDefault()
      formSubmit(form)
      $(form).find(':input').each(function() {
        $(this).attr('disabled', 'disabled')
      })
    }, false)
    listen = true
  }

  // Setup ajax attachment
  mrsattachment(form)

  // Expense bills field
  var $expense = $(form).find('[name=expense]')
  var $bills = $(form).find('#id_bills_container')
  var billsChange = function() {
    ($expense && parseInt($expense.val()) > 0) ? $bills.show() : $bills.hide()
  }
  $expense.on('change', billsChange)
  billsChange()

  // Activate label on date inputs because they have placeholders
  $(form).find('[data-form-control="date"]').siblings('label').addClass('active')

  // Return date
  $(form).find('[name*=depart]').on('input', function() {
    var retName = $(this).attr('name').replace('depart', 'return')
    var $ret = $(form).find('[name="' + retName + '"]')
    $ret.val($(this).val())
  })

  $(form).is(':visible') || $(form).fadeIn()
}

var formSubmit = function(form) {
  var $form = $(form)

  if ($.active) {
    if ($(form).find('.wait').length < 1) {
      $(`<div class="wait card-panel orange lighten-4">
            Merci de laisser le site ouvert pendant téléchargement complêt de vos documents
        </div>`).appendTo($(form))
    }
    return setTimeout($.proxy(formSubmit, this, form), 1000)
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
        // var wizard = document.querySelector('form#mrsrequest-wizard')
        formInit(form)

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

  $(form).fadeIn()
}

export default formInit
