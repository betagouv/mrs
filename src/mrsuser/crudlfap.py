from crudlfap import crudlfap

from django import forms
from django.contrib.auth.models import Group

from django_filters import filters
import django_tables2 as tables

from .models import User


class StatusFilter(filters.ChoiceFilter):
    def __init__(self, *a, **k):
        k.setdefault('choices', (
            ('disabled', 'Désactivé'),
            ('upn', 'UPN'),
            ('admin', 'Admin'),
        ))
        k.setdefault('label', 'Statut')
        super().__init__(*a, **k)

    def filter(self, qs, value):
        if value == 'disabled':
            return qs.filter(is_active=False)
        elif value == 'upn':
            return qs.filter(is_superuser=False, is_staff=True)
        elif value == 'admin':
            return qs.filter(is_superuser=True)
        return qs


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'username',
            'password',
            'email',
            'caisses',
        ]

    def save(self, commit=True):
        self.instance.set_password(self.cleaned_data['password'])
        self.instance.is_staff = True
        return super().save(commit=commit)


del crudlfap.site[User].views['delete']
crudlfap.site[User]['update'].fields.append('caisses')
crudlfap.site[User]['create'].form_class = UserForm
crudlfap.site[User]['list'].filter_fields = [
    'status',
    'caisses',
]
crudlfap.site[User]['list'].filterset_extra_class_attributes = dict(
    status=StatusFilter()
)
crudlfap.site[User]['list'].table_fields = [
    'caisses',
    'is_active',
    'email',
    'first_name',
    'last_name',
    'status',
]
crudlfap.site[User]['list'].table_columns = dict(
    status=tables.Column(verbose_name='statut'),
)
del crudlfap.site[Group]
