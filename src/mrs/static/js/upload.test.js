/* global describe, jest, test, expect */

import jsdom from 'jsdom'
const { JSDOM } = jsdom
import FileSelect from './upload.js'

const fileFixture = (
  fileName = 'file.jpeg',
  type = 'image/jpeg',
  size = 1000
) => {
  const fileDate = new Date()
  return {
    name: fileName,
    lastModified: fileDate.getTime(),
    lastModifiedDate: fileDate,
    size, // bytes
    type // MIME type
  }
}

const fileInputFixture = () => {
  const dom = new JSDOM(`
    <div>
      <div>
        <input type="file" />
      </div>
    </div>
  `)

  return dom.window.document.body.querySelector('input')
}

// withMock (bool): should return factory with mocked success/error methods
const fileSelectFactory = (putUrl, csrfToken, el, errorClass, withMock=true) => {
  const subject = new FileSelect(putUrl, csrfToken, el, errorClass)
  if(!withMock)
    return subject

  subject.success = jest.fn()
  subject.error = jest.fn()
  subject.deleteSuccess = jest.fn()
  subject.updateErrorMsg = jest.fn()
  subject.showError = jest.fn()
  subject.hideError = jest.fn()

  return subject
}

describe('FileSelect.fetchUpload', () => {
  const subject = fileSelectFactory()

  test('promise calls fetchUploadRequest() with right params', () => {
    const data = {}
    const url = ''
    const progressHandler = () => {}
    subject.fetchUploadRequest = jest.fn()

    subject.fetchUpload(data, url, progressHandler)//(resolve, reject)
    expect(subject.fetchUploadRequest.mock.calls[0][0]).toBe(data)
    expect(subject.fetchUploadRequest.mock.calls[0][1]).toBe(url)
    expect(subject.fetchUploadRequest.mock.calls[0][2]).toBe(progressHandler)
  })
})

describe('FileSelect.progressBarHandler', () => {
  const subject = fileSelectFactory()

  test('returns callback binded to el', () => {
    const mockProgress = {
      max: 0,
      value: 0,
    }

    const mockEvent = {
      total: 100,
      loaded: 50,
    }

    subject.progressBarHandler(mockProgress)(mockEvent)
    expect(mockProgress).toEqual({max: mockEvent.total, value: mockEvent.loaded})
  })
})

describe('FileSelect.fetchUploadRequest', () => {
  const _ = undefined
  const el = fileInputFixture()
  let xhr, subject
  const data = ''
  const url = '/url'
  let resolve, reject
  const progressHandler = jest.fn()

  beforeEach(() => {
    xhr = jest.fn()
    xhr.prototype.addEventListener = jest.fn()
    xhr.prototype.open = jest.fn()
    xhr.prototype.send = jest.fn()
    xhr.prototype.setRequestHeader = jest.fn()
    xhr.prototype.upload = {}
    xhr.prototype.upload.addEventListener = jest.fn()
    window.XMLHttpRequest = xhr

    subject = fileSelectFactory(_, _, el)
    subject.csrfToken = 'csrf'

    resolve = jest.fn()
    reject = jest.fn()

    subject.fetchUploadRequest(data, url, progressHandler, resolve, reject)
  })

  test('attaches progress callback', () => {
    const progressEventCall = xhr.mock.instances[0].upload.addEventListener.mock.calls[0]

    expect(progressEventCall[0]).toBe('progress')
    expect(progressEventCall[1]).toBe(progressHandler)
    expect(progressEventCall[2]).toBe(false)
  })

  test('upload finish callback calls resolve()', () => {
    const callback = xhr.mock.instances[0].addEventListener.mock.calls[0][1]
    callback()
    expect(resolve.mock.calls.length).toEqual(1)
  })

  test('upload error callback calls resolve()', () => {
    const callback = xhr.mock.instances[0].addEventListener.mock.calls[1][1]
    callback()
    expect(reject.mock.calls.length).toEqual(1)
  })

  test('reject is called if xhr.upload is false', () => {
    xhr.prototype.upload = false
    subject.fetchUploadRequest(data, url, progressHandler, resolve, reject)

    expect(reject.mock.calls.length).toEqual(1)
  })

  test('xhr is instanciated', () => {
    expect(xhr.mock.instances.length).toEqual(1)
  })

  test('xhr.open is called with proper params', () => {
    expect(xhr.mock.instances[0].open).toBeCalledWith('POST', url)
  })

  test('xhr.send is called with proper params', () => {
    expect(xhr.mock.instances[0].send).toBeCalledWith(data)
  })

  test('xhr headers are parametered', () => {
    expect(xhr.mock.instances[0].setRequestHeader.mock.calls[0])
      .toEqual(['X-CSRFToken', subject.csrfToken])
    expect(xhr.mock.instances[0].setRequestHeader.mock.calls[1])
      .toEqual(['credentials', subject.csrfToken])
  })

  test('addEventListeners are attached', () => {
    expect(xhr.mock.instances[0].addEventListener.mock.calls[0][0]).toBe('load')
    expect(xhr.mock.instances[0].addEventListener.mock.calls[1][0]).toBe('error')
    expect(xhr.mock.instances[0].upload.addEventListener.mock.calls[0][0]).toBe('progress')
  })
})

