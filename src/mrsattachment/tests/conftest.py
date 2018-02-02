import pytest
from mrsattachment.models import MRSAttachment


@pytest.fixture
def attachment(uuid, upload):
    return MRSAttachment.objects.record_upload(uuid, upload)
