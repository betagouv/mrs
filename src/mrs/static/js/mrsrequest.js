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

$(document).ajaxError(function(event, jqXHR, ajaxSettings, thrownError) {
    // We don't want user Bad requests (oversized files, unaccepted file format...)
    // to be reported to Sentry
    if (jqXHR.status != 400){
      Raven.captureMessage(jqXHR.statusText, {
        extra: {
          type: ajaxSettings.type,
          url: ajaxSettings.url,
          data: ajaxSettings.data,
          status: jqXHR.status,
          error: jqXHR.statusText,
          response: (jqXHR.responseText == null) ? "" : jqXHR.responseText.substring(0, 100)
        }
      })
    }
  }
)

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

  // On récupère les caisses et leurs attributs au format json
  document.caisses = JSON.parse(
  document.getElementById('caissesJson').innerHTML)

  // On récupère l'id de la région des régimes spéciaux
  document.regimesspeciauxId = JSON.parse(
  document.getElementById('regimesspeciauxId').innerHTML).id

  // Bloc contenant la liste déroulante de sélection de caisse
  var $caisseSelector = $(form).find('#caisse-selector')
  // Liste déroulante de sélection de caisse
  var $caisse = $(form).find('#id_caisse')

  // Bloc contenant la liste déroulante de sélection d'une caisse inactive
  var $othercaisseContainer = $(form).find('#id_other-caisse_container')
  // Liste déroulante de sélection d'une caisse inactive
  var $othercaisse = $(form).find('#id_other-caisse')

  // Liste déroulante de sélection de région
  var $region = $(form).find('#id_region')

  // Bloc contenant la liste déroulante de sélection d'une région inactive
  var $otherregionContainer = $(form).find('#id_other-region_container')
  // Liste déroulante de sélection d'une région inactive
  var $otherregion = $(form).find('#id_other-region')

  // Formulaire de saisie de la demande MRS
  var $mrsrequestForm = $(form).find('#mrsrequest-form')

  // Formulaire "Me prévenir quand la caisse sera activée"
  var $caisseForm = $(form).find('#caisse-form')

  var $parking = $(form).find('#id_expensevp_parking')
  var $parkingEnable = $(form).find('[data-parking-enable]')

  // Preselect region if found in cookie
  var regionSelected = Cookie.get('region')

  if (parseInt(regionSelected)) {

    $region.val(regionSelected)
    $caisse.val('')
    adjustSelectOptions('caisse', $region.val(),  false, true)
    $caisseSelector.show('slide')
    Cookie.set('otherregion', '')

  } else if (regionSelected=='other'){

    $region.val('other')
    hideRequestShowCaisseVoteForm(form, true)
    Cookie.set('caisse', '')

  }

  // Preselect caisse if found in cookie
  var caisseSelected = Cookie.get('caisse')

  if (parseInt(caisseSelected)) {

    $caisse.val(caisseSelected)
    adjustSelectOptions('caisse', $region.val(),  false, true)

  } else if (caisseSelected=='other'){

    $caisse.val(caisseSelected)
    adjustSelectOptions('caisse', $region.val(),  false, true)
    hideRequestShowCaisseVoteForm(form, false)
    Cookie.set('otherregion', '')

  } else {

    $caisseForm.hide()

  }

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

// NB : Masquer directement les options du select ne fonctionne pas sous IE11 et Safari,
// une solution de contournement consiste à wrapper l'option dans un span afin
// qu'elle n'apparaisse plus. Pas très élégant, mais fonctionnel.
function hideOptions(selector){
  $(form).find(selector).each(function() {
    if( !($(this).parent().is('span')) ) $(this).wrap('<span>')
  })
}

function showOptions(selector){
  $(form).find(selector).each(function() {
    if( ($(this).parent().is('span')) ) $(this).unwrap()
  })
}