describe('FileSelect.mountElement', () => {
  const _ = undefined
  const el = fileInputFixture()
  const subject = fileSelectFactory(_, _, el)

  test('adds element to the dom', () => {
    const mountPoint = el.parentNode.parentNode
    const elType = 'elType'
    const className = 'className'

    expect(mountPoint.querySelectorAll(elType + '.' + className).length).toBe(0)
    subject.mountElement(mountPoint, elType, className)
    expect(mountPoint.querySelectorAll(elType + '.' + className).length).toBe(1)
    subject.mountElement(mountPoint, elType, className)
    expect(mountPoint.querySelectorAll(elType + '.' + className).length).toBe(2)
  })
})

describe('FileSelect.getElement', () => {
  const _ = undefined
  let subject, el

  beforeEach(() => {
    el = fileInputFixture()
    subject = fileSelectFactory(_, _, el)
  })

  test('mount element is not called if element already exists', () => {
    subject.mountElement = jest.fn()

    const className = 'class-name'
    el.classList.add(className)
    subject.getElement('input', className)
    expect(subject.mountElement.mock.calls.length).toEqual(0)
  })

  test('mount element is called if element does not exist', () => {
    subject.mountElement = jest.fn()

    subject.getElement('span', 'class')
    expect(subject.mountElement.mock.calls.length).toBe(1)
  })

  test('return DOM element', () => {
    const elType = 'span'
    const className = 'class-namesss'
    const el = subject.getElement(elType, className)

    expect(el.classList[0]).toEqual(className)
  })
})

describe('FileSelect.getFilesElement', () => {
  test('calls getElement with correct param', () => {
    const subject = fileSelectFactory()
    subject.getElement = jest.fn()

    subject.getFilesElement()

    expect(subject.getElement.mock.calls)
      .toEqual([[subject.filesElType, subject.filesClass]])
  })
})

describe('FileSelect.insertLiElement', () => {
  let el, subject

  beforeEach(() => {
    const _ = undefined
    el = fileInputFixture()
    subject = fileSelectFactory(_, _, el)
  })


  test('appends li if this.multiple = true', () => {
    subject.multiple = true
    subject.insertLiElement('file-name', '/deleteUrl')
    expect(subject.el.ownerDocument.querySelectorAll('li').length).toBe(1)
    subject.insertLiElement('file-name', '/deleteUrl')
    expect(subject.el.ownerDocument.querySelectorAll('li').length).toBe(2)
  })

  test('appends li if this.multiple = false', () => {
    subject.multiple = false
    subject.insertLiElement('file-name', '/deleteUrl')
    expect(subject.el.ownerDocument.querySelectorAll('li').length).toBe(1)
    subject.insertLiElement('file-name', '/deleteUrl')
    expect(subject.el.ownerDocument.querySelectorAll('li').length).toBe(1)
  })
})

