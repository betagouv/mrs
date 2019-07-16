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
        if self.is_superuser:
            return 'admin'

        try:
            return self.groups.all()[0].name.lower()
        except IndexError:
            return False

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
            self.add_group(name)

    def password_reset(self):
        created = not self.password
        password = secrets.token_urlsafe(16)
        self.set_password(password)
        self.save()
        password_email_template = template.loader.get_template(
            'mrsuser/user_password_email.txt',
        )
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
                reply_to=[settings.TEAM_EMAIL],
            )
        ).spool('mail')
