from django.urls import reverse


def upload_request(rf, id, file, name=None, urlname=None):
    file.name = name or '1.png'
    request = rf.post(
        reverse(urlname or 'mrsrequest:pmt_upload', args=[id]),
        dict(file=file)
    )
    return request
