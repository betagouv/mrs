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
    }, false)
    listen = true
  }

  // Preselect caisse if found in cookie
  var caisseSelected = Cookie.get('caisse')
  if (parseInt(caisseSelected)) {
    $(form).find('select#id_caisse').val(caisseSelected)
  }
  $(form).find('select#id_caisse').on('change', function() {
    Cookie.set('caisse', $(this).val())
  })

  for (let element of form.querySelectorAll('textarea')) {
    M.textareaAutoResize(element)
  }

  M.updateTextFields()

  // Initialize select fields
  $(form).find('select').select()

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
      $mrsrequestForm.hide('slide')
      $caisseForm.show('slide')
    } else if ($caisse.val()) {
      $caisseForm.hide('slide')
      $mrsrequestForm.show('slide')
      var $header = $('.Header--wrapper')
      var headerHeight = $header.length ? $header.outerHeight() : 60
      $('html, body').animate({
        // Compensate for heading to show
        scrollTop: $('#pmt-form').offset().top - headerHeight + 'px'
      }, 'fast')
      if (document.caisses[$caisse.val()].parking_enable) {
        $parking.parents('.col').show('slide')
        $parkingEnable.show('slide')
      } else {
        $parking.parents('.col').hide('slide')
        $parkingEnable.hide('slide')
      }
    } else {
      $mrsrequestForm.hide('slide')
      $caisseForm.hide('slide')
    }
  }
  $caisse.change(caisseChange)
  confirming || caisseChange()

  // Show/hide iterative
  var $iterativeShow = $(form).find('[name=iterative_show]')
  var $iterativeNumberContainer = $(form).find('#id_iterative_number_container')
  var iterativeShowChange = function() {
    if ($iterativeShow.is(':checked')) {
      $iterativeNumberContainer.slideDown()
    } else {
      $iterativeNumberContainer.slideUp()
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
      return
    }
    if (i > 150) {
      i = 150
      $iterativeNumber.val('150')
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
      $newRow.find('label').each(function() {
        var oldLabel = $(this).html()
        var newLabel = oldLabel.replace(/^([^0-9]+)([0-9]*)$/, '$1 ' + (i + 1))
        $(this).html(newLabel)
      })

      var $nextRow = $(form).find(`[name*=-${i + 1}-date_depart]:last`).parents('div.layout-row')
      if ($nextRow.length) {
        $newRow.insertBefore($nextRow)
      } else {
        $newRow.insertAfter(
          $(form).find('[name*=date_depart]:last').parents('div.layout-row')
        )
      }
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
      $billvps.slideDown()
    } else {
      $billvps.slideUp()
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

    $ret.val($(this).val())
  })

  // Simple trips
  $(form).on('change', '[name=trip_kind]', function() {
    if ($('[name=trip_kind]:checked').val() == 'simple') {
      $('[name*=date_return]').val('')
      $('[name*=date_return]').prop('disabled', true)
      $('[name*=date_return]').parent().parent().fadeOut()
    } else {
      $('[name*=date_return]').prop('disabled', false)
      $('[name*=date_return]').parent().parent().fadeIn()
    }
  })
  confirming || $('[name=trip_kind]').trigger('change')

  $(form).on('change', '[name=pmt_pel]', function() {
    if ($('[name=pmt_pel]:checked').val() == 'pel') {
      $('#id_pmt_container').parents('.layout-row.row').fadeOut(() => {
        $('#id_pel_container').parents('.layout-row.row').fadeIn()
      })
    } else {
      $('#id_pel_container').parents('.layout-row.row').fadeOut(() => {
        $('#id_pmt_container').parents('.layout-row.row').fadeIn()
      })
    }
  })
  confirming || $('[name=pmt_pel]:first').trigger('change')

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
      data: $form.serialize(),
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
        var dom = $(data)
        var newform = dom.find('form#mrsrequest-wizard')
        $form.html(newform.html())
        formInit(form)
        submitUi.hideOverlay() // hide overlay

        var $header = $('.Header--wrapper')
        var headerHeight = $header.length ? $header.outerHeight() : 60

        var $error = $('.has-error')
        if ($error.length) {
          $('html, body').animate({
            // Compensate for heading to show
            scrollTop: $error.offset().top - headerHeight + 'px'
          }, 'fast')

          // Change error class to warning.
          if (newform.find('[name=confirm]').length) {
            $('.error').attr('class', 'warning')
          }
        } else {
          $('html, body').animate({
            // Compensate for heading to show
            scrollTop: $form.offset().top - headerHeight + 'px'
          }, 'fast')

          document.querySelector('html').dispatchEvent(
            new CustomEvent(
              'mrsrequest-save',
              {detail: {'mrsrequest_uuid': mrsrequest_uuid}}
            )
          )
        }
      },
      beforeSend: function(xhr) {
        if (!this.crossDomain) {
          xhr.setRequestHeader('X-CSRFToken', Cookie.get('csrftoken'))
        }
      }
    }
  )

  // prevent modification during submission
  $(form).find(':input').each(function() {
    $(this).attr('disabled', 'disabled')
  })
}

if(document.querySelector('form#mrsrequest-wizard'))
  formInit(document.querySelector('form#mrsrequest-wizard'))

$('body').on('click', '[data-load-in-form]', function() {
  submitUi.showSubmitLoading()

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
      submitUi.hideOverlay() // hide overlay
    },
  })
})

export default formInit
