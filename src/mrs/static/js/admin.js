(($) => {
  $(':input[name=template]').on('change', function() {
    var choice = $(this).val()
    if (!choice) {
      return
    }

    $(':input[name=subject]').val(window.rejectTemplates[choice].subject)
    $(':input[name=body]').val(window.rejectTemplates[choice].body)
  })

  // ok, i'd rather add 3 lines of JS than battle with django admin's css
  $('.submit-row input[href]').on('click', function(e) {
    e.preventDefault()
    document.location.href = $(this).attr('href')
  })
})(window.jQuery)
