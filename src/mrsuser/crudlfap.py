from crudlfap import shortcuts as crudlfap

from django import forms
from django.contrib.auth.models import Group

from caisse.models import Caisse

from .models import User


class UserForm(forms.ModelForm):
    groups = forms.ModelMultipleChoiceField(
        Group.objects.all(),
        required=False,
    )
    caisses = forms.ModelMultipleChoiceField(
        Caisse.objects.filter(active=True),
        required=False,
    )
    new_password = forms.CharField(
        label='Mot de passe',
        required=False,
        help_text='Laisser ce champs vide pour ne pas changer le mot de passe'
    )

    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'username',
            'email',
            'groups',
            'caisses',
            'is_superuser',
        ]

    def clean(self):
        data = super().clean()
        groups = data.get('groups', [])
        caisses = self.cleaned_data.get('caisses', [])
        su = data.get('is_superuser', False)

        if not su and not groups:
            self.add_error('groups', 'Ce champ est obligatoire.')

        admin = False
        for group in groups:
            if group.name == 'Admin':
                admin = True

        if not (admin or su) and not caisses:
            self.add_error('caisses', 'Ce champ est obligatoire.')
        return data

    def clean_new_password(self):
        new_password = self.cleaned_data.get('new_password', '')
        if not (self.instance.password or new_password):
            raise forms.ValidationError('Ce champ est obligatoire.')
        return new_password

    def save(self, commit=True):
        if self.cleaned_data.get('new_password', ''):
            self.instance.set_password(self.cleaned_data['new_password'])
        return super().save(commit=commit)


del crudlfap.site[User].views['delete']
crudlfap.site[User]['update'].form_class = UserForm
crudlfap.site[User]['update'].fields.append('is_active')
crudlfap.site[User]['create'].form_class = UserForm
crudlfap.site[User]['list'].filter_fields = [
    'groups',
    'caisses',
]
crudlfap.site[User]['list'].table_fields = [
    'caisses',
    'is_active',
    'email',
    'first_name',
    'last_name',
    'groups',
]

crudlfap.site[User].allowed_groups = ['Admin']
crudlfap.site[Group].allowed_groups = ['Admin']
