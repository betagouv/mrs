import pytest

from django.contrib.sessions.backends.base import SessionBase
from django.test.client import RequestFactory


id = pytest.fixture(lambda: '2b88b740-3920-44e9-b086-c851f58e7ea7')


class SessionRequestFactory(RequestFactory):
    def generic(self, *args, **kwargs):
        request = super().generic(*args, **kwargs)
        request.session = SessionBase()
        return request


@pytest.fixture
def srf():
    return SessionRequestFactory()
