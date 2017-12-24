from django import apps
from material.frontend.apps import ModuleMixin


class PMTAppConfig(ModuleMixin, apps.AppConfig):
    name = 'pmt'
    icon = '<i class="material-icons">hospital</i>'
    verbose_name = 'PMTs'

    def has_perm(self, user):
        return user.is_superuser
