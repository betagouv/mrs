import datetime
import logging

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
    def create_missing_for_date(self, current_date, caisses=None,
                                institutions=None):

        caisses = caisses or []
        institutions = institutions or []

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
        ).aggregate(
            result=models.Avg('delay')
        )['result']

    @denormalized(
        models.IntegerField,
        verbose_name='Nombre de demandes soumises',
    )
    def mrsrequest_count_new(self):
        return self.mrsrequest_set.created(self.date).count()

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

    def __str__(self):
        return 'Stat for {}, caisse: {}, etab: {}'.format(
            self.date, self.caisse, self.institution)

    class Meta:
        unique_together = (
            ('date', 'caisse', 'institution'),
        )
        ordering = ('date', 'caisse', 'institution',)
