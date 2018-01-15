import mock

from mrsattachment.forms import MRSAttachmentField
from mrsrequest.models import PMT


def test_widget_attrs(mocker):
    field = MRSAttachmentField(
        PMT,
        'mrsrequest:pmt_upload',
        'mrsrequest:pmt_download',
        66,
        ['foo/bar', 'test/lol'],
    )

    # Mock MRSRequestFormMixin.factory() side effect
    field.widget.view = mock.Mock()
    field.widget.view.mrsrequest_uuid = '123'

    attrs = field.widget.attrs
    assert attrs['data-upload-url'] == '/mrsrequest/pmt/MRSREQUEST_UUID/upload'
    assert attrs['data-max-files'] == 66
    assert attrs['data-mime-types'] == 'foo/bar,test/lol'
