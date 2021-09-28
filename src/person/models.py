import datetime

from django.core import validators
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext as _

from mrs.validators import name_validators


def nir_validate_alphanumeric(value):
    """Validate NIR number with Corsican letters support."""
    if not value:
        raise ValidationError(_('NIR_EXPECTED_NUMBER'))

    value = str(value)

    if len(value) < 7:
        raise ValidationError(_('NIR_EXPECTED_NUMBER'))

    # A and B are acceptable on 7th position ...
    if value[6] in ('A', 'B', 'a', 'b'):
        # only if 6th position character is 2 !
        if value[5] != '2':
            raise ValidationError(_('NIR_EXPECTED_2'))

        # Sounds like a regular corsican so far:
        # Patch that 7th position string into a 0 so that
        # any other letter will be detected in the next if
        # not isdigit() block
        value = value[:6] + '0' + value[7:]

    if not value.isdigit():
        raise ValidationError(_('NIR_EXPECTED_NUMBER'))


class Person(models.Model):
    first_name = models.CharField(
        max_length=70,
        verbose_name='Prénom',
        validators=name_validators,
    )
    last_name = models.CharField(
        max_length=70,
        verbose_name='Nom de famille',
        validators=name_validators,
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
    nir = models.CharField(
        max_length=13,
        verbose_name='Numéro de sécurité sociale',
        validators=[
            nir_validate_alphanumeric,
            validators.MinLengthValidator(13),
            # note that max_length attribute implies a max length validator
        ]
    )
    shifted = models.NullBooleanField(
        default=None,
        null=True,
        blank=True,
        verbose_name='Assuré a basculé',
    )
    creation_datetime = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        verbose_name='Date et heure de création',
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


def delete_orphan_persons():
    print('--- Deleting orphan Persons ---')
    orphan_persons = Person.objects.filter(mrsrequest__isnull=True)
    orphan_persons_count = orphan_persons.count()
    try:
        orphan_persons.delete()
        print(
            'Deleted {} orphan Persons'.format(
                orphan_persons_count
            )
        )
        print('--- END ---')
        return orphan_persons_count
    except Exception as e:
        print('Error : {}'.format(e))
        raise
