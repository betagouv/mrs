import mock

from django import forms
from mrsattachment.forms import MRSAttachmentWidget
from mrsrequest.forms import MRSRequestFormMixin


class TestForm(MRSRequestFormMixin, forms.Form):
    test = forms.FileField(widget=MRSAttachmentWidget('pmt:pmt_upload', 66))


def test_widget_attrs(mocker):
    widget = MRSAttachmentWidget('pmt:pmt_upload', 'pmt:pmt_download', 66)

    # Mock MRSRequestFormMixin.factory() side effect
    widget.view = mock.Mock()
    widget.view.mrsrequest_uuid = '123'

    assert widget.attrs['data-upload-url'] == '/pmt/123/upload'
    assert widget.attrs['data-max-files'] == 66
