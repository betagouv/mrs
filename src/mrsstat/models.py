import datetime

from denorm import denormalized

from django.db import models
from django.db import transaction

from caisse.models import Caisse
from institution.models import Institution
from mrsrequest.models import MRSRequest


class StatManager(models.Manager):
    def create_missing(self):
        caisses = Caisse.objects.filter(active=True)
        institutions = Institution.objects.all()
        first = MRSRequest.objects.order_by('creation_datetime').first()
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
            creation_datetime__lte=self.date
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
    )
    def validation_average_delay(self):
        return self.mrsrequest_set.aggregate(
            result=models.Avg('delay'))['result']

    @denormalized(models.IntegerField)
    def mrsrequest_count_total(self):
        return self.mrsrequest_set.count()

    @denormalized(models.IntegerField)
    def mrsrequest_count_new(self):
        return self.mrsrequest_set.status('new').count()

    @denormalized(models.IntegerField)
    def mrsrequest_count_validated(self):
        return self.mrsrequest_set.status('validated').count()

    @denormalized(models.IntegerField)
    def mrsrequest_count_rejected(self):
        return self.mrsrequest_set.status('rejected').count()

    @denormalized(models.IntegerField)
    def insured_shift_count(self):
        return self.mrsrequest_set.filter(insured_shift=True).count()

    @denormalized(
        models.DecimalField,
        decimal_places=2,
        max_digits=5,
        null=True,
    )
    def savings(self):
        return self.mrsrequest_set.aggregate(
            result=models.Sum('saving'))['result']

    class Meta:
        unique_together = (
            ('date', 'caisse', 'institution'),
        )
