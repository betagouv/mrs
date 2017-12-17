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
    this.filesElType = 'ul'
    this.errorElType = 'span'
    this.progressClass = 'progress-bar'
    this.hideElementClassName = 'hidden'
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
        this.showElement('progress', this.progressClass)

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

  bindDeleteUrlCallback(deleteUrl) {
    return e => {
      e.preventDefault()
      this.deleteFile(deleteUrl)
    }
  }

  bindDeleteUrl(el, deleteUrl) {
    el.addEventListener('click', this.bindDeleteUrlCallback(deleteUrl))
  }

  insertLiElement(fileName, deleteUrl) {
    const ul = this.getFilesElement()
    const li = this.createLiElement(fileName, deleteUrl)

    this.bindDeleteUrl(li, deleteUrl)

    if(this.multiple) {
      ul.appendChild(li)
    } else {
      //ul.innerHTML = li
      if(ul.childNodes.length > 0)
        ul.replaceChild(li, ul.childNodes[0])
      else
        ul.appendChild(li)
    }
  }

  //// upload file success
  // file = file object
  // response = ajax response
  success (file, response) {
    this.insertLiElement(file.name, response.deleteUrl)

    this.hideElement(this.errorElType, this.errorClass)
    this.hideElement('progress', this.progressClass)
  }

  //// upload file error
  // error (object): error exception
  error(error) {
    const errorMsg = error
    this.updateErrorMsg(errorMsg)
    this.showElement(this.errorElType, this.errorClass)
  }

  //// Mounts element in dom at mount point
  // mountPoint (DOM element): which DOM element to insert created element into
  // elType (string): type of element to insert in mount point
  // className (string): class name of inserted element
  mountElement(mountPoint, elType, className) {
    const document = this.el.ownerDocument
    const el = document.createElement(elType)
    el.classList.add(className)
    mountPoint.appendChild(el)
  }

  getElement(elType, className) {
    const { parentElement } = this.el
    const mountPoint = parentElement.parentElement

    if(!mountPoint.querySelector('.' + className)) {
      this.mountElement(mountPoint, elType, className)
    }

    return mountPoint.querySelector('.' + className)
  }

  //// Returns DOM element containing error msg
  getErrorElement() {
    return this.getElement(this.errorElType, this.errorClass)
  }

  //// Returns DOM element containing files list
  getFilesElement() {
    return this.getElement(this.filesElType, this.filesClass)
  }

  //// updates error field
  // errorMsg (strin): error message
  updateErrorMsg(errorMsg) {
    const errorElement = this.getErrorElement()
    errorElement.innerHTML = errorMsg
  }

  //// shows error message
  showElement(elType, className) {
    const el = this.getElement(elType, className)
    el.classList.remove(this.hideElementClassName)
  }

  //// hides error message
  hideElement(elType, className) {
    const el = this.getElement(elType, className)
    el.classList.add(this.hideElementClassName)
  }
}

export default FileSelect
