from datetime import date
import uuid

import pytest

from mrsrequest.models import MRSRequest
from transport.models import Bill, Transport


@pytest.fixture
def mrsrequest():
    MRSRequest.objects.all().delete()
    return MRSRequest.objects.create(id=uuid.uuid4())


@pytest.fixture
def transport(mrsrequest):
    Transport.objects.all().delete()
    return Transport.objects.create(
        mrsrequest=mrsrequest,
        date_depart=date(2000, 1, 2),
        date_return=date(2000, 1, 2),
        distance=20,
        expense=100.25,
    )


@pytest.fixture
def bill(transport):
    Bill.objects.all().delete()
    return Bill.objects.create(
        transport=transport,
        binary=b'transport_bill',
        filename='transport_bill.jpg',
    )