describe('FileSelect.createLiElement', () => {
})

describe('FileSelect.error()', () => {
  const getSubject = () => {
    const _ = undefined
    const el = fileInputFixture()
    const subject = fileSelectFactory(_, _, el, _, false)
    subject.updateErrorMsg = jest.fn()
    subject.showElement = jest.fn()

    return subject
  }

  test('FileSelect.error() updates error msg', () => {
    const subject = getSubject()

    const error = 'error'

    subject.error(error, subject.el)
    const errorEl = subject.getElement(subject.errorElType, subject.errorClass)
    expect(errorEl.innerHTML).toEqual(error)
  })

  test('FileSelect.error() calls showMessage()', () => {
    const subject = getSubject()

    subject.error('error', subject.el)
    expect(subject.showElement.mock.calls).toEqual([[subject.errorElType, subject.errorClass, subject.el]])
  })
})

describe('FileSelect.success()', () => {
  const el = fileInputFixture()
  const deleteUrl = '/delete'
  const response = JSON.stringify({
    deleteUrl
  })

  const getSubject = () => {
    const subject = fileSelectFactory(undefined, undefined, el, undefined, false)
    subject.hideElement = jest.fn()
    subject.showElement = jest.fn()

    return subject
  }

  test('calls bindDeleteUrl with correct params', () => {
    const subject = getSubject()

    subject.bindDeleteUrlCallback = jest.fn()
    subject.success(response, subject.el)
    expect(subject.bindDeleteUrlCallback.mock.calls[0][0]).toBe(JSON.parse(response).deleteUrl)

  })

  test('hides progress bar', () => {
    const subject = getSubject()

    subject.success(response, subject.el)

    expect(subject.hideElement.mock.calls)
      .toEqual([
        ['progress', subject.progressClass, subject.el],
      ])
  })

  test('show remove button', () => {
    const subject = getSubject()

    subject.success(response, subject.el)

    expect(subject.showElement.mock.calls)
      .toEqual([
        [subject.deleteElType, subject.deleteClass, subject.el],
      ])
  })
})

describe('FileSelect.upload() success', () => {
  const file = fileFixture()
  const _ = undefined
  const el = fileInputFixture()
  const subject = fileSelectFactory(_, _, el)
  const response = {
    deleteUrl: '/delete'
  }

  beforeAll(async () => {
    subject.fetchUpload = jest.fn().mockImplementation(
      () => Promise.resolve(response)
    )

    await subject.upload(file)
  })

  test('FileSelect.success() should be called', () => {
    expect(subject.success.mock.calls.length).toBe(1)
    expect(subject.success.mock.calls[0][0]).toEqual(response)
  })

  test('FileSelect.error() should not be called', () => {
    expect(subject.error.mock.calls).toEqual([])
  })
})

describe('FileSelect.upload() validation error: file too large', () => {
  const file = fileFixture(undefined, undefined, 1000000000)
  const _ = undefined
  const el = fileInputFixture()
  const subject = fileSelectFactory(_, _, el)

  beforeAll(async () => {
    await subject.upload(file)
  })

  test('FileSelect.success() should not be called', () => {
    expect(subject.success.mock.calls).toEqual([])
  })

  test('FileSelect.error() should be called', () => {
    const li = subject.createLiElement(file.name, '')
    expect(subject.error.mock.calls).toEqual([[subject.errorMsg.fileSize, li]])
  })
})

