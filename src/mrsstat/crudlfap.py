from crudlfap import crudlfap

from .models import Stat


class StatListView(crudlfap.ListView):
    pass


crudlfap.Router(
    Stat,
    material_icon='multiline_chart',
    views=[
        StatListView(),
    ]
).register()
