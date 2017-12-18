import mock

from django import forms
from mrsattachment.forms import MRSAttachmentWidget, MRSAttachementFormMixin


class TestForm(MRSAttachementFormMixin, forms.Form):
    test = forms.FileField(widget=MRSAttachmentWidget('pmt_upload', 66))


def test_widget_attrs(mocker):
    widget = MRSAttachmentWidget('pmt_upload', 'pmt_download', 66)

    # Mock MRSAttachementFormMixin.factory() side effect
    widget.view = mock.Mock()
    widget.view.request.mrsrequest_uuid = '123'

    assert widget.attrs['data-upload-url'] == '/pmt/123/upload'
    assert widget.attrs['data-max-files'] == 66


def test_form_factory(srf, mocker):
    view = mock.Mock()

    view.request = srf.get('/')
    form = TestForm.factory(view)
    assert 'test' in form.fields, 'should be preset on GET'
    assert form.fields['test'].widget.view == view, (
        'should set the widget view attribute for attrs')

    view.request = srf.post('/')
    assert 'test' not in TestForm.factory(view).fields, (
        'should be gone on POST')
