from django.contrib.auth.models import (
    AbstractUser,
    Group,
    UserManager,
)
from django.db import models


class UserManager(UserManager):
    def get_queryset(self):
        return super().get_queryset().prefetch_related('caisses', 'groups')

    def _create_user(self, *args, **kwargs):
        kwargs.pop('is_staff', False)
        return super()._create_user(*args, **kwargs)


class User(AbstractUser):
    caisses = models.ManyToManyField(
        'caisse.caisse',
        null=True,
    )

    objects = UserManager()

    @property
    def is_staff(self):
        return True

    @property
    def profile(self):
        try:
            return self.groups.all()[0].name.lower()
        except IndexError:
            return 'admin' if self.is_superuser else False

    class Meta(AbstractUser.Meta):
        db_table = 'auth_user'

    def add_group(self, groupname):
        """
        Add this user to a group by the group name.
        """
        name = groupname.strip().capitalize()
        if 'Upn' in name:
            name = 'UPN'
        group = Group.objects.get(name=name)
        self.groups.add(group)
        self.save()

    def add_groups(self, groupnames):
        for name in groupnames:
            self.add_group(name)
