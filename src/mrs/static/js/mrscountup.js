import $ from 'jquery'
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
  var users_shown = false
  var requests_shown = false
  var delay_shown = false

  $.fn.isInViewport = function () {
    var elementTop = $(this).offset().top
    var elementBottom = elementTop + $(this).outerHeight()
    var viewportTop = $(window).scrollTop()
    var viewportBottom = viewportTop + $(window).height()
    return elementBottom > viewportTop && elementTop < viewportBottom
  }

  var compute_shown = function () {
    if (
      !users_shown || !requests_shown || !delay_shown
    ) {
      var users_in_viewport = $('#countup-users').isInViewport()
      var requests_in_viewport = $('#countup-requests').isInViewport()
      var delay_in_viewport = $('#countup-delay').isInViewport()

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
})
