from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models


class UserManager(UserManager):
    def _create_user(self, *args, **kwargs):
        if kwargs.pop('is_superuser', False):
            kwargs['profile'] = 'admin'

        if kwargs.pop('is_staff', False) and 'profile' not in kwargs:
            kwargs['profile'] = 'upn'

        return super()._create_user(*args, **kwargs)


class User(AbstractUser):
    PROFILE_CHOICES = (
        ('admin', 'Admin'),
        ('upn', 'UPN'),
        ('stat', 'Stat'),
        ('support', 'Relation client'),
    )

    profile = models.CharField(
        choices=PROFILE_CHOICES,
        max_length=50,
        verbose_name='profil',
    )

    caisses = models.ManyToManyField(
        'caisse.caisse',
        null=True,
        blank=True,
    )

    objects = UserManager()

    @property
    def is_staff(self):
        return self.is_active

    @property
    def is_superuser(self):
        return self.profile == 'admin'

    class Meta(AbstractUser.Meta):
        db_table = 'auth_user'
