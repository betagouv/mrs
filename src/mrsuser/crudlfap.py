from crudlfap import crudlfap

from .models import User

crudlfap.site[User]['update'].fields.append('caisses')
crudlfap.site[User]['create'].fields.append('caisses')
crudlfap.site[User]['list'].filter_fields.append('caisses')
crudlfap.site[User]['list'].table_fields.insert(0, 'caisses')
crudlfap.site[User]['list'].table_fields.insert(1, 'active')
