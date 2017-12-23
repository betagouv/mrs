import mock

from django import forms
from mrsattachment.forms import MRSAttachmentField
from mrsrequest.forms import MRSRequestFormMixin


class TestForm(MRSRequestFormMixin, forms.Form):
    test = MRSAttachmentField(
        'transport:bill_upload',
        'transport:bill_download',
        20,
    )


def test_widget_attrs(mocker):
    field = MRSAttachmentField(
        'pmt:pmt_upload',
        'pmt:pmt_download',
        66,
    )

    # Mock MRSRequestFormMixin.factory() side effect
    field.widget.view = mock.Mock()
    field.widget.view.mrsrequest_uuid = '123'

    assert field.widget.attrs['data-upload-url'] == '/pmt/123/upload'
    assert field.widget.attrs['data-max-files'] == 66
