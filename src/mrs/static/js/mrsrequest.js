import $ from 'jquery'
import Cookie from 'js-cookie'
import mrsattachment from './mrsattachment'
import SubmitUi from './submit-ui'
import M from 'mrsmaterialize'

// https://developer.mozilla.org/en-US/docs/Web/API/CustomEvent/CustomEvent#Polyfill
(function () {
  if ( typeof window.CustomEvent === 'function' ) return false
  function CustomEvent ( event, params ) {
    params = params || { bubbles: false, cancelable: false, detail: undefined }
    var evt = document.createEvent( 'CustomEvent' )
    evt.initCustomEvent( event, params.bubbles, params.cancelable, params.detail )
    return evt
  }
  CustomEvent.prototype = window.Event.prototype
  window.CustomEvent = CustomEvent
})()

var listen = false

var submitUi = new SubmitUi(document.querySelector('body'))

function checkedEnables(form, mode) {
  var $enabler = $(form).find(`#id_mode${mode}`)
  var $form = $(form).find(`#${mode}-form`)
  var change = function() {
    $enabler.is(':checked') ? $form.slideDown() : $form.slideUp()
  }
  $enabler.on('change', change)
  change()
}

var formInit = function (form) {
  var confirming = $(form).find('[name=confirm]').length

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

  // Show/hide modes
  if (!confirming) {
    for (var mode of ['vp', 'atp']) {
      checkedEnables(form, mode)
    }
  }


  // Setup ajax attachment
  if (!confirming) {
    mrsattachment(form)
  }

  // Show/hide mrsrequest or vote form
  document.caisses = JSON.parse(document.getElementById('caissesJson').innerHTML)
  var $caisse = $(form).find('#id_caisse')
  var $mrsrequestForm = $(form).find('#mrsrequest-form')
  var $caisseForm = $(form).find('#caisse-form')
  var $parking = $(form).find('#id_parking_expensevp')
  var $parkingEnable = $(form).find('[data-parking-enable]')
  var caisseChange = function() {
    if ($caisse.val() == 'other') {
      $caisseForm.show()
      $mrsrequestForm.hide()
    } else if ($caisse.val()) {
      $caisseForm.hide()
      $mrsrequestForm.show()
      if (document.caisses[$caisse.val()].parking_enable) {
        $parking.parents('.col').show()
        $parkingEnable.show()
      } else {
        $parking.parents('.col').hide()
        $parkingEnable.hide()
      }
    } else {
      $mrsrequestForm.hide()
      $caisseForm.hide()
    }
  }
  $caisse.change(caisseChange)
  confirming || caisseChange()

  // Initialize select fields
  $(form).find('select').select()

  // Show/hide iterative
  var $iterativeShow = $(form).find('[name=iterative_show]')
  var $iterativeNumberContainer = $(form).find('#id_iterative_number_container')
  var iterativeShowChange = function() {
    if ($iterativeShow.is(':checked')) {
      $iterativeNumberContainer.slideDown()
    } else {
      $iterativeNumberContainer.hide()
      $iterativeNumberContainer.find(':input').val('1')
      $(form).find('[name*=-date_depart]:not(:first)').each(function() {
        $(this).parents('div.layout-row.row').remove()
      })
    }
  }
  $iterativeShow.on('change', iterativeShowChange)
  confirming || iterativeShowChange()

  // Generate transport date fields
  var $dateRow = $('#id_transport-0-date_depart_container').parents('div.layout-row.row')
  var $iterativeNumber = $(form).find('[name=iterative_number]')
  var iterativeNumberChange = function() {
    var i = parseInt($iterativeNumber.val())

    if (isNaN(i) || i < 1) {
      $iterativeNumber.val(1)
      i = 1
    }
    i--  // compensate for first form that starts at 0

    // remove all transport lines that have a form number above the i var
    $(form).find('[name*=-date_depart]').each(function() {
      if (parseInt($(this).attr('name').split('-')[1]) > i) {
        $(this).parents('div.layout-row.row').remove()
      }
    })

    // add necessary transport lines
    while(i) {
      var $existing = $(form).find('[name=transport-' + i + '-date_depart]')
      if ($existing.length) {
        i--
        continue
      }

      var $newRow = $dateRow.clone(false)
      $newRow.find(':input').each(function() {
        $(this).attr('name', $(this).attr('name').replace('-0-', `-${i}-`))
        $(this).val('')
      })
      $newRow.find('label').append(' ' + (i + 1))
      $newRow.insertAfter(
        $(form).find('[name*=date_depart]:last').parents('div.layout-row')
      )
      i--
    }
  }
  $iterativeNumber.on('input', iterativeNumberChange)
  $iterativeNumber.on('change', iterativeNumberChange)
  confirming || iterativeNumberChange()

  // Expense billvps field
  var $expensevp = $(form).find('[name=expensevp]')
  var $billvps = $(form).find('#id_billvps_container')
  var expensevpChange = function() {
    function active(field) {
      return field.length && parseFloat(field.val().replace(',', '.')) > 0
    }
    if (active($expensevp) || active($parking)) {
      $billvps.show()
    } else {
      $billvps.hide()
    }
  }
  $expensevp.on('input', expensevpChange)
  $expensevp.on('change', expensevpChange)
  $parking.on('input', expensevpChange)
  $parking.on('change', expensevpChange)
  confirming || expensevpChange()

  // Activate label on date inputs because they have placeholders
  $(form).find('[data-form-control="date"]').siblings('label').addClass('active')

  // Return date
  $(form).on('input', '[name*=depart]', function() {
    if ($('[name=trip_kind]').val() != 'return') return

    var retName = $(this).attr('name').replace('depart', 'return')
    var $ret = $(form).find('[name="' + retName + '"]')

    if (! $ret.val()) {
      $ret.val($(this).val())
    }
  })

  // Simple trips
  $(form).on('change', '[name=trip_kind]', function() {
    if ($('[name=trip_kind]:checked').val() == 'simple') {
      $('[name*=date_return]').val('')
      $('[name*=date_return]').prop('disabled', true)
      $('[name*=date_return]').parent().parent().hide()
    } else {
      $('[name*=date_return]').prop('disabled', false)
      $('[name*=date_return]').parent().parent().show()
    }
  })
  confirming || $('[name=trip_kind]').trigger('change')

  M.AutoInit(form)
  $(form).is(':visible') || $(form).fadeIn()
  if (confirming) {
    var f = $(form).find('#mrsrequest-form')
    f.is(':visible') || f.fadeIn()
  }

  // compensate for https://github.com/Dogfalo/materialize/issues/6049
  for (let select of document.querySelectorAll('select.invalid')) {
    try {
      var input = select.previousSibling.previousSibling.previousSibling
    } catch (error) {
      continue
    }
    if (input.classList) {
      input.classList.add('invalid')
    }
  }
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
  var $expensevp = $(form).find('[name=expensevp]')
  if ($expensevp.val() == '') $expensevp.val('0')
  $form.find('.wait').remove()

  // For postMessage in success callback
  var mrsrequest_uuid = $form.find('input[name="mrsrequest_uuid"]').val()

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
          document.querySelector('html').dispatchEvent(
            new CustomEvent(
              'mrsrequest-save',
              {detail: {'mrsrequest_uuid': mrsrequest_uuid}}
            )
          )

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

if(document.querySelector('form#mrsrequest-wizard'))
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
