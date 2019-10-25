import { CountUp } from 'countup.js';

const countUpOptions1 = {
  separator: ' ',
  decimal: ',',
};

const countUpOptions2 = {
  decimalPlaces: 1,
  separator: ' ',
  decimal: ',',
  suffix: '<br>jours'
};

$(document).ready(function() {
    var users_shown = false;
    var requests_shown = false;
    var delay_shown = false;

    $.fn.isInViewport = function() {
        var elementTop = $(this).offset().top;
        var elementBottom = elementTop + $(this).outerHeight();
        var viewportTop = $(window).scrollTop();
        var viewportBottom = viewportTop + $(window).height();
        return elementBottom > viewportTop && elementTop < viewportBottom;
    };

    var compute_shown = function () {
        if (
            !users_shown || !requests_shown || !delay_shown
        ) {
            var users_in_viewport = $("#countup-users").isInViewport();
            var requests_in_viewport = $("#countup-requests").isInViewport();
            var delay_in_viewport = $("#countup-delay").isInViewport();

            if (users_in_viewport && !users_shown) {
                let countUpUsers = new CountUp('countup-users', countUpUsersVal, countUpOptions1);
                if (!countUpUsers.error) {
                  countUpUsers.start();
                } else {
                  console.error(countUpUsers.error);
                }
                users_shown = true;
            }
            if (requests_in_viewport && !requests_shown) {
              let countUpRequests = new CountUp('countup-requests', countUpRequestsVal, countUpOptions1);
              if (!countUpRequests.error) {
                countUpRequests.start();
              } else {
                console.error(countUpRequests.error);
              }
              requests_shown = true;
            }
            if (delay_in_viewport && !delay_shown) {
              let countUpDelay = new CountUp('countup-delay', countUpDelayVal, countUpOptions2);
              if (!countUpDelay.error) {
                countUpDelay.start();
              } else {
                console.error(countUpDelay.error);
              }
              delay_shown = true;
            }
        }
        if (
            users_shown && requests_shown && delay_shown
        ) {
            $(window).off();
        }
    };

    $(window).on("resize scroll", function() {
        compute_shown();
        console.log("test");
    });

    compute_shown();
});
