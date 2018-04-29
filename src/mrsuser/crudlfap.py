from crudlfap import crudlfap

from django.contrib.auth.models import Group

from .models import User


crudlfap.site[User]['update'].fields.append('caisses')
crudlfap.site[User]['create'].fields.append('caisses')
crudlfap.site[User]['list'].filter_fields.append('caisses')
crudlfap.site[User]['list'].filter_fields.append('is_active')
crudlfap.site[User]['list'].table_fields.insert(0, 'caisses')
crudlfap.site[User]['list'].table_fields.insert(1, 'is_active')
del crudlfap.site[Group]
