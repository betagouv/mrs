$(document).ready(function () {
  $('#recherche-input').on('keyup change', function () {
    $('.collapse').collapse('hide')
    let recherche = $(this).val().toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '')

    if (recherche === '') {
      $('.card').show()
      $('#aucun-resultat').hide()
    } else {
      let shown = false
      $('.card-header').map(function () {
        if ($(this).html().toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').indexOf(recherche) > 1) {
          $(this).parent().show()
          shown = true
        } else {
          $(this).parent().hide()
        }
      })
      if (!shown) {
        $('.card-body').map(function () {
          if ($(this).html().toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').indexOf(recherche) > 1) {
            $(this).parent().parent().show()
            shown = true
          } else {
            $(this).parent().parent().hide()
          }
        })
      }

      if (!shown) {
        $('#aucun-resultat').show()
      } else {
        $('#aucun-resultat').hide()
      }
    }
  })
})