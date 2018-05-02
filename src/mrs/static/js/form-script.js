import $ from 'jquery'

$(document).ready(function () {
  $('select').change(function () {
    var str = $(this).parent().find('input').val()
    var result = str
    if (str && str.indexOf(',') != -1) {
      var strarr = str.split(',')
      result = strarr[strarr.length - 1]
    }
    $(this).parent().find('input').val(result)
  })
})