// Fonction permettant d'ajuster (afficher et/ou masquer) les options dans
// le select natif, selon la région sélectionnée
function adjustSelectOptions(select_name, region_id, with_regimes_speciaux, with_others){

  // On masque toutes les options qui n'ont pas la région sélectionnées au sein
  // de l'attribut data-regions
  hideOptions('[name=' + select_name +'] option:not([data-regions~=' + region_id + '])')

  // On affiche toutes les options qui ont la région sélectionnée au sein
  // de l'attribut data-regions
  showOptions('[name=' + select_name +'] option[data-regions~=' + region_id + ']')

  // Si les régimes spéciaux sont à rajouter, on affiche les options qui ont
  // la région régimes spéciaux au sein de l'attribut data-regions
  if(with_regimes_speciaux){
    showOptions('[name=' + select_name +'] option[data-regions~=' + document.regimesspeciauxId + ']')
  }

  // Si l'option autres est à afficher, on l'affiche
  if(with_others){
    showOptions('[name=' + select_name +'] option[value=other]')
  }

  // On affiche un item vide par défaut
  showOptions('[name=' + select_name +'] option[value=""]')

}

// Fonction permettant d'afficher le formulaire "Me prévenir quand la caisse
// sera disponible" et de masquer le formulaire classique de demande, avec la
// possibilité ou non d'afficher le sélecteur de caisse
function hideRequestShowCaisseVoteForm(form, caisse_selector_hidden){

    caisse_selector_hidden ? $(form).find('#caisse-selector').hide('slide') : $(form).find('#caisse-selector').show('slide')

    $(form).find('#mrsrequest-form').hide('slide')
    $(form).find('#caisse-form').show('slide')
}

