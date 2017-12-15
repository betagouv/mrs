from mrs.middleware import ThreadLocalMiddleware

from threadlocals.threadlocals import get_current_request


def test_threadlocalmiddleware():
    response = 'test_threadlocalmiddleware'
    middleware = ThreadLocalMiddleware(lambda r: response)
    assert middleware('foo') == response
    assert get_current_request() == 'foo'
