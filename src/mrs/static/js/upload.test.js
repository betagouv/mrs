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

describe('FileSelect.fetchUploadRequest', () => {
  const _ = undefined
  const el = fileInputFixture()
  let xhr, subject
  const data = ''
  const url = '/url'
  let resolve, reject

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

    subject.fetchUploadRequest(data, url, resolve, reject)
  })

  test('reject is called if xhr.upload is false', () => {
    xhr.prototype.upload = false
    subject.fetchUploadRequest(data, url, resolve, reject)

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

describe('FileSelect.bindDeleteUrl', () => {
  const subject = fileSelectFactory()
  subject.deleteFile = jest.fn()
  const el = fileInputFixture()
  el.addEventListener = jest.fn()

  test('attaches event listener with correct args', () => {
    const deleteUrl = '/delete'
    subject.bindDeleteUrl(el, '/delete')

    expect(el.addEventListener.mock.calls[0][0]).toBe('click')
    // expect(el.addEventListener.mock.calls[0][1]).toEqual(subject.bindDeleteUrlCallback)
    el.addEventListener.mock.calls[0][1]({preventDefault: () => {}})
    expect(subject.deleteFile.mock.calls[0][0]).toEqual(deleteUrl)
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

  beforeAll(() => {
    el = fileInputFixture()
    subject = fileSelectFactory(_, _, el)
    subject.mountElement = jest.fn()
  })

  test('mount element is not called if element already exists', () => {
    const className = 'class-name'
    el.classList.add(className)
    subject.getElement('input', className)
    expect(subject.mountElement.mock.calls.length).toEqual(0)
  })

  test('mount element is called if element does not exist', () => {
    subject.getElement('span', 'class')
    expect(subject.mountElement.mock.calls.length).toBe(1)
  })

  test('return DOM element', () => {
    const elType = 'span'
    const className = 'class-name'
    const el = subject.getElement(elType, className)

    expect(el.classList[0]).toEqual(className)
  })
})

describe('FileSelect.getProgressElement', () => {
  test('calls getElement with correct param', () => {
    const subject = fileSelectFactory()
    subject.getElement = jest.fn()

    subject.getProgressElement()

    expect(subject.getElement.mock.calls)
      .toEqual([['progress', subject.progressClass]])
  })
})

describe('FileSelect.getErrorElement', () => {
  test('calls getElement with correct param', () => {
    const subject = fileSelectFactory()
    subject.getElement = jest.fn()

    subject.getErrorElement()

    expect(subject.getElement.mock.calls)
      .toEqual([[subject.errorElType, subject.errorClass]])
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

  test('calls bindDeleteUrl with correct params', () => {
    const deleteUrl = '/delete'

    subject.bindDeleteUrl = jest.fn()
    subject.insertLiElement('file-name', deleteUrl)

    expect(subject.bindDeleteUrl.mock.calls.length).toEqual(1)
    expect(subject.bindDeleteUrl.mock.calls[0][1]).toEqual(deleteUrl)
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


describe('FileSelect.showError() and FileSelect.hideError()', () => {
  const el = fileInputFixture()

  test('shows and hides error message to and from  DOM',  () => {
    const _ = undefined
    const subject = fileSelectFactory(_, _, el, _, false)
    const errorElement = subject.getErrorElement()

    subject.hideElement(subject.errorElType, subject.errorClass)
    expect(errorElement.className.includes(subject.hideElementClassName)).toBe(true)

    subject.showElement(subject.errorElType, subject.errorClass)
    expect(errorElement.className.includes(subject.hideElementClassName)).toBe(false)

  })
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

  test('FileSelect.error() calls updateErrorMsg with correct param', () => {
    const subject = getSubject()

    const error = 'error'
    const errorMsg = error

    subject.error(error)
    expect(subject.updateErrorMsg.mock.calls).toEqual([[errorMsg]])
  })

  test('FileSelect.error() calls showMessage()', () => {
    const subject = getSubject()

    subject.error('error')
    expect(subject.showElement.mock.calls).toEqual([[subject.errorElType, subject.errorClass]])
  })
})

describe('FileSelect.updateErrorMsg()', () => {
  const errorClass = 'error'
  const el = fileInputFixture()


  test('adds error message to DOM',  () => {
    const subject = fileSelectFactory(undefined, undefined, el, errorClass, false)

    const errorMsg1 = 'error1'
    const errorMsg2 = 'error2'
    const domErrorMsg = subject.getErrorElement()

    subject.updateErrorMsg(errorMsg1)
    expect(domErrorMsg.innerHTML).toBe(errorMsg1)

    subject.updateErrorMsg(errorMsg2)
    expect(domErrorMsg.innerHTML).toBe(errorMsg2)
  })
})

describe('FileSelect.success()', () => {
  const el = fileInputFixture()
  const file1 = fileFixture()
  const file2 = fileFixture('foo.jpeg')
  const response = {
    deleteUrl: '/delete'
  }

  const getSubject = () => {
    const subject = fileSelectFactory(undefined, undefined, el, undefined, false)
    subject.hideElement = jest.fn()

    return subject
  }

  test('Updates the DOM propoerly', () => {
    const subject = getSubject()

    //// check file name and delete url in DOM for given <li> index
    // file (file object): contains filename
    // index (int): index of <li> to test
    const assertFile = (file, index) => {
      const fileNamesElement = subject.getFilesElement()
      const fileName = fileNamesElement
        .querySelectorAll('li')[index]
        .querySelector('span')
        .innerHTML
      const href = fileNamesElement
        .querySelectorAll('li a[href="' + response.deleteUrl + '"]')[index]
        .getAttribute('href')
      expect(fileName).toBe(file.name)
      expect(href).toBe(response.deleteUrl)
    }

    subject.success(file1, response)
    assertFile(file1, 0)

    subject.success(file2, response)
    assertFile(file2, 1)
  })

  test('calls hideError', () => {
    const subject = getSubject()

    subject.success(file1, '/delete')

    expect(subject.hideElement.mock.calls)
      .toEqual([
        [subject.errorElType, subject.errorClass],
        ['progress', subject.progressClass],
      ])
  })
})

describe('FileSelect.deleteSuccess()', () => {
  const file1 = fileFixture('file1.jpeg')
  const deleteUrl1 = '/delete1'
  const file2 = fileFixture('file2.jpeg')
  const deleteUrl2 = '/delete2'

  const el = fileInputFixture()
  const subject = fileSelectFactory(undefined, undefined, el, undefined, false)
  subject.insertLiElement(
    file1,
    deleteUrl1
  )
  subject.insertLiElement(
    file2,
    deleteUrl2
  )

  test('updates DOM properly', () => {
    //// tests how many <li> have a child with href=deleteUrl
    // deleteUrl (string): file delete url
    // elementCount (int): expected <li> count
    const assertDelete = (deleteUrl, elementCount) => {
      const li = subject.getFilesElement().querySelectorAll('li a[href="' + deleteUrl + '"]')
      const nLi = li.length

      expect(nLi).toBe(elementCount)
    }

    assertDelete(deleteUrl1, 1)
    assertDelete(deleteUrl2, 1)

    subject.deleteSuccess(deleteUrl1)
    assertDelete(deleteUrl1, 0)
    assertDelete(deleteUrl2, 1)

    subject.deleteSuccess(deleteUrl2)
    assertDelete(deleteUrl1, 0)
    assertDelete(deleteUrl2, 0)

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
    expect(subject.success.mock.calls).toEqual([[file, response]])
  })

  test('FileSelect.error() should not be called', () => {
    expect(subject.error.mock.calls).toEqual([])
  })
})

describe('FileSelect.upload() validation error: file too large', () => {
  const file = fileFixture(undefined, undefined, 1000000000)
  const subject = fileSelectFactory()

  subject.upload(file)

  test('FileSelect.success() should not be called', () => {
    expect(subject.success.mock.calls).toEqual([])
  })

  test('FileSelect.error() should be called', () => {
    expect(subject.error.mock.calls).toEqual([[subject.errorMsg.fileSize]])
  })
})

describe('FileSelect.upload() validation error: invalid file mime type', () => {
  const file = fileFixture(undefined, 'audio/mpeg3')
  const subject = fileSelectFactory()

  subject.upload(file)

  test('FileSelect.success() should not be called', () => {
    expect(subject.success.mock.calls).toEqual([])
  })

  test('FileSelect.error() should be called', () => {
    expect(subject.error.mock.calls).toEqual([[subject.errorMsg.mimeType]])
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

  test('FileSelect.error() should be called', () => {

    expect(subject.error.mock.calls).toEqual([[errMsg]])
  })
})

describe('FileSelect.isFileValid()', () => {
  const file = fileSelectFactory()

  test('validates mime type', () => {
    const fileObject = fileFixture()
    expect(file.isFileValid(fileObject)).toBe(true)
  })

  test('does not validate mime type', () => {
    const fileObject = fileFixture(undefined, 'audio/mpeg3')
    expect(file.isFileValid(fileObject)).toBe(false)
  })

  test('validates file size', () => {
    const fileObject = fileFixture()
    expect(file.isFileValid(fileObject)).toBe(true)
  })

  test('does not validate file size', () => {
    const fileObject = fileFixture(undefined, undefined, 1000000000)
    expect(file.isFileValid(fileObject)).toBe(false)
  })
})

describe('FileSelect.deleteFile()', () => {
  const deleteUrl = '/delete'
  const deleteOptions = {
    method: 'DELETE',
    credentials: 'same-origin',
    headers: {
      'X-CSRFToken': undefined,
    }
  }

  test('creates delete request with correct url and options', async () => {
    const subject = fileSelectFactory()

    window.fetch = jest.fn()

    await subject.deleteFile(deleteUrl)

    expect(window.fetch.mock.calls).toEqual([[deleteUrl, deleteOptions]])
  })

  test('calls this.deleteSuccess() with correct arguments', async () => {
    const subject = fileSelectFactory()
    window.fetch = jest.fn().mockImplementation(
      () => Promise.resolve()
    )

    await subject.deleteFile(deleteUrl)
    expect(subject.deleteSuccess.mock.calls).toEqual([[deleteUrl]])
    expect(subject.error.mock.calls).toEqual([])
  })

  test('calls this.error() with correct arguments', async () => {
    const subject = fileSelectFactory()
    const error = 'delete error msg'
    window.fetch = jest.fn().mockImplementation(
      () => Promise.reject(error)
    )

    await subject.deleteFile(deleteUrl)
    expect(subject.deleteSuccess.mock.calls).toEqual([])
    expect(subject.error.mock.calls).toEqual([[error]])
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