// Fonction permettant de masquer le formulaire "Me prévenir quand la caisse
// sera disponible" et d'afficher ou masquer le formulaire classique de demande,
// avec la possibilité ou non d'afficher le sélecteur de caisse
function showRequestHideCaisseVoteForm(
  form, caisse_selector_hidden, request_form_hidden){

    caisse_selector_hidden ? $(form).find('#caisse-selector').hide('slide') : $(form).find('#caisse-selector').show('slide')

    request_form_hidden ? $(form).find('#mrsrequest-form').hide('slide') : $(form).find('#mrsrequest-form').show('slide')
    
    $(form).find('#caisse-form').hide('slide')

}

  // Fonction appelée lorsqu'un changement est détecté sur le select des régions
  var regionChange = function() {

    // Si l'utilisateur sélectionne "Autres" dans la liste des régions
    if ($region.val() == 'other') {

      // On masque le formulaire demande et le sélecteur classique de caisse
      // pour afficher le formulaire "Me prévenir quand ma caisse sera
      // disponible"
      $otherregionContainer.show()
      hideRequestShowCaisseVoteForm(form, true)
      $caisse.val('other')

    // Si l'utilisateur sélectionne une région dans la liste des régions (c'est
    // à dire une région avec au moins une caisse active)
    } else if ($region.val()) {

      $caisse.val('')
      adjustSelectOptions('caisse', $region.val(),  false, true)

      showRequestHideCaisseVoteForm(form, false, true)

      Cookie.set('region', $region.val())

    // Si aucune région n'est sélectionnée, on masque tout sauf le select
    } else {

      showRequestHideCaisseVoteForm(form, true, true)

    }
  }

  var otherregionChange = function() {

    if($otherregion.val()!=document.regimesspeciauxId){

      $othercaisse.val('')
      adjustSelectOptions('other-caisse', $otherregion.val(),  true, false)

    } else {

      $othercaisse.val('')
      adjustSelectOptions('other-caisse', $otherregion.val(),  false, false)

    }

  }

  var caisseChange = function() {

    if ($caisse.val() == 'other') {

      hideRequestShowCaisseVoteForm(form, false)
      $otherregionContainer.hide()
      $othercaisse.val('')
      adjustSelectOptions('other-caisse', $region.val(), true, false)

    } else if ($caisse.val()) {

      showRequestHideCaisseVoteForm(form, false)

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

      Cookie.set('caisse', $caisse.val())

    } else {

      hideRequestShowCaisseVoteForm(form, true)

    }
  }

  $caisse.change(caisseChange)
  $region.change(regionChange)
  $otherregion.change(otherregionChange)
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
  var $billvps = $(form).find('#id_billvps_container')
  var $toll = $(form).find('[name=expensevp_toll]')
  var expensevpChange = function() {
    function active(field) {
      return field.length && parseFloat(field.val().replace(',', '.')) > 0
    }
    if (active($toll) || active($parking)) {
      $billvps.slideDown()
    } else {
      $billvps.slideUp()
    }
  }
  $toll.on('input', expensevpChange)
  $toll.on('change', expensevpChange)
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

  var distancevp_help = function() {
    // use 2 by default for the sake of the example
    var count = parseInt($('#id_iterative_number').val()) || 2
    var single = ! $('[name=trip_kind][value=return]').is(':checked')

    if (count == 1) {
      if (single) {
        $('#id_distancevp_container label').html(
          'Indiquez le nombre de km parcourus lors de votre aller simple'
        )
        $('#id_distancevp_container .help-block').slideUp()
      } else {
        $('#id_distancevp_container label').html(
          'Indiquez le nombre de km parcourus lors de votre aller + retour'
        )
        $('#id_distancevp_container .help-block').slideDown()
      }
    } else {
      var exemple = count * 10
      if (single) {
        $('#id_distancevp_container label').html(
          `Indiquez le nombre de km parcourus lors de vos ${count} allers simples.<br />`
        )
        $('#id_distancevp_container .help-block').html(
          `Par exemple pour 10 km par aller simple, déclarez ${exemple} km parcourus`
          + '<div id="distancevp_preview"></div>'
        )
        $('#id_distancevp_container .help-block').slideDown()
      } else {
        $('#id_distancevp_container label').html(
          `Indiquez le nombre de km parcourus lors de vos ${count} allers retours.<br />`
        )
        $('#id_distancevp_container .help-block').html(
          `Par exemple pour 10 km par aller + retour, déclarez ${exemple} km parcourus`
          + '<div id="distancevp_preview"></div>'
        )
        $('#id_distancevp_container .help-block').slideDown()
      }
    }
  }
  $(form).on('input', '#id_iterative_number', distancevp_help)
  $(form).on('change', '#id_iterative_show', distancevp_help)
  $(form).on('change', '#id_trip_kind', distancevp_help)
  distancevp_help()

  var distancevp_preview = function() {
    if (!$('#distancevp_preview').length) return
    if (!parseInt($('#id_distancevp').val())) return

    var count = parseFloat($('#id_iterative_number').val()) || 2
    var distancevp = parseFloat($('#id_distancevp').val().replace(',', '.'))
    var average = distancevp / count
    if (distancevp % count) {
      average = average.toFixed(1)
    }

    var single = ! $('[name=trip_kind][value=return]').is(':checked')
    $('#distancevp_preview').html(
      `Votre déclaration correspond à une moyenne de <b>${average}km</b>`
      + ' par trajet ' + (single ? '(aller simple)' : '(aller retour)')
    )

    $('#distancevp_preview').fadeIn()
  }
  $(form).on('input', '#id_distancevp', distancevp_preview)
  $(form).on('input', '#id_iterative_number', distancevp_preview)
  $(form).on('change', '#id_trip_kind', distancevp_preview)
  distancevp_preview()

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
  for (var name of ['expensevp_toll', 'expensevp_parking']) {
    var $field = $(form).find('[name=' + name + ']')
    if ($field.val() == '') $field.val('0')
  }
  $form.find('.wait').remove()

  // For postMessage in success callback
  var mrsrequest_uuid = $form.find('input[name="mrsrequest_uuid"]').val()

  $.post(
    {
      url: document.location.href,
      type: 'POST',
      data: $form.serialize(),
      error: function(err) {
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
