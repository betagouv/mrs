from crudlfap import crudlfap

from django import forms
from django.contrib.auth.models import Group

from django_filters import filters

from caisse.models import Caisse

from .models import User


class UserForm(forms.ModelForm):
    caisses = forms.ModelMultipleChoiceField(
        Caisse.objects.filter(active=True)
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
            'caisses',
            'profile',
        ]

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
