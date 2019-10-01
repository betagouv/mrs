import pytest

from mrsuser.models import User


@pytest.mark.django_db
def test_multi_profile_eq():
    user = User.objects.create(username='test_multi_profile_eq')
    user.groups.create(name='foo')
    user.groups.create(name='bar')
    assert user.profile == 'foo'
    assert user.profile == 'bar'

    user.is_superuser = True
    assert user.profile == 'admin'
