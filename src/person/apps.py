from django import apps
from material.frontend.apps import ModuleMixin


class PersonAppConfig(ModuleMixin, apps.AppConfig):
    name = 'person'
    icon = '<i class="material-icons">people</i>'
    verbose_name = 'Personnes'

    def has_perm(self, user):
        return user.is_superuser
