(($) => {
  $(':input[name=reason]').on('change', function() {
    var choice = $(this).val()
    if (!choice) {
      return
    }

    $(':input[name=mail_body]').html(window.rejectTemplates[choice])
  })

  // ok, i'd rather add 3 lines of JS than battle with django admin's css
  $('.submit-row input[href]').on('click', function(e) {
    e.preventDefault()
    document.location.href = $(this).attr('href')
  })
})(window.jQuery)
