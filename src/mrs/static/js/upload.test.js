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

const fileSelectFactory = () => {
  const subject = new FileSelect()
  subject.success = jest.fn()
  subject.error = jest.fn()

  return subject
}

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
  const file = new FileSelect()

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
    const file = new FileSelect()

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
  const file = new FileSelect(putUrl, csrfToken)

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
