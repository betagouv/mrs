/*global $ */
import Cookie from 'js-cookie'
import mrsattachment from './mrsattachment'
import SubmitUi from './submit-ui'

var listen = false

var submitUi = new SubmitUi(document.querySelector('body'))

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

  // Show/hide iterative
  var $iterativeShow = $(form).find('[name=iterative_show]')
  var $iterativeNumberContainer = $(form).find('#id_iterative_number_container')
  var iterativeShowChange = function() {
    if ($iterativeShow.is(':checked')) {
      $iterativeNumberContainer.slideDown()
    } else {
      $iterativeNumberContainer.hide()
      $iterativeNumberContainer.find(':input').val('1')
      $(form).find('[name*=-date_depart]').each(function() {
        $(this).parents('div.layout-row.row').remove()
      })
    }
  }
  $iterativeShow.on('change', iterativeShowChange)
  iterativeShowChange()

  // Generate transport date fields
  var $dateRow = $('#id_date_depart_container').parents('div.layout-row.row')
  var $iterativeNumber = $(form).find('[name=iterative_number]')
  var iterativeNumberChange = function() {
    var i = parseInt($iterativeNumber.val())

    $(form).find('[name*=-date_depart]').each(function() {
      if (parseInt($(this).attr('name').split('-')[0]) > i) {
        $(this).parents('div.layout-row.row').remove()
      }
    })

    while(i > 1) {
      var $existing = $(form).find('[name=' + i + '-date_depart]')
      if ($existing.length) {
        i--
        continue
      }

      var $target = $(form).find('[name=' + (i + 1) + '-date_depart]')
      if ($target.length)
        $target = $target.parents('div.layout-row.row')
      else
        $target = $(form).find('#id_distance_container').parents('div.layout-row.row')

      var $newRow = $dateRow.clone(false)
      $newRow.find(':input').each(function() {
        $(this).attr('name', i + '-' + $(this).attr('name'))
        $(this).val('')
      })
      $newRow.find('label').append(' ' + i)
      $newRow.insertBefore($target)
      i--
    }
  }
  $iterativeNumber.on('change', iterativeNumberChange)
  iterativeNumberChange()

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
  $(form).on('input', '[name*=depart]', function() {
    var retName = $(this).attr('name').replace('depart', 'return')
    var $ret = $(form).find('[name="' + retName + '"]')
    $ret.val($(this).val())
  })

  $(form).is(':visible') || $(form).fadeIn()
}

var formSubmit = function(form) {
  // show loading overlay
  submitUi.showSubmitLoading()

  var $form = $(form)

  if ($.active) {
    if ($(form).find('.wait').length < 1) {
      submitUi.hideOverlay() // hide overlay and show message

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
        submitUi.showSubmitError('error') // Show overlay with error state

        // artificially show error overlay for 0.5s so user has feedback
        window.setTimeout(() => {
          submitUi.hideOverlay() // hide overlay
          $(form).find(':input').each(function() {
            $(this).removeAttr('disabled')
          })
        }, 500)
      },
      success: function(data) {
        var dom = $(data)
        var newform = dom.find('form#mrsrequest-wizard')
        $form.html(newform.html())
        // var wizard = document.querySelector('form#mrsrequest-wizard')
        formInit(form)

        var $error = $('.has-error')
        if ($error.length) {
          submitUi.showSubmitError('error') // show error overlay

          // artificially show error overlay for 0.5s so user has feedback
          window.setTimeout(() => {
            submitUi.hideOverlay() // hide overlay

            $('html, body').animate({
              scrollTop: $error.offset().top + 'px'
            }, 'fast')
          }, 1000)
        } else {
          submitUi.showSubmitSuccess('success') // show success overlay

          // artificially show success overlay for 0.5s so user has feedback
          window.setTimeout(() => {
            submitUi.hideOverlay() // hide overlay

            $('html, body').animate({
              scrollTop: $(form).offset().top + 'px'
            }, 'fast')
          }, 1000)
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
