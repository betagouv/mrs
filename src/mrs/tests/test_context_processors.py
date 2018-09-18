from mrs.context_processors import strip_password


def test_strip_password():
    assert strip_password('http://a:b@c:d/e') == 'http://a@c/e'
