from crudlfap import crudlfap

from datetime import date

from django import template
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import EmailMessage
from django.db import models

import holidays


try:
    import uwsgi
except ImportError:
    uwsgi = None


def validate_caisse_number(value):
    try:
        value = int(value)
    except ValueError:
        raise ValidationError('Doit etre numerique')

    if not 0 < value < 999:
        raise ValidationError('Doit etre entre 0 et 999')


class Caisse(models.Model):
    code = models.CharField(max_length=9)
    name = models.CharField(
        verbose_name='nom',
        max_length=50,
    )
    number = models.CharField(
        max_length=3,
        verbose_name='numéro',
        validators=[validate_caisse_number],
    )
    liquidation_email = models.EmailField(
        verbose_name='email du service de liquidation',
        blank=True,
        null=True
    )
    active = models.BooleanField(
        verbose_name='activé',
        default=False,
    )
    score = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def short_code(self):
        return self.code[:5]


def caisse_number_format(sender, instance, **kwargs):
    instance.number = '{:03d}'.format(int(instance.number))
models.signals.pre_save.connect(caisse_number_format, sender=Caisse)


def daily_mail(force=False):
    if date.today() in holidays.France() and not force:
        return

    for caisse in Caisse.objects.filter(active=True):
        mrsrequests = caisse.mrsrequest_set.all().status('new').order_by(
            'creation_datetime')

        num = len(mrsrequests)
        if not num:
            continue

        context = dict(
            object_list=mrsrequests,
            BASE_URL=settings.BASE_URL,
            ADMIN_ROOT=crudlfap.site.views['home'].url,
        )

        email = EmailMessage(
            template.loader.get_template(
                'caisse/liquidation_daily_mail_title.txt',
            ).render(context).strip(),
            template.loader.get_template(
                'caisse/liquidation_daily_mail_body.html',
            ).render(context).strip(),
            settings.DEFAULT_FROM_EMAIL,
            [caisse.liquidation_email],
            reply_to=[settings.DEFAULT_FROM_EMAIL],
        )
        email.content_subtype = 'html'
        email.send()

if uwsgi:
    uwsgi.register_signal(99, "", daily_mail)
    for i in range(1, 5):
        uwsgi.add_cron(99, 0, 8, -1, -1, i)


class Email(models.Model):
    email = models.EmailField()
    caisse = models.ForeignKey('Caisse', on_delete=models.CASCADE)

    def __str__(self):
        return self.email
