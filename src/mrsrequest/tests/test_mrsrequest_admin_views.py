import pytest

from crudlfap import crudlfap
from crudlfap_auth.crudlfap import User

from mrsrequest.models import MRSRequest


@pytest.fixture
def mrsrequest(uuid):
    return MRSRequest.objects.create(pk=uuid)


@pytest.mark.django_db
def test_mrsrequestvalidateview_get(srf, mrsrequest):
    request = srf.get('/page')
    view = crudlfap.site['mrsrequest.mrsrequest']['validate'].as_view()

    # Test deny non staff
    response = view(request, pk=mrsrequest.pk)
    assert response.status_code == 302
    assert 'login' in response['Location']

    # Test allow superuser
    request.user = User.objects.create(is_superuser=True)
    response = view(request, pk=mrsrequest.pk)
    assert response.status_code == 200

    # Test deny if has status
    mrsrequest.status = 2
    mrsrequest.save()
    view(request, pk=mrsrequest.pk)
    mrsrequest.refresh_from_db()
    assert mrsrequest.status == 2
