from crudlfap import crudlfap

from django import forms
from django.contrib.auth.models import Group

from django_filters import filters

from caisse.models import Caisse

from .models import User


class UserForm(forms.ModelForm):
    caisses = forms.ModelMultipleChoiceField(
        Caisse.objects.all()
    )

    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'username',
            'password',
            'email',
            'caisses',
            'profile',
        ]

    def save(self, commit=True):
        if self.cleaned_data.get('password', ''):
            self.instance.set_password(self.cleaned_data['password'])
        return super().save(commit=commit)


del crudlfap.site[User].views['delete']
crudlfap.site[User]['update'].form_class = UserForm
crudlfap.site[User]['update'].fields.append('is_active')
crudlfap.site[User]['create'].form_class = UserForm
crudlfap.site[User]['list'].filterset_extra_class_attributes = dict(
    profile=filters.ChoiceFilter(choices=User.PROFILE_CHOICES)
)
crudlfap.site[User]['list'].filter_fields = [
    'profile',
    'caisses',
]
crudlfap.site[User]['list'].table_fields = [
    'caisses',
    'is_active',
    'email',
    'first_name',
    'last_name',
    'profile',
]
del crudlfap.site[Group]
