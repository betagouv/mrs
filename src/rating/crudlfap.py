from crudlfap import shortcuts as crudlfap

from .models import Rating


crudlfap.Router(Rating).register()
