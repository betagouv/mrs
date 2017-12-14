const jsdom = require('jsdom')
const nock = require('nock')


class FileSelect {
    constructor(putUrl, csrftoken) {
        this.errorMsg = {
            mimeType: 'Mime type not valid',
            fileSize: 'File too large',
        }
        this.validMimeTypes = [
            'image/jpeg',
        ]
        this.maxFileSize = Math.pow(10, 7) // 10 MB
        this.putUrl = putUrl
        this.csrfToken = csrftoken
    }

    // file mime type (string)
    // private, tested through this.validateFile
    mimeTypeValidate(mimeType) {
        return this.validMimeTypes.indexOf(mimeType) >= 0
    }

    // file size (bytes)
    // private, tested through this.validateFile
    fileSizeValidate(size) {
        return size <= this.maxFileSize
    }

    // file object
    isFileValid(file) {
        if(!this.mimeTypeValidate(file.type)) {
            this.error(this.errorMsg.mimeType)
            return false
        }

        if(!this.fileSizeValidate(file.size)) {
            this.error(this.errorMsg.fileSize)
            return false
        }

        return true
    }

    // file = file object
    async putRequest(file) {
        const data = new FormData()
        data.append('file', file)

        const headers = {
            'X-CSRFToken': this.csrfToken,
            'content-type': '',
        }

        const putOptions = {
            method: 'POST',
            headers,
            body: data,
        }

        return await fetch(this.putUrl, putOptions)
    }

    // delete url for file (string)
    async deleteRequest(deleteUrl) {
        const deleteOptions = {
            method: 'DELETE',
        }

        return await fetch(deleteUrl, deleteOptions)
    }

    // file = file object
    async upload(file) {
        // request
        if(this.isFileValid(file)) {
            try {
                const resp = await this.putRequest()

                this.success(file, resp)
            } catch (e) {
                // request error (only take httpError)
                this.error(e)
            }

        }
    }


    // file = file object
    // response = ajax response
    success(file, response) {
        // Add file <li>
        console.log('success')
    }

    // error => error exception
    error(error) {
        // Add error <li>
        console.log('error')
    }

}



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
        type, // MIME type
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
        deleteUrl: '/delete',
    }

    window.fetch = jest.fn().mockImplementation(
        () => Promise.resolve(response)
    );

    subject.upload(file)

    test('FileSelect.success() should be called', () => {
        expect(subject.success.mock.calls).toEqual([[file, response]])
    })

    test('FileSelect.error() should never be called', () => {
        expect(subject.error.mock.calls).toEqual([])
    })
});

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
});

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
});

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
            method: 'DELETE',
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
            method: 'POST',
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
