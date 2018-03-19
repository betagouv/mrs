import graphene

import mrsrequest.schema


class Query(mrsrequest.schema.Query, graphene.ObjectType):
    # This class will inherit from multiple Queries
    # as we begin to add more apps to our project
    pass

schema = graphene.Schema(query=Query, mutation=mrsrequest.schema.CreateMRSRequest)