describe('FileSelect.upload() validation error: invalid file mime type', () => {
  const _ = undefined
  const el = fileInputFixture()
  const file = fileFixture(_, 'audio/mpeg3')
  const subject = fileSelectFactory(_, _, el)

  beforeAll(async () => {
    await subject.upload(file)
  })

  test('FileSelect.success() should not be called', () => {
    expect(subject.success.mock.calls).toEqual([])
  })

  test('FileSelect.error() should be called', () => {
    const li = subject.createLiElement(file.name, '')
    expect(subject.error.mock.calls).toEqual([[subject.errorMsg.mimeType, li]])
  })
})

describe('FileSelect.upload() request error', () => {
  const _ = undefined
  const errMsg = 0
  const file = fileFixture()
  const el = fileInputFixture()
  const subject = fileSelectFactory(_, _, el)

  beforeAll(async () => {
    subject.fetchUpload = jest.fn().mockImplementation(
      () => Promise.reject(errMsg)
    )

    await subject.upload(file)
  })

  test('FileSelect.success() should not be called',() => {
    expect(subject.success.mock.calls).toEqual([])
  })

  test('FileSelect.error() should be called with params', () => {
    const li = subject.createLiElement(file.name, '')
    expect(subject.error.mock.calls).toEqual([[errMsg, li]])
  })
})

describe('FileSelect.isFileValid()', () => {
  const subject = fileSelectFactory()

  test('validates mime type', () => {
    const fileObject = fileFixture()
    expect(subject.validateFile(fileObject)).toBe(undefined)
  })

  test('does not validate mime type', () => {
    const fileObject = fileFixture(undefined, 'audio/mpeg3')
    expect(() => subject.validateFile(fileObject)).toThrow(subject.errorMsg.mimeType)
  })

  test('validates file size', () => {
    const fileObject = fileFixture()
    expect(subject.validateFile(fileObject)).toBe(undefined)
  })

  test('does not validate file size', () => {
    const fileObject = fileFixture(undefined, undefined, 1000000000)
    expect(() => subject.validateFile(fileObject)).toThrow(subject.errorMsg.fileSize)
  })
})

describe('FileSelect.bindDeleteUrlCallback()()', () => {
  const deleteUrl = '/delete'
  const deleteOptions = {
    method: 'DELETE',
    credentials: 'same-origin',
    headers: {
      'X-CSRFToken': undefined,
    }
  }

  let el, mockEvent
  beforeEach(() => {
    el = {
      parentNode: {
        removeChild: jest.fn()
      }
    }
    mockEvent = { preventDefault: jest.fn() }
  })

  test('creates delete request with correct url and options', async () => {
    const subject = fileSelectFactory()

    window.fetch = jest.fn()

    await subject.bindDeleteUrlCallback(deleteUrl, el)(mockEvent)

    expect(window.fetch.mock.calls).toEqual([[deleteUrl, deleteOptions]])
  })

  test('calls this.deleteSuccess() with correct arguments', async () => {
    const subject = fileSelectFactory()
    window.fetch = jest.fn().mockImplementation(
      () => Promise.resolve()
    )


    await subject.bindDeleteUrlCallback(deleteUrl, el)(mockEvent)
    expect(el.parentNode.removeChild.mock.calls[0][0]).toBe(el)

    // does not call error()
    expect(subject.error.mock.calls).toEqual([])
  })
})

describe('FileSelect.putRequest()', () => {
  const putUrl = '/put'
  const csrfToken = 123
  const subject = fileSelectFactory(putUrl, csrfToken)

  beforeAll(async () => {
    subject.fetchUpload = jest.fn()
    await subject.putRequest()
  })

  test('posts to correct url', () => {
    // fetch is called with correct URL as first param
    expect(subject.fetchUpload.mock.calls[0][1]).toEqual(putUrl)
  })

  test('posts with correct options', () => {
    // fetch is called with correct URL as first param
    // expect(window.fetch.mock.calls[0][1]).toEqual(putOptions)
  })
})
