import pytest

from mrsrequest.models import MRSRequest
from mrsrequest.views import (
    MRSRequestValidateView,
)


@pytest.fixture
def mrsrequest(uuid):
    return MRSRequest.objects.create(pk=uuid)


@pytest.mark.django_db
def test_mrsrequestvalidateview_get(srf, mrsrequest):
    request = srf.get('/page')
    view = MRSRequestValidateView.as_view()

    # Test deny non staff
    response = view(request)
    assert response.status_code == 302
    assert response['Location'] == '/admin/login/?next=/page'

    # Test allow staff
    request.user.is_staff = True
    response = view(request, pk=mrsrequest.pk)
    assert response.status_code == 200

    # Test deny if has status
    mrsrequest.status = 2
    mrsrequest.save()
    with pytest.raises(Exception):
        view(request, pk=mrsrequest.pk)
