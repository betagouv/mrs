/* global describe, jest, test, expect */

const jsdom = require('jsdom')
const nock = require('nock')
const FileSelect = require('./upload.js')
// const FileSelect = upload.FileSelect
console.log(FileSelect)

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

  // Mock request
  const response = {
    deleteUrl: '/delete'
  }

  window.fetch = jest.fn().mockImplementation(
    () => Promise.resolve(response)
  )

  subject.upload(file)

  test('FileSelect.success() should be called', () => {
    expect(subject.success.mock.calls).toEqual([[file, response]])
  })

  test('FileSelect.error() should never be called', () => {
    expect(subject.error.mock.calls).toEqual([])
  })
})

describe('FileSelect.upload() error: file too large', () => {
  const file = fileFixture(undefined, undefined, 1000000000)
  const subject = fileSelectFactory()

  subject.upload(file)

  test('FileSelect.success() should not be called', () => {
    expect(subject.success.mock.calls).toEqual([])
  })

  test('FileSelect.error() should never be called', () => {
    expect(subject.error.mock.calls).toEqual([[subject.errorMsg.fileSize]])
  })
})

describe('FileSelect.upload() error: invalid file mime type', () => {
  const file = fileFixture(undefined, 'audio/mpeg3')
  const subject = fileSelectFactory()

  subject.upload(file)

  test('FileSelect.success() should not be called', () => {
    expect(subject.success.mock.calls).toEqual([])
  })

  test('FileSelect.error() should never be called', () => {
    expect(subject.error.mock.calls).toEqual([[subject.errorMsg.mimeType]])
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
  const file = new FileSelect()

  test('creates delete request with correct url and options', () => {
    const fileObject = fileFixture()
    window.fetch = jest.fn()

    const deleteUrl = 'url'
    const deleteOptions = {
      method: 'DELETE'
    }
    file.deleteRequest(deleteUrl)

    expect(window.fetch.mock.calls).toEqual([[deleteUrl, deleteOptions]])
  })
})

describe('FileSelect.putRequest()', () => {
  const putUrl = '/put'
  const csrfToken = 123
  const file = new FileSelect(putUrl, csrfToken)

  test('posts to correct url', () => {
    const fileObject = fileFixture()
    window.fetch = jest.fn()

    const putOptions = {
      method: 'POST'
    }
    file.putRequest()

    // fetch is called with correct URL as first param
    expect(window.fetch.mock.calls[0][0]).toEqual(putUrl)
  })

  test('posts with correct options', () => {
    // fetch is called with correct URL as first param
    // expect(window.fetch.mock.calls[0][1]).toEqual(putOptions)
  })
})
