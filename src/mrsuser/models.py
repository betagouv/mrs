from django.contrib.auth.models import (
    AbstractUser,
    Group,
    Permission,
    UserManager,
)
from django.contrib.contenttypes.models import ContentType
from django.db import models


class UserManager(UserManager):
    def get_queryset(self):
        return super().get_queryset().prefetch_related('caisses', 'groups')

    def _create_user(self, *args, **kwargs):
        if kwargs.pop('is_staff', False) and 'profile' not in kwargs:
            kwargs['group_names'] = ['upn']

        user = super()._create_user(*args, **kwargs)
        for group in kwargs['group_names']:
            user.groups.add(
                Group.objects.get_or_create(group)[0]
            )
        return user


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
            return False

    @property
    def profiles(self):
        return [g.name for g in view.request.user.groups.all()]

    class Meta(AbstractUser.Meta):
        db_table = 'auth_user'
