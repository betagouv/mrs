from crudlfap import crudlfap

from .models import Institution


crudlfap.Router(
    Institution,
    material_icon='local_hospital',
    views=[
        crudlfap.FilterTables2ListView(
            table_sequence=('finess', 'origin')
        ),
        crudlfap.CreateView,
        crudlfap.UpdateView,
        crudlfap.DeleteView,
    ]
).register()
