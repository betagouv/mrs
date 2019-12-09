from crudlfap import shortcuts as crudlfap

from datetime import date

from django import template
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import EmailMessage
from django.db import models
from djcall.models import Caller

import holidays


def validate_caisse_number(value):
    try:
        value = int(value)
    except ValueError:
        raise ValidationError('Doit etre numerique')

    if not 0 < value < 999:
        raise ValidationError('Doit etre entre 0 et 999')


class Region(models.Model):
    name = models.CharField(
        verbose_name='nom de la région',
        max_length=30,
    )
    insee_id = models.CharField(
        verbose_name='code INSEE de la région',
        max_length=2
    )
    cheflieu_code = models.CharField(
        verbose_name='code commune INSEE du chef lieu de la région',
        max_length=5
    )

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


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
    habilitation_email = models.EmailField(
        verbose_name='email du service d\'habilitation',
        blank=True,
        null=True
    )
    active = models.BooleanField(
        verbose_name='activé',
        default=False,
    )
    parking_enable = models.BooleanField(
        verbose_name='active la saisie de frais de parking',
        default=True,
    )
    score = models.PositiveIntegerField(default=0)
    import_datetime = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Dernier import'
    )

    # Une région englobe aucune ou plusieurs caisses
    # Une caisse peut appartenir à aucune ou plusieurs régions
    regions = models.ManyToManyField(Region)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def short_code(self):
        return self.code[:5]

    def get_conflicting_url(self):
        return '&'.join([
            crudlfap.site['mrsrequest.mrsrequest']['list'].url + '?',
            f'caisse={self.pk}',
            f'has_conflicts_accepted=2',
        ])

    def get_conflicted_url(self):
        return '&'.join([
            crudlfap.site['mrsrequest.mrsrequest']['list'].url + '?',
            f'caisse={self.pk}',
            f'has_conflicts_resolved=2',
        ])


def caisse_number_format(sender, instance, **kwargs):
    instance.number = '{:03d}'.format(int(instance.number))
models.signals.pre_save.connect(caisse_number_format, sender=Caisse)


def daily_mail(force=False):
    if date.today() in holidays.France() and not force:
        return

    for caisse in Caisse.objects.filter(active=True):
        mrsrequests = caisse.mrsrequest_set.all().status('new').order_by(
            'creation_datetime')

        if not len(mrsrequests):
            continue

        context = dict(
            object_list=mrsrequests,
            BASE_URL=settings.BASE_URL,
            ADMIN_ROOT=crudlfap.site.views['home'].url,
        )

        Caller(
            callback='djcall.django.email_send',
            kwargs=dict(
                subject=template.loader.get_template(
                    'caisse/liquidation_daily_mail_title.txt',
                ).render(context).strip(),
                body=template.loader.get_template(
                    'caisse/liquidation_daily_mail_body.html',
                ).render(context).strip(),
                to=[caisse.liquidation_email],
                reply_to=[settings.DEFAULT_FROM_EMAIL],
                content_subtype='html'
            )
        ).spool('mail')


def monthly_mail(force=False):
    from mrsrequest.models import today

    today = today()

    for caisse in Caisse.objects.filter(active=True).order_by('pk'):
        objects = caisse.mrsrequest_set.filter(
            mandate_date=None
        ).status(
            'validated'
        ).created(
            date__lte=date(
                today.year,
                today.month - 1,
                today.day,
            )
        ).order_by('creation_datetime')

        content = objects.csv()
        if not content.count('\n'):
            continue

        message = EmailMessage(
            subject=template.loader.get_template(
                'caisse/liquidation_monthly_mail_title.txt',
            ).render().strip(),
            body=template.loader.get_template(
                'caisse/liquidation_monthly_mail_body.html',
            ).render().strip(),
            to=[caisse.liquidation_email],
            reply_to=[settings.DEFAULT_FROM_EMAIL],
            attachments=[
                (
                    f'{today.year}-{today.month}-stats.csv',
                    content,
                    'text/csv',
                ),
            ]
        )
        message.content_subtype = 'html'
        message.send()


class Email(models.Model):
    email = models.EmailField()
    caisse = models.ForeignKey('Caisse', on_delete=models.CASCADE)

    def __str__(self):
        return self.email
