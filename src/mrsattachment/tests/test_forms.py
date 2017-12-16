import mock

from django import forms


def test_widget_attrs(settings):
    with mock.patch('django.urls.reverse') as reverse:
        from mrsattachment.forms import MRSAttachmentWidget
    reverse.return_value = '/123/foo'

    widget = MRSAttachmentWidget('urlname', 66)

    # Mock MRSAttachementFormMixin.factory() side effect
    widget.view = mock.Mock()
    widget.view.request.mrsrequest_uuid = '123'

    assert widget.attrs['data-upload-url'] == '/123/foo'
    reverse.assert_called_once_with('urlname', args=['123']),

    assert widget.attrs['data-max-files'] == 66


def test_form_factory(srf):
    with mock.patch('django.urls.reverse'):
        from mrsattachment.forms import (
            MRSAttachementFormMixin, MRSAttachmentWidget)

    class TestForm(MRSAttachementFormMixin, forms.Form):
        test = forms.FileField(widget=MRSAttachmentWidget('urlname', 66))

    view = mock.Mock()

    view.request = srf.get('/')
    form = TestForm.factory(view)
    assert 'test' in form.fields, 'should be preset on GET'
    assert form.fields['test'].widget.view == view, (
        'should set the widget view attribute for attrs')

    view.request = srf.post('/')
    assert 'test' not in TestForm.factory(view).fields, (
        'should be gone on POST')
