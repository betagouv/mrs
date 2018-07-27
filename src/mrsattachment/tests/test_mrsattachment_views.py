import io
import json

import mock
import pytest

from django import http

from mrsattachment.models import MRSAttachment
from mrsattachment.tests.utils import upload_request
from mrsattachment.views import (
    MRSFileDeleteView,
    MRSFileDownloadView,
    MRSFileUploadView,
)
from mrsrequest.models import MRSRequest


def test_mrsfiledeleteview_allowed_objects_usage(rf):
    '''Test promise to use model.objects.allowed_objects() for security.'''

    request = rf.delete('/delete/123')

    view = MRSFileDeleteView(
        request=request,
        model=mock.Mock(),
        kwargs=dict(pk=13)
    )
    response = view.dispatch(request, pk=13)

    # Check if the manager allowed_objects was called properly, it's the heart
    # of security in the file delete view, it's a bit obscure so don't rely on
    # it and add integration tests for each of your url made with
    # MRSFileDeleteView and your model, ie. like pmt module.
    view.model.objects.allowed_objects.assert_called_once_with(request)
    assert view.object is (
        view.model.objects.allowed_objects.return_value.get.return_value
    ), 'delete() should have made self.object = self.get_object()'

    # Check that the object was deleted
    view.object.delete.assert_called_once()

    # Check that we have a nice response code
    assert response.status_code == 200


@pytest.mark.django_db
def test_mrsfileuploadview_security(srf, id):
    '''Save upload if request had MRSRequest.allow(request).'''
    record = type(
        'TestModel',
        (object,),
        dict(
            get_delete_url=lambda s: '/del',
            get_download_url=lambda s: '/down',
            get_upload_url=lambda s: '/up',
            filename='test_mrsfileuploadview_security.jpg',
        ),
    )

    model = mock.Mock()
    model.objects.record_upload.return_value = record()

    view = MRSFileUploadView.as_view(model=model)

    # Test missing FILE
    request = srf.post('/')
    MRSRequest(id=id).allow(request)
    response = view(request, mrsrequest_uuid=id)
    assert response.status_code == 400
    assert response.content == b'Pas de fichier re\xc3\xa7u'

    with io.BytesIO(b'test_mrsfileuploadview_security') as f:
        f.name = 'test_mrsfileuploadview_security.jpg'

        request = upload_request(srf, id, f)

        # Test missing uuid
        response = view(request)
        assert response.status_code == 400
        assert response.content == b'Nous avons perdu le UUID'

        # Test deny
        response = view(request, mrsrequest_uuid=id)
        assert response.status_code == 400
        assert model.objects.record_upload.call_count == 0, (
            'record_upload should not have been called')

        # Allow
        MRSRequest(id=id).allow(request)

        # Test allow
        response = view(request, mrsrequest_uuid=id)
        assert response.status_code == 200

        # Test record_upload call: mrsrequest argument
        arg0 = model.objects.record_upload.call_args_list[0][0][0]
        assert arg0 == id, 'should have kept uuid from upload_request'

        # Test record_upload call: file argument
        arg0 = model.objects.record_upload.call_args_list[0][0][0]
        upload = model.objects.record_upload.call_args_list[0][0][1]
        assert upload == request.FILES['file'], (
            'should have used the passed file'
        )

        # record_upload() should have been called once, as described above
        model.objects.record_upload.assert_called_once()

        # Test response
        data = json.loads(response.content)
        assert len(data['files']) == 1
        f = data['files'][0]
        assert f['deleteUrl'] == '/del', 'should be get_delete_url()'
        assert f['thumbnailUrl'] == '/down', 'should be get_download_url()'
        assert f['url'] == '/down', 'should be get_download_url()'


@pytest.mark.django_db
def test_mrsfiledownloadview_security(srf, attachment):
    view = MRSFileDownloadView.as_view(model=MRSAttachment)
    request = srf.get('/')

    with pytest.raises(http.Http404):
        view(request, pk=attachment.id)

    request.user.profile = 'stat'
    with pytest.raises(http.Http404):
        view(request, pk=attachment.id)

    def _():
        response = view(request, pk=attachment.id)
        assert response.status_code == 200
        assert b''.join(response.streaming_content) == b'aoeu'
        assert response['Content-Length'] == '4'
        assert isinstance(response, http.FileResponse)

    request.user.profile = 'admin'
    _()

    request.user.profile = None
    MRSRequest(attachment.mrsrequest_uuid).allow(request)
    _()
