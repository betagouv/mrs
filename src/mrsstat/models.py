import datetime
import logging
import pytz

from denorm import denormalized

from django.db import models
from django.db import transaction

from caisse.models import Caisse
from institution.models import Institution
from mrsrequest.models import MRSRequest


logger = logging.getLogger(__name__)


class StatManager(models.Manager):
    def create_missing(self):
        first = MRSRequest.objects.order_by('creation_datetime').first()
        if not first:
            return
        caisses = Caisse.objects.filter(active=True)
        institutions = Institution.objects.all()
        current_date = datetime.date.today()

        today = True
        while current_date > first.creation_datetime.date():
            objects = self.create_missing_for_date(
                current_date,
                caisses,
                institutions
            )

            if today:
                for obj in objects:
                    obj.save()  # trigger refresh
                today = False

            current_date -= datetime.timedelta(days=1)

    @transaction.atomic
    def create_missing_for_date(self, current_date, caisses, institutions):
        objects = []
        objects.append(
            self.model.objects.get_or_create(
                date=current_date,
                caisse=None,
                institution=None,
            )[0]
        )

        for caisse in caisses:
            objects.append(
                self.model.objects.get_or_create(
                    date=current_date,
                    caisse=caisse,
                    institution=None,
                )[0]
            )

            for institution in institutions:
                objects.append(
                    self.model.objects.get_or_create(
                        date=current_date,
                        institution=institution,
                        caisse=caisse,
                    )[0]
                )

        for institution in institutions:
            objects.append(
                self.model.objects.get_or_create(
                    date=current_date,
                    institution=institution,
                    caisse=None,
                )[0]
            )
        return objects


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

    objects = StatManager()

    @property
    def mrsrequest_set(self):
        if hasattr(self, '_mrsrequest_set'):
            return self._mrsrequest_set

        qs = MRSRequest.objects.filter(
            creation_datetime__lte=datetime.datetime(
                self.date.year,
                self.date.month,
                self.date.day,
                23,
                59,
                tzinfo=pytz.utc
            )
        )
        if self.caisse:
            qs = qs.filter(caisse=self.caisse)
        if self.institution:
            qs = qs.filter(institution=self.institution)
        self._mrsrequest_set = qs
        return self._mrsrequest_set

    @denormalized(
        models.DecimalField,
        decimal_places=2,
        max_digits=5,
        null=True,
        verbose_name='Délai moyen de paiement (en jours)',
    )
    def validation_average_delay(self):
        return self.mrsrequest_set.aggregate(
            result=models.Avg('delay'))['result']

    @denormalized(
        models.IntegerField,
        verbose_name='Nombre total de demandes',
    )
    def mrsrequest_count_total(self):
        return self.mrsrequest_set.count()

    @denormalized(
        models.IntegerField,
        verbose_name='Nombre de nouvelles demandes',
    )
    def mrsrequest_count_new(self):
        return self.mrsrequest_set.status('new').count()

    @denormalized(
        models.IntegerField,
        verbose_name='Nombre de demandes validées',
    )
    def mrsrequest_count_validated(self):
        return self.mrsrequest_set.status('validated').count()

    @denormalized(
        models.IntegerField,
        verbose_name='Nombre de demandes rejettées',
    )
    def mrsrequest_count_rejected(self):
        return self.mrsrequest_set.status('rejected').count()

    @denormalized(
        models.IntegerField,
        verbose_name='Nombre de bascules de TAP',
    )
    def insured_shift_count(self):
        return self.mrsrequest_set.filter(insured_shift=True).count()

    @denormalized(
        models.DecimalField,
        decimal_places=2,
        max_digits=16,
        null=True,
    )
    def savings(self):
        return self.mrsrequest_set.aggregate(
            result=models.Sum('saving'))['result']

    def __str__(self):
        return 'Stat for {}, caisse: {}, etab: {}'.format(
            self.date, self.caisse, self.institution)

    class Meta:
        unique_together = (
            ('date', 'caisse', 'institution'),
        )
        ordering = ('date', 'caisse', 'institution',)
