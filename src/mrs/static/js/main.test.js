const jsdom = require('jsdom')
const nock = require('nock')


class FileSelect {
    constructor() {
        this.errorMsg = {
            mimeType: 'Mime type not valid',
        }
        this.validMimeTypes = [
            'image/jpeg',
        ]
        this.maxFileSize = Math.pow(10, 7) // 10 MB
    }

    // file mime type (string)
    mimeTypeValidate(mimeType) {
        return this.validMimeTypes.indexOf(mimeType) >= 0
    }

    // file size (bytes)
    fileSizeValidate(size) {
        return size <= this.maxFileSize
    }

    // file = file object
    async upload(file) {
        // validation (type, size)
        let validated = true

        if(!this.mimeTypeValidate(file.type)) {
            return this.error(this.errorMsg.mimeType)
        }

        // request
        if(validated) {
            try {
                const resp  = await fetch('url.fausseurl')

                this.success(file, resp)
            } catch (e) {
                // request error (only take httpError)
                this.error(e)
            }

        } else {
            // file error
            this.error()
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



const fileFixture = (fileName = 'file.jpeg', type = 'image/jpeg') => {
    const fileDate = new Date()
    return {
        name: fileName,
        lastModified: fileDate.getTime(),
        lastModifiedDate: fileDate,
        size: 100000, // bytes
        type, // MIME type
    }
}


describe('file upload success', () => {
    const file = fileFixture()

    const subject = new FileSelect()
    subject.success = jest.fn()
    subject.error = jest.fn()

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


    // check expect(li.innerHTML).toBe(filename etc)
});

describe('test mimeTypeValidate', () => {
    const file = new FileSelect()

    test('validate mime type', () => {
        expect(file.mimeTypeValidate('image/jpeg')).toBe(true)
    })

    test('does not validate mime type', () => {
        expect(file.mimeTypeValidate('audio/mpeg3')).toBe(false)
    })
})

describe('test file size', () => {
    const file = new FileSelect()

    test('file size valid', () => {
        expect(file.fileSizeValidate(100)).toBe(true)
    })

    test('file size not valid', () => {
        expect(file.fileSizeValidate(10000000000000)).toBe(false)
    })
})
