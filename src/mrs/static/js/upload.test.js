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

describe('FileSelect.insertLiElement', () => {
})

describe('FileSelect.showError() and FileSelect.hideError()', () => {
  const errorClass = 'error'
  const dom = new JSDOM(`
    <input type="file" />
    <div class="${ errorClass }">
    </div>
    <ul>
    </ul>
  `)
  const el = dom.window.document.body


  test('shows and hides error message to and from  DOM',  () => {
    const _ = undefined
    const subject = fileSelectFactory(_, _, el, _, false)
    const errorElement = el.querySelector('.' + errorClass)
    let errorClassNames = errorElement.className

    subject.hideError()
    expect(errorElement.className.includes(subject.hideErrorClassName)).toBe(true)

    subject.showError()
    expect(errorElement.className.includes(subject.hideErrorClassName)).toBe(false)

  })
})

describe('FileSelect.error()', () => {
  const getSubject = () => {
    const _ = undefined
    const subject = fileSelectFactory(_, _, _, _, false)
    subject.updateErrorMsg = jest.fn()
    subject.showError = jest.fn()

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
    expect(subject.showError.mock.calls).toEqual([[]])

  })
})

describe('FileSelect.updateErrorMsg()', () => {
  const errorClass = 'error'
  const dom = new JSDOM(`
    <input type="file" />
    <div class="${ errorClass }">
    </div>
    <ul>
    </ul>
  `)
  const el = dom.window.document.body


  test('adds error message to DOM',  () => {
    const subject = fileSelectFactory(undefined, undefined, el, errorClass, false)

    const errorMsg1 = 'error1'
    const errorMsg2 = 'error2'
    const domErrorMsg = el.querySelector('.' + errorClass)

    subject.updateErrorMsg(errorMsg1)
    expect(domErrorMsg.innerHTML).toBe(errorMsg1)

    subject.updateErrorMsg(errorMsg2)
    expect(domErrorMsg.innerHTML).toBe(errorMsg2)
  })
})

describe('FileSelect.success()', () => {
  const dom = new JSDOM(`
    <input type="file" />
    <ul>
    </ul>
  `)

  const el = dom.window.document.body
  const file1 = fileFixture()
  const file2 = fileFixture('foo.jpeg')
  const response = {
    deleteUrl: '/delete'
  }

  const getSubject = () => {
    const subject = fileSelectFactory(undefined, undefined, el, undefined, false)
    subject.hideError = jest.fn()

    return subject
  }

  test('Updates the DOM propoerly', () => {
    const subject = getSubject()

    //// check file name and delete url in DOM for given <li> index
    // file (file object): contains filename
    // index (int): index of <li> to test
    const assertFile = (file, index) => {
      const fileName = el.querySelectorAll('li')[index].querySelector('span').innerHTML
      const href = el.querySelectorAll('li a[href="' + response.deleteUrl + '"]')[index].getAttribute('href')
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

    expect(subject.hideError.mock.calls).toEqual([[]])
  })
})

describe('FileSelect.deleteSuccess()', () => {
  const file1 = fileFixture('file1.jpeg')
  const deleteUrl1 = '/delete1'
  const file2 = fileFixture('file2.jpeg')
  const deleteUrl2 = '/delete2'

  const createUl = (file, deleteUrl) => {
    return `
      <li>
        <span>${ file.name }</span>
        <a href="${ deleteUrl }">
          delete
        </a>
      </li>
    `
  }

  const dom = new JSDOM(
    '<input type="file" />'
      + '<ul>'
      + createUl(file1, deleteUrl1)
      + createUl(file2, deleteUrl2)
      + '</ul>'
  )

  const el = dom.window.document.body
  const subject = fileSelectFactory(undefined, undefined, el, undefined, false)

  test('updates DOM properly', () => {
    //// tests how many <li> have a child with href=deleteUrl
    // deleteUrl (string): file delete url
    // elementCount (int): expected <li> count
    const assertDelete = (deleteUrl, elementCount) => {
      const li = el.querySelectorAll('li a[href="' + deleteUrl + '"]')
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
  const subject = fileSelectFactory()
  const response = {
    deleteUrl: '/delete'
  }

  beforeAll(async () => {
    window.fetch = jest.fn().mockImplementation(
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
  const errMsg = 0
  const file = fileFixture()
  const subject = fileSelectFactory()

  beforeAll(async () => {
    window.fetch = jest.fn().mockImplementation(
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
    method: 'DELETE'
  }

  test('creates delete request with correct url and options', async () => {
    const subject = fileSelectFactory()

    window.fetch = jest.fn()
    const fileObject = fileFixture()

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
  const file = fileSelectFactory(putUrl, csrfToken)

  beforeAll(async () => {
    window.fetch = jest.fn()
    const fileObject = fileFixture()

    const putOptions = {
      method: 'POST'
    }
    await file.putRequest()
  })

  test('posts to correct url', () => {
    // fetch is called with correct URL as first param
    expect(window.fetch.mock.calls[0][0]).toEqual(putUrl)
  })

  test('posts with correct options', () => {
    // fetch is called with correct URL as first param
    // expect(window.fetch.mock.calls[0][1]).toEqual(putOptions)
  })
})
