from crudlfap import shortcuts as crudlfap

from .models import Contact


class ContactListView(crudlfap.ListView):
    search_fields = (
        'name',
        'email',
        'message',
        'mrsrequest__display_id',
    )

    table_sequence = (
        'creation_datetime',
        'caisse',
        'name',
        'subject',
    )

    def get_show_caisse_filter(self):
        self.show_caisse_filter = (
            self.request.user.caisses.count() > 1
            or self.request.user.profile == 'admin'
        )

    def get_filterset(self):
        filterset = super().get_filterset() or self.filterset
        form = filterset.form
        if 'caisse' in form.fields and self.request.user.profile != 'admin':
            form.fields['caisse'].queryset = self.request.user.caisses.all()
        return filterset

    def get_filter_fields(self):
        return ['caisse'] if self.show_caisse_filter else []


class ContactRouter(crudlfap.Router):
    model = Contact
    allowed_groups = ['Admin', 'Superviseur']
    material_icon = 'contact_mail'
    views = [
        crudlfap.DeleteObjectsView,
        crudlfap.DeleteView,
        ContactListView,
        crudlfap.DetailView,
    ]

    def get_queryset(self, view):
        user = view.request.user

        if user.is_superuser or user.profile == 'admin':
            return self.model.objects.all()
        elif user.profile == 'superviseur':
            return self.model.objects.filter(
                caisse__in=view.request.user.caisses.all()
            )

        return self.model.objects.none()

ContactRouter().register()
