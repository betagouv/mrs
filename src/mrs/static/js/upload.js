/* global fetch, FormData */


class FileSelect {
  // putUrl (string): file upload url
  // csrftoken (string): csrf token
  // el (dom element object): file input element to add msgs to
  // errorClass (string): error div classname
  // multiple (bool): true to allow multiple files to be uploaded
  constructor (putUrl, csrftoken, el, errorClass='error', multiple=true, validMimeTypes=false) {
    this.errorMsg = {
      mimeType: 'Type de fichier refusé',
      fileSize: 'Fichier trop lourd',
    }
    this.validMimeTypes = validMimeTypes ? validMimeTypes : [
      'image/jpeg',
      'image/jpg',
      'image/png',
    ]
    this.maxFileSize = Math.pow(10, 7) // 10 MB
    this.putUrl = putUrl
    this.csrfToken = csrftoken
    this.el = el
    this.errorClass = errorClass
    this.fileNameClass = 'file-name'
    this.filesClass = 'files'
    this.filesElType = 'ul'
    this.errorElType = 'span'
    this.deleteClass = 'delete-file'
    this.deleteElType = 'a'
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
  validateFile(file) {
    // todo: raise both errors is better for the user
    if (!this.mimeTypeValidate(file.type)) {
      throw `${this.errorMsg.mimeType}: ${file.type}`
    }

    if (!this.fileSizeValidate(file.size)) {
      throw `${this.errorMsg.fileSize}: ${file.size} / ${this.maxFileSize}`
    }
  }

  fetchUploadRequest(data, url, progressHandler, resolve, reject) {
    const xhr = new XMLHttpRequest()

    const completeHandler = () => {
      const resp = xhr.response
      resolve(resp)
    }


    const errorHandler = e => {
      reject(e)
    }

    if(xhr.upload) {
      xhr.upload.addEventListener('progress', progressHandler, false)
      xhr.addEventListener('load', completeHandler, false)
      xhr.addEventListener('error', errorHandler, false)
      xhr.open('POST', url)
      xhr.setRequestHeader('X-CSRFToken', this.csrfToken)
      xhr.setRequestHeader('credentials', this.csrfToken)
      xhr.send(data)
    } else {
      reject('Could not initialize ajax request')
    }
  }

  fetchUpload(data, url, progressHandler) {
    return new Promise((resolve, reject) =>
      this.fetchUploadRequest(data, url, progressHandler, resolve, reject))
  }

  progressBarHandler(el) {
    return ({ total, loaded }) => {
      el.max = total
      el.value = loaded
    }
  }

  //// make upload file request
  // file (file object): file to upload
  // proressEl (dom el): reference to progress bar dom element to update
  async putRequest(file, progressEl) {
    const data = new FormData()
    data.append('file', file)


    return await this.fetchUpload(data, this.putUrl, this.progressBarHandler(progressEl))
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

  //// Upload file
  // file (file object): file to upload
  async upload(file) {
    let resp
    const li = this.insertLiElement(file.name, '')

    try {
      this.validateFile(file)
      this.showElement('progress', this.progressClass, li)
      const progress = this.getElement('progress', this.progressClass, li)
      progress.max = 100
      progress.value = 0

      resp = await this.putRequest(file, li.querySelector('progress'))
    } catch (e) {
      return this.error(e, li)
    }

    this.success(resp, li)
  }

  createLiElement(fileName, deleteUrl) {
    const document = this.el.ownerDocument
    const li = document.createElement('li')

    li.innerHTML = `
      <span class="${this.fileNameClass}">
        ${fileName}
      </span>

      <progress max="100" value="0" class="${this.progressClass}">
      </progress>

      <span class="${this.errorClass} ${this.hideElementClassName}">
      </span>

      <a data-delete-url="${deleteUrl}" class="${this.deleteClass} ${this.hideElementClassName}">
        remove
      </a>
    `

    return li
  }

  bindDeleteUrlCallback(deleteUrl, el) {
    return async (e) => {
      e.preventDefault()

      // removing li in DOM regardless of request success
      el.parentNode.removeChild(el)

      try {
        await this.deleteRequest(deleteUrl)
      } catch (e) {
        // silencing the delete error as to not bother the user with it
      }
    }
  }

  insertLiElement(fileName, deleteUrl) {
    const ul = this.getFilesElement()
    const li = this.createLiElement(fileName, deleteUrl)

    if(this.multiple) {
      ul.appendChild(li)
    } else {
      if(ul.childNodes.length > 0)
        ul.replaceChild(li, ul.childNodes[0])
      else
        ul.appendChild(li)
    }

    return li
  }

  //// upload file success
  // file = file object
  // response = ajax response
  // el = element to update
  success (response, el) {
    // bind delete url
    const deleteButton = this.getElement(this.deleteElType, this.deleteClass, el)
    const deleteUrl = JSON.parse(response).files[0].deleteUrl
    deleteButton.addEventListener('click', this.bindDeleteUrlCallback(deleteUrl, el))

    // update and show remove element
    this.showElement(this.deleteElType, this.deleteClass, el)

    this.hideElement('progress', this.progressClass, el)
  }

  //// upload file error
  // error (object): error exception
  error(error, el) {
    this.hideElement(this.deleteElType, this.deleteClass, el)
    this.hideElement('progress', this.progressClass, el)
    this.showElement(this.errorElType, this.errorClass, el)

    const errorEl = this.getElement(this.errorElType, this.errorClass, el)
    errorEl.innerHTML = error
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

  getElement(elType, className, mountPoint) {
    if(!mountPoint) {
      const { parentElement } = this.el
      mountPoint = parentElement.parentElement
    }

    if(!mountPoint.querySelector(elType + '.' + className)) {
      this.mountElement(mountPoint, elType, className)
    }

    return mountPoint.querySelector(elType + '.' + className)
  }

  //// Returns DOM element containing files list
  getFilesElement() {
    return this.getElement(this.filesElType, this.filesClass)
  }

  //// shows error message
  showElement(elType, className, root) {
    const el = this.getElement(elType, className, root)
    el.classList.remove(this.hideElementClassName)
  }

  //// hides error message
  hideElement(elType, className, root) {
    const el = this.getElement(elType, className, root)
    el.classList.add(this.hideElementClassName)
  }
}

export default FileSelect
