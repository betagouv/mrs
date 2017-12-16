/* global fetch, FormData */

class FileSelect {
  // putUrl (string): file upload url
  // csrftoken (string): csrf token
  // el (dom element object): file input element to add msgs to
  // errorClass (string): error div classname
  // multiple (bool): true to allow multiple files to be uploaded
  constructor (putUrl, csrftoken, el, errorClass='error', multiple=true) {
    this.errorMsg = {
      mimeType: 'Mime type not valid',
      fileSize: 'File too large',
    }
    this.validMimeTypes = [
      'image/jpeg',
      'image/jpg',
      'image/png',
    ]
    this.maxFileSize = Math.pow(10, 7) // 10 MB
    this.putUrl = putUrl
    this.csrfToken = csrftoken
    this.el = el
    this.errorClass = errorClass
    this.filesClass = 'files'
    this.hideErrorClassName = 'hidden'
    this.multiple = multiple
  }

  //// validate file MIME type
  //// private, tested through this.validateFile
  // mimeType (string): file mime type
  mimeTypeValidate (mimeType) {
    // todo: print mimetypes to user if not valid
    return this.validMimeTypes.indexOf(mimeType) >= 0
  }

  //// Validate file size
  //// private, tested through this.validateFile
  // size (int): file size (bytes)
  fileSizeValidate (size) {
    // todo: print maxsize to user if not valid
    return size <= this.maxFileSize
  }

  //// Upload file validation
  // file (file object): upload file object
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

  getRequestOptions() {
    const headers = {
      'X-CSRFToken': this.csrfToken,
    }

    return {
      headers,
      credentials: 'same-origin',
    }
  }

  //// make upload file request
  // file (file object): file to upload
  async putRequest(file) {
    const data = new FormData()
    data.append('file', file)

    const putOptions = {
      method: 'POST',
      body: data,
      ...this.getRequestOptions(),
    }

    return await fetch(this.putUrl, putOptions)
  }

  async deleteRequest(deleteUrl) {
    const headers = {
      'X-CSRFToken': this.csrfToken,
    }

    const deleteOptions = {
      method: 'DELETE',
      headers,
      credentials: 'same-origin',
    }

    await fetch(deleteUrl, deleteOptions)
  }

  //// Send delete file request
  // deleteUrl (string): delete url for file
  async deleteFile(deleteUrl) {
    try {
      await this.deleteRequest(deleteUrl)

      this.deleteSuccess(deleteUrl)
    } catch (e) {
      this.error(e)
    }
  }

  //// Upload file
  // file (file object): file to upload
  async upload(file) {
    if (this.isFileValid(file)) {
      let resp
      try {
        const _resp = await this.putRequest(file)
        resp = await _resp.json(_resp)
      } catch (e) {
        this.error(e)

        return
      }

      this.success(file, resp)
    }
  }

  //// delete file success
  // deleteUrl (string): url endpoint to delete file
  deleteSuccess(deleteUrl) {
    const filesElement = this.getFilesElement()
    const elToRemove = filesElement.querySelector('a[href="' + deleteUrl + '"]')

    elToRemove.parentNode.parentNode.removeChild(elToRemove.parentNode)
  }

  createLiElement(fileName, deleteUrl) {
    const document = this.el.ownerDocument
    const li = document.createElement('li')
    li.innerHTML = (
      '<span>'
      + fileName
      + '</span>'
      + '<a href="' + deleteUrl + '" class="delete-file">'
      + 'remove'
      + '</a>'
    )

    return li
  }

  insertLiElement(fileName, deleteUrl) {
    const bindDeleteUrl = el => {
      el.addEventListener('click', e => {
        e.preventDefault()
        this.deleteFile(deleteUrl)
      })
    }

    const ul = this.getFilesElement()
    const li = this.createLiElement(fileName, deleteUrl)

    bindDeleteUrl(li)

    if(this.multiple) {
      ul.appendChild(li)
    } else {
      ul.innerHTML = li
    }
  }

  //// upload file success
  // file = file object
  // response = ajax response
  success (file, response) {
    this.insertLiElement(file.name, response.deleteUrl)

    this.hideError()
  }

  //// upload file error
  // error (object): error exception
  error(error) {
    const errorMsg = error
    this.updateErrorMsg(errorMsg)
    this.showError()
  }

  //// Returns DOM element containing error msg
  getErrorElement() {
    const { parentElement } = this.el
    const mountPoint = parentElement.parentElement

    if(!mountPoint.querySelector('.' + this.errorClass)) {
      const document = this.el.ownerDocument
      const errorEl = document.createElement('span')
      errorEl.classList.add(this.errorClass)
      mountPoint.appendChild(errorEl)
    }

    return mountPoint.querySelector('.' + this.errorClass)
  }

  //// Returns DOM element containing files list
  getFilesElement() {
    const { parentElement } = this.el
    const mountPoint = parentElement.parentElement

    if(!mountPoint.querySelector('.' + this.filesClass)) {
      const document = this.el.ownerDocument
      const filesEl = document.createElement('ul')
      filesEl.classList.add(this.filesClass)
      mountPoint.appendChild(filesEl)
    }

    return mountPoint.querySelector('.' + this.filesClass)
  }

  //// updates error field
  // errorMsg (strin): error message
  updateErrorMsg(errorMsg) {
    const errorElement = this.getErrorElement()
    errorElement.innerHTML = errorMsg
  }

  //// shows error message
  showError() {
    const errorElement = this.getErrorElement()
    errorElement.classList.remove(this.hideErrorClassName)
  }

  //// hides error message
  hideError() {
    const errorElement = this.getErrorElement()
    errorElement.classList.add(this.hideErrorClassName)
  }
}

export default FileSelect
