from django.urls import reverse

from pmt.models import PMT


def test_pmt_get_delete_url():
    assert PMT(id=3).get_delete_url() == reverse('pmt_delete', args=[3])
