import graphene
from graphene_django.types import DjangoObjectType

from .models import MRSRequest


class CreateMRSRequest(graphene.Mutation):
    ok = graphene.Boolean()
    mrsrequest = graphene.Field(lambda: MRSRequestType)

    def mutate(self, info, caisse, distance, expense, institution):
        mrsrequest = MRSRequest(
            distance=distance,
            expense=expense,
            institution=institution,
        )
        ok = True
        return CreateMRSRequest(mrsrequest=mrsrequest, ok=ok)


class MRSRequestType(DjangoObjectType):
    class Meta:
        model = MRSRequest
        only_fields = (
            'caisse',
            'distance',
            'expense',
            'institution',
        )


class Mutation(graphene.ObjectType):
    create_mrs_request = CreateMRSRequest.Field()


class Query(graphene.ObjectType):
    mrsrequest = graphene.Field(MRSRequestType)
