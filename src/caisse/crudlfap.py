from crudlfap import crudlfap

from .models import Caisse, Email


crudlfap.Router(
    Caisse,
    material_icon='domain',
    views=[
        crudlfap.CreateView,
        crudlfap.DeleteView,
        crudlfap.UpdateView,
        crudlfap.DetailView,
        crudlfap.FilterTables2ListView.clone(
            table_sequence=(
                'code',
                'name',
                'number',
                'active',
                'score'
            ),
            search_fields=(
                'code',
                'name',
                'number',
            ),
            filter_fields=(
                'active',
            )
        ),
    ]
).register()


crudlfap.Router(
    Email,
    material_icon='contact_mail',
    views=[
        crudlfap.FilterTables2ListView.clone(
            table_sequence=('email', 'caisse'),
        ),
    ]
).register()
