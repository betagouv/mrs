/* global $ */
import '../sass/form.sass'
import Cookie from 'js-cookie'
import './mrsrequest'

window.addEventListener('message', receiveMessage, false)

var allowOriginRoot = window.allowOrigin.split('/').slice(0, 3).join('/')

function receiveMessage(event) {
  if (window.allowInsecure === false && event.origin !== allowOriginRoot) {
    alert('Dropping insecure message from origin: ' + event.origin)
    return
  }

  var $pmt = $('input[name=pmt][type=file]')
  var $uuid = $('input[name=mrsrequest_uuid][type=hidden]')
  var url = $pmt.attr('data-upload-url').replace('MRSREQUEST_UUID', $uuid.val())
  var pmtUrl = JSON.parse(event.data).pmt_url
  var fileName = pmtUrl.split('/')[pmtUrl.split('/').length - 1]  // -1 didn't

  function reqListener () {
    var formData = new FormData()
    var blob = this.response
    formData.append('pmt', blob, fileName)

    var xhr = new XMLHttpRequest()
    xhr.open('POST', url, true)
    xhr.onreadystatechange = function() {
      if (xhr.readyState == 4 && xhr.status != 200) {
        $('#pmt-form').show()
      }
    }
    xhr.setRequestHeader('X-CSRFToken', Cookie.get('csrftoken'))
    xhr.send(formData)
  }

  var oReq = new XMLHttpRequest()
  oReq.addEventListener('load', reqListener)
  oReq.open('GET', pmtUrl)
  oReq.responseType = 'blob'
  oReq.send()
}

document.querySelector('html').addEventListener('mrsrequest-save', function(e) {
  window.parent.postMessage(
    e.detail,
    window.allowInsecure ? '*' : allowOriginRoot
  )
})
