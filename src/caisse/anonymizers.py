from hattori.base import BaseAnonymizer, faker
from caisse.models import Caisse


class MRSCaisseAnonymizer(BaseAnonymizer):
    model = Caisse

    attributes = [
        ('liquidation_email', faker.email),
    ]

    def get_query_set(self):
        return Caisse.objects.all()
