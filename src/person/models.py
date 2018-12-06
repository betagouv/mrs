import datetime

from django.core import validators
from django.db import models


class Person(models.Model):
    first_name = models.CharField(
        max_length=200,
        verbose_name='Prénom',
    )
    last_name = models.CharField(
        max_length=200,
        verbose_name='Nom de famille',
    )
    birth_date = models.DateField(
        null=True,
        verbose_name='Date de naissance',
        validators=[
            validators.MinValueValidator(
                datetime.date(year=1900, month=1, day=1)
            )
        ],
    )
    email = models.EmailField(
        null=True,
        verbose_name='Email',
    )

    use_email = models.BooleanField(
        default=False,
        null=True,
        blank=True,
        verbose_name="L'assuré autorise à utiliser son email.",
    )

    nir = models.BigIntegerField(
        verbose_name='Numéro de sécurité sociale',
        validators=[
            validators.
            MinValueValidator(
                1000000000000,
                message="Le NIR doit contenir 13 caracteres."),
        ]
    )
    shifted = models.NullBooleanField(
        default=None,
        null=True,
        blank=True,
        verbose_name='Assuré a basculé',
    )

    class Meta:
        ordering = ('last_name', 'first_name',)
        verbose_name = 'Personne'

    def __str__(self):
        return '%s %s %s' % (self.first_name, self.last_name, self.birth_date)

    def save(self, *args, **kwargs):
        """
        Validate all fields, since validators are not run on save by default.
        """
        self.full_clean()
        return super(Person, self).save(*args, **kwargs)

    def get_dates(self):
        dates = {'depart': dict(), 'return': dict()}

        valids = self.mrsrequest_set.filter(
            status=self.mrsrequest_set.model.STATUS_VALIDATED
        ).prefetch_related('transport_set')
        for mrsrequest in valids:
            transports = mrsrequest.transport_set.exclude(date_depart=None)
            for transport in transports:
                for i in ('depart', 'return'):
                    value = getattr(transport, f'date_{i}')

                    if i == 'return' and not value:
                        continue

                    if value not in dates[i].keys():
                        dates[i][value] = []
                    dates[i][value].append(mrsrequest)

        return dates

    def get_duplicate_dates(self):
        dupes = {'depart': dict(), 'return': dict()}

        for i, dates in self.get_dates().items():
            for date, mrsrequests in dates.items():
                if len(mrsrequests) == 1:
                    continue

                dupes[i][date] = mrsrequests

        return {k: v for k, v in dupes.items() if v}
