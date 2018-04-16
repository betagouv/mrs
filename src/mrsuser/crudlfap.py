from crudlfap import crudlfap

from .models import User

crudlfap.site[User]['update'].fields.append('caisses')
crudlfap.site[User]['create'].fields.append('caisses')
crudlfap.site[User]['list'].filter_fields.append('caisses')
