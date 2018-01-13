import mock

from django import forms
from mrsattachment.forms import MRSAttachmentField
from mrsrequest.models import PMT
from mrsrequest.forms import MRSRequestFormMixin


class TestForm(MRSRequestFormMixin, forms.Form):
    test = MRSAttachmentField(
        mock.Mock(),
        'mrsrequest:bill_upload',
        'mrsrequest:bill_download',
        20,
    )


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
    assert attrs['data-upload-url'] == '/mrsrequest/pmt/123/upload'
    assert attrs['data-max-files'] == 66
    assert attrs['data-mime-types'] == 'foo/bar,test/lol'
