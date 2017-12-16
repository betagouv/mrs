import collections
import mock
import uuid

from mrsrequest.models import MRSRequest
from mrsrequest.views import MRSRequestCreateView
from mrsattachment.tests.test_mrsattachment_forms import TestForm


def test_mrsrequestcreateview_forms_factory(srf):
    class Form(TestForm):
        factory = mock.Mock()

    class View(MRSRequestCreateView):
        form_classes = [Form]
        request = srf.get('/')  # oopscheat

    forms = View().forms_factory()
    assert len(forms) == 1
    assert forms == collections.OrderedDict(Form=Form.factory.return_value)


def test_mrsrequestcreateview_get_mrsrequest_uuid(srf):
    view = MRSRequestCreateView()

    request = srf.get('/')
    result = view.get_mrsrequest_uuid(request)
    # Should return a string, not UUID instance
    assert isinstance(result, str)
    # String should not be empty
    assert result

    mrsrequest = MRSRequest(id=uuid.uuid4())

    # Test deny unauthorized uuid passed in POST request
    request = srf.post('/', dict(mrsrequest_uuid=str(mrsrequest.id)))
    result = view.get_mrsrequest_uuid(request)
    assert result is False

    # Allow
    mrsrequest.allow(request)

    # Test allow
    assert view.get_mrsrequest_uuid(request) == str(mrsrequest.id)


def test_mrsrequestcreateview_dispatch(srf):
    class View(MRSRequestCreateView):
        get_mrsrequest_uuid = mock.Mock()
        forms_factory = mock.Mock()

    request = srf.get('/')
    view = View(request=request)
    view.dispatch(request)
    assert request.mrsrequest_uuid == view.get_mrsrequest_uuid.return_value
    assert view.forms == view.forms_factory.return_value

    # Should respond with 400 Bad Request if get_mrsrequest_uuid returns False
    view.get_mrsrequest_uuid.return_value = False
    response = view.dispatch(request)
    assert response.status_code == 400
