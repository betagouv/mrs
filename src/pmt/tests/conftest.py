import pytest

from mrsrequest.models import MRSRequest
from pmt.models import PMT
import uuid


@pytest.fixture
def mrsrequest():
    MRSRequest.objects.all().delete()
    return MRSRequest.objects.create(id=uuid.uuid4())


@pytest.fixture
def pmt(mrsrequest):
    PMT.objects.all().delete()
    return PMT.objects.create(
        mrsrequest=mrsrequest,
        binary=b'lol',
        filename='lol.jpg',
    )
