from crudlfap import shortcuts as crudlfap

from .models import Caisse, Email


crudlfap.Router(
    Caisse,
    allowed_groups=['Admin'],
    material_icon='domain',
    views=[
        crudlfap.CreateView,
        crudlfap.DeleteView,
        crudlfap.UpdateView,
        crudlfap.DetailView,
        crudlfap.ListView.clone(
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
    allowed_groups=['Admin'],
    material_icon='contact_mail',
    views=[
        crudlfap.ListView.clone(
            table_sequence=('email', 'caisse'),
        ),
    ]
).register()
