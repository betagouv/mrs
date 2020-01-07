import { CountUp } from 'countup.js'

const countUpOptions1 = {
  separator: '&nbsp',
  decimal: ',',
}

const countUpOptions2 = {
  decimalPlaces: 1,
  separator: ' ',
  decimal: ',',
  suffix: '<br>jours'
}

$(document).ready(function () {
  let users_shown = false
  let requests_shown = false
  let delay_shown = false

  $.fn.isInViewport = function () {
    let elementTop = $(this).offset().top
    let elementBottom = elementTop + $(this).outerHeight()
    let viewportTop = $(window).scrollTop()
    let viewportBottom = viewportTop + $(window).height()
    return elementBottom > viewportTop && elementTop < viewportBottom
  }

  let compute_shown = function () {
    if (
      !users_shown || !requests_shown || !delay_shown
    ) {
      let users_in_viewport = $('#countup-users').isInViewport()
      let requests_in_viewport = $('#countup-requests').isInViewport()
      let delay_in_viewport = $('#countup-delay').isInViewport()

      if (users_in_viewport && !users_shown) {
        let countUpUsers = new CountUp('countup-users', $('#countup-users').html(), countUpOptions1)
        if (!countUpUsers.error) {
          countUpUsers.start()
        }
        users_shown = true
      }
      if (requests_in_viewport && !requests_shown) {
        let countUpRequests = new CountUp('countup-requests', $('#countup-requests').html(), countUpOptions1)
        if (!countUpRequests.error) {
          countUpRequests.start()
        }
        requests_shown = true
      }
      if (delay_in_viewport && !delay_shown) {
        let countUpDelay = new CountUp('countup-delay', $('#countup-delay').html(), countUpOptions2)
        if (!countUpDelay.error) {
          countUpDelay.start()
        }
        delay_shown = true
      }
    }
    if (
      users_shown && requests_shown && delay_shown
    ) {
      $(window).off()
    }
  }

  $(window).on('resize scroll', function () {
    compute_shown()
  })

  compute_shown()

  function getRandomInt(max) {
    return Math.floor(Math.random() * Math.floor(max))
  }
  const temoignages = [
    'J’ai bien reçu le remboursement pour mes frais de transport en voiture particulière, ' +
    'paiement très rapide et simplifié grâce à l’envoi par internet ! Merci ! <br><b>Amelie F.</b>',
    'Service très pratique et simple à utiliser. Le remboursement des frais est très rapide, que demander de plus ?' +
    '<br><b>Aida. D</b>',
    'Mes remboursements simplifiés est un service qui porte bien son nom.' +
    '<br><b>Nicolas R.</b>',
    'Pas de formulaire à envoyer, rapidité du traitement de la demande et rapidité du remboursement. Le top.' +
    '<br><b>Alain A.</b>'
  ]
  let temoignages_index = getRandomInt(temoignages.length)
  $('#temoignage-suivant').click(function() {
    if (temoignages_index < temoignages.length - 1) {
      temoignages_index += 1
    } else {
      temoignages_index = 0
    }
    $('#temoignage').html(
      temoignages[temoignages_index]
    )
  })
  $('#temoignage').html(
    temoignages[temoignages_index]
  )
})
