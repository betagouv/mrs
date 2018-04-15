/*global $ */
import Cookie from 'js-cookie'
import FileSelect from './upload'

var formInit = function(form) {
  var $form = $(form)

  $(form).on('click', '[data-delete-url]', function() {
    var $a = $(this)
    $.ajax({
      method: 'DELETE',
      url: $(this).attr('data-delete-url'),
      error: function() {
        // console.log('error')
      },
      success: function() {
        $a.parents('li').slideUp()
      },
      beforeSend: function(xhr) {
        if (!this.crossDomain) {
          xhr.setRequestHeader('X-CSRFToken', Cookie.get('csrftoken'))
        }
      }
    })
  })

  var formData = $form.serializeArray()
  formData.push({
    name: 'csrfmiddlewaretoken',
    value: Cookie.get('csrftoken')
  })

  function createErrorMsg(e) {
    return `<span class="error">${e}</span>`
  }
 
  $('[data-upload-url][type=file]').each(function() {
    const url = $(this).attr('data-upload-url').replace(
      'MRSREQUEST_UUID', $('[name=mrsrequest_uuid]').val()),
      element = $(this)[0],
      fileUpload = new FileSelect(url, Cookie.get('csrftoken'), element, 'error', true, false)

    const upload = () => {
      let files = $(this).prop('files')

      for (var i = 0; i < files.length; i ++) {
        fileUpload.upload(files[i])
      }
    }

    element.addEventListener('change', upload);
  })
}

export default formInit
