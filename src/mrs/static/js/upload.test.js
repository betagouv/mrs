/* global describe, jest, test, expect */

const jsdom = require('jsdom')
const nock = require('nock')
const FileSelect = require('./upload.js')

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
const fileSelectFactory = (putUrl, csrfToken, el, withMock=true) => {
  const subject = new FileSelect(putUrl, csrfToken, el, withMock)
  if(!withMock)
    return subject

  subject.success = jest.fn()
  subject.error = jest.fn()

  return subject
}

describe('FileSelect.success()', () => {
  const { JSDOM } = jsdom
  const dom = new JSDOM(`
    <input type="file" />
    <ul>
    </ul>
  `)

  const el = dom.window.document.body
  const file1 = fileFixture()
  const file2 = fileFixture('foo.jpeg')
  const subject = fileSelectFactory(undefined, undefined, el, false)
  const response = {
    deleteUrl: '/delete'
  }

  test('Updates the DOM propoerly', () => {
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

})

describe('FileSelect.deleteSuccess()', () => {
  const { JSDOM } = jsdom
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
  const subject = fileSelectFactory(undefined, undefined, el, false)

  test('updates DOM properly', () => {
    const assertDelete = (deleteUrl, testResult) => {
      const li = el.querySelectorAll('li a[href="' + deleteUrl + '"]')
      // numbers of <li> with link matching deleteUrl
      const nLi = li.length

      expect(nLi).toBe(testResult)
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

describe('FileSelect.deleteRequest()', () => {
  const deleteUrl = '/delete'
  const deleteOptions = {
    method: 'DELETE'
  }

  beforeAll(async () => {
    const file = fileSelectFactory()

    window.fetch = jest.fn()
    const fileObject = fileFixture()


    await file.deleteRequest(deleteUrl)
  })

  test('creates delete request with correct url and options', () => {
    expect(window.fetch.mock.calls).toEqual([[deleteUrl, deleteOptions]])
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
