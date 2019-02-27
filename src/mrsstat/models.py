import datetime
import itertools
import logging
import os

from denorm import denormalized

from django.db import models
from django.db import transaction
from django.db.models import signals
from djcall.models import Caller

from caisse.models import Caisse
from institution.models import Institution
from person.models import Person
from mrsrequest.models import datetime_max, today, MRSRequest


logger = logging.getLogger(__name__)


def date_range(min_date, max_date=None):
    max_date = max_date or datetime.date.today()
    date = min_date
    while max_date > date:
        yield date
        date += datetime.timedelta(days=1)


class StatManager(models.Manager):
    def create_missing(self):
        first = MRSRequest.objects.order_by('creation_datetime').first()
        if not first:
            return

        for i in date_range(first.creation_datetime.date()):
            self.update_date(i)

    @transaction.atomic
    def update_date(self, date, caisses=None, institutions=None):
        if caisses is None:
            caisses = list(Caisse.objects.filter(active=True)) + [None]

        if institutions is None:
            institutions = list(Institution.objects.all()) + [None]

        for caisse, institution in itertools.product(caisses, institutions):
            existing = self.filter(
                date=date, caisse=caisse, institution=institution
            ).first()

            if existing:
                existing.denorm_reset()
                existing.save()
            else:
                self.create(
                    date=date, caisse=caisse, institution=institution
                )


class Stat(models.Model):
    date = models.DateField()
    caisse = models.ForeignKey(
        'caisse.Caisse',
        on_delete=models.CASCADE,
        null=True
    )
    institution = models.ForeignKey(
        'institution.Institution',
        on_delete=models.CASCADE,
        null=True
    )
    mrsrequest_count_conflicted = models.IntegerField(
        verbose_name='Nb. affichages page de confirmation',
        default=0,
    )
    mrsrequest_count_conflicting = models.IntegerField(
        verbose_name='Nb. demandes soumises avec conflit non resolu',
        default=0,
    )

    objects = StatManager()

    def denorm_reset(self):
        self.savings = None
        self.validation_average_delay = None
        self.insured_shifts = None
        self.mrsrequest_count_new = None
        self.mrsrequest_count_inprogress = None
        self.mrsrequest_count_validated = None
        self.mrsrequest_count_rejected = None
        self.mrsrequest_total_new = None
        self.mrsrequest_total_inprogress = None
        self.mrsrequest_total_validated = None
        self.mrsrequest_total_rejected = None
        self.insured_shifts_total = None

    @property
    def mrsrequest_set(self):
        """QS of MRSRequest with corresponding caisse and institution."""
        if hasattr(self, '_mrsrequest_set'):
            return self._mrsrequest_set

        qs = MRSRequest.objects.all()
        if self.caisse:
            qs = qs.filter(caisse=self.caisse)
        if self.institution:
            qs = qs.filter(institution=self.institution)
        self._mrsrequest_set = qs
        return self._mrsrequest_set

    @denormalized(
        models.DecimalField,
        decimal_places=2,
        max_digits=9,
        null=True,
        verbose_name='Econnomie réalisée',
    )
    def savings(self):
        return self.mrsrequest_set.status_changed(
            'validated',
            self.date,
        ).aggregate(
            result=models.Sum('saving')
        )['result']

    @denormalized(
        models.DecimalField,
        decimal_places=2,
        max_digits=5,
        null=True,
        verbose_name='Délai moyen de paiement (en jours)',
    )
    def validation_average_delay(self):
        return self.mrsrequest_set.status_changed(
            'validated',
            self.date,
        ).aggregate(result=models.Avg('delay'))['result']

    @denormalized(
        models.IntegerField,
        default=0,
        verbose_name='Nombre de bascules',
    )
    def insured_shifts(self):
        return self.mrsrequest_set.created(self.date).filter(
            insured_shift=True).count()

    @denormalized(
        models.IntegerField,
        verbose_name='Nombre de demandes soumises',
    )
    def mrsrequest_count_new(self):
        return self.mrsrequest_set.created(self.date).count()

    @denormalized(
        models.IntegerField,
        verbose_name='Nombre de demandes en cours',
    )
    def mrsrequest_count_inprogress(self):
        return self.mrsrequest_set.status_changed(
            'inprogress',
            self.date
        ).count()

    @denormalized(
        models.IntegerField,
        verbose_name='Nombre de demandes validées',
    )
    def mrsrequest_count_validated(self):
        return self.mrsrequest_set.status_changed(
            'validated',
            self.date
        ).count()

    @denormalized(
        models.IntegerField,
        verbose_name='Nombre de demandes rejettées',
    )
    def mrsrequest_count_rejected(self):
        return self.mrsrequest_set.status_changed(
            'rejected',
            self.date,
        ).count()

    @denormalized(
        models.IntegerField,
        verbose_name='Nombre cumulé de demandes soumises',
    )
    def mrsrequest_total_new(self):
        return self.mrsrequest_set.created(
            datetime__lte=datetime_max(self.date)
        ).count()

    @denormalized(
        models.IntegerField,
        verbose_name='Nombre cumulé de demandes en cours',
    )
    def mrsrequest_total_inprogress(self):
        return self.mrsrequest_set.status_filter(
            'inprogress',
            datetime__lte=datetime_max(self.date),
        ).count()

    @denormalized(
        models.IntegerField,
        verbose_name='Nombre cumulé de demandes validées',
    )
    def mrsrequest_total_validated(self):
        return self.mrsrequest_set.status_filter(
            'validated',
            datetime__lte=datetime_max(self.date),
        ).count()

    @denormalized(
        models.IntegerField,
        verbose_name='Nombre cumulé de demandes rejettées',
    )
    def mrsrequest_total_rejected(self):
        return self.mrsrequest_set.status_filter(
            'rejected',
            datetime__lte=datetime_max(self.date),
        ).count()

    @denormalized(
        models.IntegerField,
        default=0,
        verbose_name='Nombre cumulé de bascules',
    )
    def insured_shifts_total(self):
        return self.mrsrequest_set.created(
            datetime__lte=datetime_max(self.date),
        ).filter(
            insured_shift=True
        ).count()

    def __str__(self):
        return 'Stat for {}, caisse: {}, etab: {}'.format(
            self.date, self.caisse, self.institution)

    class Meta:
        unique_together = (
            ('date', 'caisse', 'institution'),
        )
        ordering = ('date', 'caisse', 'institution',)


def update_stat_for_mrsrequest(**kwargs):
    m = MRSRequest.objects.get(pk=kwargs['pk'])
    for date in date_range(m.creation_datetime.date()):
        Stat.objects.update_date(
            date,
            [None, m.caisse],
            [None, m.institution],
        )


def stat_update(sender, instance, **kwargs):
    Caller(
        callback='mrsstat.models.update_stat_for_mrsrequest',
        kwargs=dict(pk=instance.pk),
    ).spool('stat')


def stat_update_person(sender, instance, **kwargs):
    if instance.shifted:
        for req in instance.mrsrequest_set.all():
            # trigger denorm recalculate
            req.saving = None
            req.save()
            stat_update(type(req), req)


def increment(name, count, date=None):
    date = date or today()
    stat = Stat.objects.filter(date=date).first()
    if not stat:
        stat = Stat(date=date)
    counter = getattr(stat, name, 0)
    result = counter + count
    setattr(stat, name, result)
    stat.save()
    logger.debug(f'Incremented {name}={counter}+{count}={result}')


if not os.getenv('CI'):
    signals.post_save.connect(stat_update, sender=MRSRequest)
    signals.post_save.connect(stat_update_person, sender=Person)
