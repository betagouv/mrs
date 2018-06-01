from crudlfap import crudlfap

from django import forms
from django.contrib.auth.models import Group

from .models import User


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
crudlfap.site[User]['list'].filter_fields.append('caisses')
crudlfap.site[User]['list'].filter_fields.append('is_active')
crudlfap.site[User]['list'].table_fields.insert(0, 'caisses')
crudlfap.site[User]['list'].table_fields.insert(1, 'is_active')
del crudlfap.site[Group]
