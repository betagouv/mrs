import graphene

import caisse.schema
import mrsrequest.schema


class Query(caisse.schema.Query,
            mrsrequest.schema.Query,
            graphene.ObjectType):
    pass


class Mutation(mrsrequest.schema.Mutation,
               graphene.ObjectType):
    pass

schema = graphene.Schema(query=Query, mutation=Mutation)
