import graphene
from graphene_django.types import DjangoObjectType

from .models import Caisse


class CaisseType(DjangoObjectType):
    class Meta:
        model = Caisse
        only_fields = (
            'id',
            'name',
            'active',
        )


class Query(object):
    all_caisses = graphene.List(CaisseType)

    def resolve_all_caisses(self, info, **kwargs):
        return Caisse.objects.all()
