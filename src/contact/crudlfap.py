from crudlfap import shortcuts as crudlfap

from .models import Contact


class ContactRouter(crudlfap.Router):
    model = Contact
    allowed_groups = ['Admin']
    material_icon = 'contact_mail'
    views = [
        crudlfap.DeleteObjectsView,
        crudlfap.DeleteView,
        crudlfap.ListView.clone(
            filter_fields=(
                'caisse',
            ),
            search_fields=(
                'name',
                'email',
                'message',
                'mrsrequest__display_id',
            ),
            table_sequence=(
                'creation_datetime',
                'caisse',
                'name',
                'subject',
            )
        ),
        crudlfap.DetailView,
    ]

ContactRouter().register()
