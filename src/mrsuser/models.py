import secrets

from django import template
from django.conf import settings
from django.contrib.auth.models import (
    AbstractUser,
    Group,
    UserManager,
)
from django.db import models

from djcall.models import Caller


class UserManager(UserManager):
    def get_queryset(self):
        return super().get_queryset().prefetch_related('caisses', 'groups')

    def _create_user(self, *args, **kwargs):
        kwargs.pop('is_staff', False)
        return super()._create_user(*args, **kwargs)


class ProfileDescriptor:
    class Eq:
        def __init__(self, names, is_superuser):
            self.names = names
            if is_superuser:
                self.names.append('admin')

        def __eq__(self, value):
            return value.lower() in self.names

    def __get__(self, obj, type=None):
        return ProfileDescriptor.Eq(
            [g.name.lower() for g in obj.groups.all()],
            obj.is_superuser
        )


class User(AbstractUser):
    caisses = models.ManyToManyField(
        'caisse.caisse'
    )
    number = models.CharField(
        blank=False,
        null=True,
        max_length=30,
        verbose_name="Numéro d'agent",
    )

    objects = UserManager()

    profile = ProfileDescriptor()

    @property
    def is_staff(self):
        return True

    class Meta(AbstractUser.Meta):
        db_table = 'auth_user'

    def add_group(self, groupname):
        """
        Add this user to a group by the group name.
        """
        group = Group.objects.get(name__iexact=groupname.strip())
        self.groups.add(group)
        self.save()

    def add_groups(self, groupnames):
        for name in groupnames:
            self.add_group(name.strip())

    def password_reset(self, caisse):
        created = not self.password
        password = secrets.token_urlsafe(16)
        self.set_password(password)
        self.save()
        password_email_template = template.loader.get_template(
            'mrsuser/user_password_email.txt',
        )
        # In case of super admins not linked to any caisse, reply_to heads
        # to settings.TEAM_EMAIL
        email = caisse.habilitation_email if caisse else None

        if email:
            reply_to = email
        else:
            reply_to = settings.TEAM_EMAIL
        Caller(
            callback='djcall.django.email_send',
            kwargs=dict(
                subject=(
                    '[MRS] Votre mot de passe'
                    if created else
                    '[MRS] Votre nouveau mot de passe'
                ),
                body=password_email_template.render(dict(
                    created=created,
                    user=self,
                    password=password,
                    BASE_URL=settings.BASE_URL,
                )),
                to=[self.email],
                reply_to=[reply_to],
            )
        ).spool('mail')
