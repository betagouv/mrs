import Cookie from 'js-cookie'
import FileSelect from './upload'
import ScrollReveal from 'scrollreveal'
import $ from 'jquery'

(() => {
  // datepicker needs jquery names `jQuery` in window global namespace
  window.jQuery = $
  // Materialize needs jquery names `$` in window global namespace
  window.$ = $

  var form = document.querySelector('form.mrsrequest');
  form.addEventListener('submit', function (e) {
    e.preventDefault()
    formData = new FormData(e.target)
    console.log(Array.from(formData.keys()))
  }, false);

  var uploads = document.querySelectorAll('[data-upload-url]');
  for (var upload of uploads) {
    var file = upload.parentElement.parentElement.querySelector('input[type=file]')
    file.addEventListener('change', function (e) {
      var upload = e.target.parentElement.parentElement.querySelector('[data-upload-url]')
      var select = new FileSelect(
        upload.getAttribute('data-upload-url'),
        Cookie.get('csrftoken'),
        e.target,
      )
      var name = e.target.getAttribute('name')
      var fileData = new FormData(form).get(name)
      select.upload(fileData)
    })
  }

  const sr = ScrollReveal()
  sr.reveal('.scroll-reveal')
})()
