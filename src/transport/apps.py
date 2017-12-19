from django import apps
from material.frontend.apps import ModuleMixin


class TransportAppConfig(ModuleMixin, apps.AppConfig):
    name = 'transport'
    icon = '<i class="material-icons">people</i>'
    verbose_name = 'Transports'

    def has_perm(self, user):
        return user.is_superuser
