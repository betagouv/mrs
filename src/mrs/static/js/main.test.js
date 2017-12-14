const jsdom = require('jsdom')
const nock = require('nock')


// file = file object
// success = success callback
// error = error callback
class FileSelect {
    constructor() {
        this.errorMsg = 'Erreur'
        this.validMimeTypes = [
            'image/jpeg',
        ]
    }

    async upload(file) {
        // validation (type, size)
        let validated = false

        if(file.type === this.validMimeTypes[0])
            validated = true

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


describe('file upload', () => {
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
