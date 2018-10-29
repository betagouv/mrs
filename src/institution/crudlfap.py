from crudlfap import shortcuts as crudlfap

from .models import Institution


crudlfap.Router(
    Institution,
    allowed_groups=['Admin'],
    material_icon='local_hospital',
    namespace='institutionrouter',
    views=[
        crudlfap.ListView(
            table_sequence=('finess', 'origin')
        ),
        crudlfap.CreateView,
        crudlfap.UpdateView,
        crudlfap.DeleteView,
    ]
).register()
