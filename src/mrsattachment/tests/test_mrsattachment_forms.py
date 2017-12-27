import mock

from django import forms
from pmt.models import PMT
from mrsattachment.forms import MRSAttachmentField
from mrsrequest.forms import MRSRequestFormMixin


class TestForm(MRSRequestFormMixin, forms.Form):
    test = MRSAttachmentField(
        mock.Mock(),
        'transport:bill_upload',
        'transport:bill_download',
        20,
    )


def test_widget_attrs(mocker):
    field = MRSAttachmentField(
        PMT,
        'pmt:pmt_upload',
        'pmt:pmt_download',
        66,
        ['foo/bar', 'test/lol'],
    )

    # Mock MRSRequestFormMixin.factory() side effect
    field.widget.view = mock.Mock()
    field.widget.view.mrsrequest_uuid = '123'

    assert field.widget.attrs['data-upload-url'] == '/pmt/123/upload'
    assert field.widget.attrs['data-max-files'] == 66
    assert field.widget.attrs['data-mime-types'] == 'foo/bar,test/lol'
