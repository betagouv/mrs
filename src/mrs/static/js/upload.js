/* global fetch, FormData */

class FileSelect {
  // putUrl (string): file upload url
  // csrftoken (string): csrf token
  // el (dom element object): file input element to add msgs to
  constructor (putUrl, csrftoken, el) {
    this.errorMsg = {
      mimeType: 'Mime type not valid',
      fileSize: 'File too large'
    }
    this.validMimeTypes = [
      'image/jpeg'
    ]
    this.maxFileSize = Math.pow(10, 7) // 10 MB
    this.putUrl = putUrl
    this.csrfToken = csrftoken
    this.el = el
  }

  // file mime type (string)
  // private, tested through this.validateFile
  mimeTypeValidate (mimeType) {
    return this.validMimeTypes.indexOf(mimeType) >= 0
  }

  // file size (bytes)
  // private, tested through this.validateFile
  fileSizeValidate (size) {
    return size <= this.maxFileSize
  }

  // file object
  isFileValid (file) {
    if (!this.mimeTypeValidate(file.type)) {
      this.error(this.errorMsg.mimeType)
      return false
    }

    if (!this.fileSizeValidate(file.size)) {
      this.error(this.errorMsg.fileSize)
      return false
    }

    return true
  }

  // file = file object
  async putRequest (file) {
    const data = new FormData()
    data.append('file', file)

    const headers = {
      'X-CSRFToken': this.csrfToken,
      'content-type': ''
    }

    const putOptions = {
      method: 'POST',
      headers,
      body: data
    }

    return await fetch(this.putUrl, putOptions)
  }

  // delete url for file (string)
  async deleteRequest (deleteUrl) {
    const deleteOptions = {
      method: 'DELETE'
    }

    try {
      await fetch(deleteUrl, deleteOptions)

      this.deleteSuccess(deleteUrl)
    } catch (e) {
      this.error(e)
    }
  }

  // file = file object
  async upload (file) {
    // request
    if (this.isFileValid(file)) {
      try {
        const resp = await this.putRequest()

        this.success(file, resp)
      } catch (e) {
        this.error(e)
      }
    }
  }

  deleteSuccess(deleteUrl) {
    const { el } = this
    const elToRemove = el.querySelector('li a[href="' + deleteUrl + '"]')

    elToRemove.parentNode.parentNode.removeChild(elToRemove.parentNode)
  }

  // file = file object
  // response = ajax response
  success (file, response) {
    const ul = this.el.childNodes[2]
    ul.innerHTML += (
      '<li>'
      + '<span>'
      + file.name
      + '</span>'
      + '<a href="' + response.deleteUrl + '">'
      + 'remove'
      + '</a>'
      + '</li>'
    )

    // formatting ul.innerHTML as 1 liner
    var i = ul.innerHTML.indexOf('<');
    ul.innerHTML = ul.innerHTML.substr(i, ul.innerHTML.length - 1)
  }

  // error => error exception
  error (error) {
    // Add error to <li> (display only httpErrors)
    console.log(error)
  }
}

module.exports = FileSelect
