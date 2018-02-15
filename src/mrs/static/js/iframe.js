import '../sass/form.sass'
import Cookie from 'js-cookie'
import mrsrequest from './mrsrequest'

window.addEventListener('message', receiveMessage, false)

function receiveMessage(event) {
  // exemple on mdn suggests to implement this basic kind of security
  // https://developer.mozilla.org/en-US/docs/Web/API/Window/postMessage
  // if (event.origin !== 'http://example.org:8080')
  //  return;

  var $pmt = $('input[name=pmt][type=file]')
  var $uuid = $('input[name=mrsrequest_uuid][type=hidden]')
  var url = $pmt.attr('data-upload-url').replace('MRSREQUEST_UUID', $uuid.val())
  var pmtUrl = JSON.parse(event.data).pmt_url
  var fileName = pmtUrl.split('/')[pmtUrl.split('/').length - 1]  // -1 didn't

  function reqListener () {
    var formData = new FormData()
    var blob = new Blob(
      [this.response],
      {
        type: this.getResponseHeader('Content-Type')
      }
    )
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
  oReq.send()
}

(() => {
  mrsrequest(document.querySelector('form#mrsrequest-wizard'))
})()
