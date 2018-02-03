import os

from mrs.context_processors import settings, strip_password


def test_strip_password():
    assert strip_password('http://a:b@c:d/e') == 'http://a@c/e'


def test_settings():
    os.environ['INSTANCE'] = 'testinstance'
    assert settings(None) == dict(settings=dict(
        RAVEN_DNS='', INSTANCE='testinstance'))
