/*global $ */
import Cookie from 'js-cookie'
import mrsattachment from './mrsattachment'
import SubmitUi from './submit-ui'

var listen = false

var submitUi = new SubmitUi(document.querySelector('body'))

var formInit = function (form) {
  var $form = $(form)

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

  // http://materializecss.com/forms.html#select
  $form
    .find('select')
    .not('.disabled')
    .not('.material-ignore')
    .select()

  // Show/hide contact form
  var $cpam = $form.find('[name=cpam]')
  var $contactForm = $form.find('.mrsrequest-contact-form')
  var $mrsrequestForm = $form.find('.mrsrequest-form')
  var cpamUpdate = function() {
    if ($cpam.val() == 'other') {
      $mrsrequestForm.is(':visible') && $mrsrequestForm.slideUp()
      $contactForm.is(':visible') || $contactForm.slideDown()
    } else if ($cpam.val()) {
      $mrsrequestForm.is(':visible') || $mrsrequestForm.slideDown()
      $contactForm.is(':visible') && $contactForm.slideUp()
    } else {
      $mrsrequestForm.is(':visible') && $mrsrequestForm.slideUp()
      $contactForm.is(':visible') && $contactForm.slideUp()
    }
  }
  $cpam.on('change', cpamUpdate)
  cpamUpdate()

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
  $iterativeNumber.on('input', iterativeNumberChange)
  $iterativeNumber.on('change', iterativeNumberChange)
  iterativeNumberChange()

  // Expense bills field
  var $expense = $(form).find('[name=expense]')
  var $bills = $(form).find('#id_bills_container')
  var billsChange = function() {
    ($expense && parseInt($expense.val()) > 0) ? $bills.show() : $bills.hide()
  }
  $expense.on('input', billsChange)
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
        // Show overlay with error state
        var errorMsg = 'Une erreur inconnue est survenue. Veuillez reessayer dans quelques minutes, merci.'
        submitUi.showSubmitError(errorMsg, () => {
          submitUi.hideOverlay() // hide overlay
          $(form).find(':input').each(function() {
            $(this).removeAttr('disabled')
          })
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
          // show error overlay
          var errorMsg = 'Le formulaire contient une ou plusieurs erreurs'
          submitUi.showSubmitError(errorMsg, () => {
            submitUi.hideOverlay() // hide overlay

            $('html, body').animate({
              // Compensate for potential heading to show
              scrollTop: $error.offset().top - 60 + 'px'
            }, 'fast')
          })
        } else {
          var successMsg = 'Soumission du formulaire reussie'
          submitUi.showSubmitSuccess(successMsg) // show success overlay

          // artificially show success overlay for 3s so user has feedback
          window.setTimeout(() => {
            submitUi.hideOverlay() // hide overlay

            $('html, body').animate({
              scrollTop: $(form).offset().top + 'px'
            }, 'fast')
          }, 3000)
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

formInit(document.querySelector('form#mrsrequest-wizard'))

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
      formInit(form)
    },
  })
})

export default formInit
