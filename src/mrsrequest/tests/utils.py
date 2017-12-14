from django.urls import reverse


def upload_request(rf, id, file):
    request = rf.post(
        reverse('pmt_upload', args=[id]),
        dict(file=file)
    )
    # Middleware is not called, deal with session manually
    request.session = dict()
    return request
