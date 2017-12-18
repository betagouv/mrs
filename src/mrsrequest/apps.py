from django import apps
from material.frontend.apps import ModuleMixin


class MRSRequestAppConfig(ModuleMixin, apps.AppConfig):
    name = 'mrsrequest'
    icon = '<i class="material-icons">people</i>'
    verbose_name = 'Requêtes'

    def has_perm(self, user):
        return user.is_superuser
