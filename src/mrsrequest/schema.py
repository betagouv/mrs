import graphene

from graphene import Schema, relay, resolve_only_args
from graphene_django.types import DjangoObjectType

from .models import MRSRequest, Transport


class MRSRequestNode(DjangoObjectType):
    class Meta:
        model = MRSRequest
        interfaces = (relay.Node,)


class MRSRequestInput(graphene.InputObjectType):
    institution = graphene.String()


class CreateMRSRequest(relay.ClientIDMutation):
    class Input:
        mrsrequest = graphene.Argument(MRSRequestInput)

    new_mrsrequest = graphene.Field(MRSRequestNode)

    @classmethod
    def mutate_and_get_payload(cls, args, context, info):
        data = args.get('mrsrequest')
        print('mrsrequest', data)
        return cls(new_mrsrequest=MRSRequest())

class Query(object):
    mrsrequest = graphene.Field(MRSRequestNode)
