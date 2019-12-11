import collections
import datetime
from decimal import Decimal
from denorm import denormalized
import pytz
import secrets
import uuid

from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.core import validators
from django.core.exceptions import ValidationError
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models, transaction, IntegrityError
from django.db.models import signals
from django.urls import reverse
from django.utils import timezone

from mrs.settings import DATE_FORMAT_FR
from mrsattachment.models import MRSAttachment, MRSAttachmentManager
from person.models import Person

TWOPLACES = Decimal(10) ** -2

CSV_COLUMNS = (
    'caisse',
    'id',
    'nir',
    'naissance',
    'transport',
    'mandatement',
    'base',
    'montant',
    'bascule',
    'finess',
    'adeli',
)


def today():
    return datetime_date(datetime.datetime.now())


def to_date_datetime(date_or_datetime, hour, minute, second, microsecond):
    mytz = pytz.timezone(settings.TIME_ZONE)
    if isinstance(date_or_datetime, datetime.datetime):
        if timezone.is_aware(date_or_datetime):
            date = date_or_datetime.astimezone(mytz)
        else:
            date = mytz.localize(date_or_datetime)
    elif isinstance(date_or_datetime, datetime.date):
        date = date_or_datetime

    return mytz.localize(
        datetime.datetime(
            date.year,
            date.month,
            date.day,
            hour,
            minute,
            second,
            microsecond,
        )
    )


def datetime_date(date):
    return datetime_min(date).date()


def datetime_min(date):
    return to_date_datetime(date, 0, 0, 0, 0)


def datetime_max(date):
    return to_date_datetime(date, 23, 59, 59, 999999)


def transport_date_validate(value):
    if value > timezone.now().date():
        raise ValidationError(
            'La date doit être égale ou anterieure à la date du jour',
        )


class BillManager(MRSAttachmentManager):
    def __init__(self, *args, **kwargs):
        self.mode = kwargs.pop('mode', None)
        super().__init__(*args, **kwargs)

    def get_queryset(self):
        qs = super().get_queryset()
        if self.mode:
            qs = qs.filter(mode=self.mode)
        return qs


class Bill(MRSAttachment):
    MODE_VP = 'vp'
    MODE_ATP = 'atp'
    MODE_CHOICES = (
        (MODE_VP, 'Vehicule Personnel'),
        (MODE_ATP, 'Transports en commun'),
    )

    mrsrequest = models.ForeignKey(
        'MRSRequest',
        null=True,
        on_delete=models.CASCADE,
    )
    mode = models.CharField(
        choices=MODE_CHOICES,
        default='vp',
        db_index=True,
        max_length=3,
    )

    class Meta:
        ordering = ['mrsrequest', 'id']
        verbose_name = 'Justificatif'

    def unlink(self):
        self.transport = None

    def get_download_url(self):
        return reverse('mrsrequest:bill_download', args=[self.pk])

    def get_delete_url(self):
        return reverse('mrsrequest:bill_destroy', args=[self.pk])


class BillVP(Bill):
    MODE = Bill.MODE_VP
    objects = BillManager(mode=MODE)

    def __init__(self, *args, **kwargs):
        kwargs['mode'] = self.MODE
        super().__init__(*args, **kwargs)

    class Meta:
        proxy = True


class BillATP(Bill):
    MODE = Bill.MODE_ATP
    objects = BillManager(mode=MODE)

    def __init__(self, *args, **kwargs):
        kwargs['mode'] = self.MODE
        super().__init__(*args, **kwargs)

    class Meta:
        proxy = True
# if you're up for some sports then override the models.Model metaclass with
# your own and refactor the above


class MRSRequestQuerySet(models.QuerySet):
    def status(self, name):
        return self.filter(status=MRSRequest.get_status_id(name))

    def status_by(self, status, user):
        return self.status_filter(status, user=user)

    def status_changed(self, status, date):
        return self.status_filter(status, date=date)

    def status_filter(self,
                      *statuses,
                      date__gte=None,
                      date__lte=None,
                      date=None,
                      datetime__gte=None,
                      datetime__lte=None,
                      user=None):

        """Filter on the status logentries.

        .. py:parameter:: date

            Date or datetime object that will be casted into the datetimes of
            the *first* and *last* datetimes of the same day of
            settings.TIME_ZONE.

        .. py:parameter:: date__gte

            Date or datetime object that will be casted into the datetime of
            the *first* minute of the day of settings.TIME_ZONE, it will be
            used in a *greater than or equal* filter on LogEntry.datetime.

        .. py:parameter:: date__lte

            Date or datetime object that will be casted into the datetime of
            the *last* minute of the day of settings.TIME_ZONE, it will be used
            in a *lesser than or equal* filter on LogEntry.datetime.

        .. py:parameter:: datetime__gte

            Datetime object to pass as-is to LogEntry.datetime greater than
            or equal filter.

        .. py:parameter:: datetime__lte

            Datetime object to pass as-is to MRSRequestLogEntry.datetime lesser
            than or equal filter.

        """
        logentries = MRSRequestLogEntry.objects.filter(
            status__in=[
                MRSRequest.get_status_id(status)
                for status in statuses
            ],
        )

        if user:
            logentries = logentries.filter(user=user)

        if date:
            datetime__gte = datetime_min(date)
            datetime__lte = datetime_max(date)
        else:
            if date__gte:
                datetime__gte = datetime_min(date__gte)

            if date__lte:
                datetime__lte = datetime_min(date__lte)

        if datetime__gte:
            logentries = logentries.filter(
                datetime__gte=datetime__gte,
            )

        if datetime__lte:
            logentries = logentries.filter(
                datetime__lte=datetime__lte,
            )

        return self.filter(logentries__in=logentries).distinct()

    def in_status_by(self, name, user):
        return self.status(name).status_by(name, user)

    def created(self,
                date=None,
                date__gte=None,
                date__lte=None,
                datetime__gte=None,
                datetime__lte=None,
                caisse=None):

        if date:
            date__gte = date
            date__lte = date

        if date__gte:
            datetime__gte = datetime_min(date__gte)
        if date__lte:
            datetime__lte = datetime_max(date__lte)

        qs = self

        if caisse:
            qs = qs.filter(
                caisse=caisse
            )

        if datetime__gte:
            qs = qs.filter(creation_datetime__gte=datetime__gte)
        if datetime__lte:
            qs = qs.filter(creation_datetime__lte=datetime__lte)

        return qs

    def processed(self):
        return self.filter(
            status__in=(
                MRSRequest.STATUS_VALIDATED,
                MRSRequest.STATUS_REJECTED,
            ),
        )

    def csv(self):
        content = [';'.join(CSV_COLUMNS)]
        qs = self.select_related('insured').prefetch_related('transport_set')
        for obj in qs:
            date_depart = None
            for transport in obj.transport_set.all():
                if not date_depart or transport.date_depart < date_depart:
                    date_depart = transport.date_depart

            if date_depart is None:
                continue  # manually imported from old database

            content.append(';'.join([
                str(obj.caisse.number),
                str(obj.display_id),
                str(obj.insured.nir),
                obj.insured.birth_date.strftime(DATE_FORMAT_FR),
                date_depart.strftime(DATE_FORMAT_FR),
                '',
                '',
                '',
                '',
                '',
                '',
            ]))

        return '\n'.join(content)


class MRSRequestManager(models.Manager):
    def get_queryset(self):
        return MRSRequestQuerySet(self.model, using=self._db)

    def allowed_objects(self, request):
        return self.filter(id__in=self.allowed_uuids(request))

    def allowed_uuids(self, request):
        session = getattr(request, 'session', {})
        return session.get(self.model.SESSION_KEY, [])


class MRSRequest(models.Model):
    SESSION_KEY = 'MRSRequest.ids'

    STATUS_NEW = 1  # matches admin.models.ADDITION
    # Those have status different from admin flags
    STATUS_CANCELED = 100
    STATUS_REJECTED = 999
    STATUS_INPROGRESS = 1000
    STATUS_VALIDATED = 2000

    STATUS_CHOICES = (
        (STATUS_NEW, 'Soumise'),
        (STATUS_CANCELED, 'Annulée'),
        (STATUS_REJECTED, 'Rejetée'),
        (STATUS_INPROGRESS, 'En cours de liquidation'),
        (STATUS_VALIDATED, 'Validée'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    creation_datetime = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        verbose_name='Date et heure de la demande',
    )
    display_id = models.BigIntegerField(
        verbose_name='Numéro de demande',
        unique=True,
    )
    caisse = models.ForeignKey(
        'caisse.Caisse',
        on_delete=models.SET_NULL,
        null=True,
    )
    insured = models.ForeignKey(
        'person.Person',
        on_delete=models.SET_NULL,
        null=True,
    )
    insured_shift = models.NullBooleanField(
        default=None,
        null=True,
        blank=True,
        verbose_name='Assuré a basculé sur cette demande',
    )
    modevp = models.BooleanField(
        default=False,
        blank=True,
        verbose_name='Avez vous voyagé en véhicule personnel ?',
        help_text='(Voiture, moto)',
    )
    distancevp = models.PositiveIntegerField(
        verbose_name='Distance (km)',
        help_text='Indiquez le nombre total de kilomètres parcourus :'
        ' Par exemple, vous réalisez 2 trajets de 40 kilomètres'
        ' aller/retour, déclarez 80 kilomètres parcourus.',
        null=True,
        blank=True,
    )
    expensevp_toll = models.DecimalField(
        null=True,
        blank=True,
        decimal_places=2,
        max_digits=6,
        validators=[validators.MinValueValidator(Decimal('0.00'))],
        verbose_name='Frais de péage',
        help_text='Somme totale des frais de péage (en € TTC)',
    )
    expensevp_parking = models.DecimalField(
        null=True,
        blank=True,
        decimal_places=2,
        max_digits=6,
        validators=[validators.MinValueValidator(Decimal('0.00'))],
        verbose_name='Frais de stationnement',
        help_text='Somme totale des frais de stationnement (en € TTC)',
    )

    @denormalized(
        models.DecimalField,
        blank=True,
        null=True,
        decimal_places=2,
        max_digits=6,
        validators=[validators.MinValueValidator(Decimal('0.00'))],
        verbose_name='Total des frais',
        help_text='Somme des frais de péage et stationnement (en € TTC)'
    )
    def expensevp(self):
        if self.expensevp:
            return self.expensevp

        expensevp_parking = self.expensevp_parking or 0
        expensevp_toll = self.expensevp_toll or 0
        return expensevp_parking + expensevp_toll

    modeatp = models.BooleanField(
        blank=True,
        default=False,
        verbose_name='Avez vous voyagé en transports en commun ?',
        help_text='(Avion, bus, métro, train, bateau…)',
    )
    expenseatp = models.DecimalField(
        blank=True,
        null=True,
        decimal_places=2, max_digits=6,
        default=0,
        validators=[validators.MinValueValidator(Decimal('0.00'))],
        verbose_name='Frais de transports',
        help_text=(
            'Somme totale des frais de'
            ' transport en commun (en € TTC)'
        )
    )
    pel = models.CharField(
        max_length=14,
        verbose_name='Numéro de PMET',
        null=True,
        blank=True,
        validators=[
            validators.RegexValidator(
                '[a-zA-Z0-9]{14}',
                message='Le numéro de PMET doit comporter'
                ' 14 caractères alpha numériques',
            )
        ],
    )
    convocation = models.DateField(
        verbose_name='Date de convocation au service médical',
        null=True,
        blank=True,
        validators=[
            validators.MinValueValidator(
                datetime.date(year=2000, month=1, day=1)
            ),
            transport_date_validate,
        ],
    )
    status = models.IntegerField(
        choices=STATUS_CHOICES,
        verbose_name='Statut',
        default=STATUS_NEW,
    )
    status_datetime = models.DateTimeField(
        db_index=True,
        null=True,
        blank=True,
        verbose_name='Date et heure de changement de statut',
    )
    status_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        db_index=True,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name='Auteur du changement de statut',
    )
    suspended = models.BooleanField(
        db_index=True,
        blank=True,
        default=False
    )
    institution = models.ForeignKey(
        'institution.Institution',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name='Établissement',
    )
    mandate_datevp = models.DateField(
        null=True,
        blank=True,
        verbose_name='Date de mandatement VP',
        validators=[
            validators.MinValueValidator(
                datetime.date(year=2000, month=1, day=1)
            )
        ],
    )
    mandate_dateatp = models.DateField(
        null=True,
        blank=True,
        verbose_name='Date de mandatement ATP',
        validators=[
            validators.MinValueValidator(
                datetime.date(year=2000, month=1, day=1)
            )
        ],
    )
    payment_base = models.DecimalField(
        null=True,
        blank=True,
        max_digits=8,
        decimal_places=2,
        verbose_name='Base de remboursement',
    )
    payment_amount = models.DecimalField(
        null=True,
        blank=True,
        max_digits=8,
        decimal_places=2,
        verbose_name='Montant remboursé',
    )
    adeli = models.IntegerField(null=True, blank=True)
    data = JSONField(
        blank=True,
        encoder=DjangoJSONEncoder,
        null=True,
        verbose_name='Formulaire tel que soumit par l\'usager',
    )
    conflicts_accepted = models.PositiveIntegerField(
        default=0,
        verbose_name='Nb. signalements acceptés',
        help_text='Nombre de signalements acceptés pour cette demande',
    )
    conflicts_resolved = models.PositiveIntegerField(
        default=0,
        verbose_name='Nb. signalements résolus',
        help_text='Nombre de signalements résolus avant soumission',
    )
    token = models.CharField(
        default=secrets.token_urlsafe,
        null=True,
        editable=False,
        verbose_name='Token d\'authentification pour modifier la demande',
        max_length=255,
    )

    objects = MRSRequestManager()

    class Meta:
        verbose_name = 'Demande'
        ordering = ['-creation_datetime']

    @property
    def dates(self):
        if getattr(self, '_dates', None) is None:
            self._dates = set()
            for transport in self.transport_set.all():
                for date in transport.dates:
                    self._dates.add(date)
            self._dates = sorted(self._dates)
        return self._dates

    @property
    def duplicate_transports(self):
        if getattr(self, '_duplicate_transports', None) is None:
            self._duplicate_transports = Transport.objects.filter(
                mrsrequest__insured=self.insured,
                mrsrequest__status__in=(
                    self.STATUS_INPROGRESS,
                    self.STATUS_VALIDATED,
                ),
            ).exclude(
                models.Q(mrsrequest__pk=self.pk)
            ).filter(
                models.Q(date_depart__in=self.dates)
                | models.Q(date_return__in=self.dates)
            ).distinct().order_by(
                'mrsrequest__creation_datetime'
            ).select_related(
                'mrsrequest'
            ).prefetch_related('mrsrequest__transport_set')
        return self._duplicate_transports

    @property
    def duplicates_by_transport(self):
        if getattr(self, '_duplicates_dates', None) is None:
            dupes = dict()
            for date in self.dates:
                for transport in self.duplicate_transports:
                    if date in transport.dates:
                        dupes.setdefault(transport.mrsrequest, set())
                        dupes[transport.mrsrequest].add(date)

            self._duplicates_dates = collections.OrderedDict()
            for key in sorted(dupes.keys(), key=lambda x: x.creation_datetime):
                self._duplicates_dates[key] = sorted(dupes[key])

        return self._duplicates_dates

    def __str__(self):
        return str(self.display_id)

    @property
    def modes(self):
        modes = []
        for mode in ['atp', 'vp']:
            if getattr(self, f'mode{mode}', None):
                modes.append(mode)
        return modes

    def status_in(self, *names):
        return self.status in [
            getattr(self, f'STATUS_{name.upper()}')
            for name in names
        ]

    # todo: rename to status_update
    def update_status(self, user, status, log_datetime=None,
                      create_logentry=False):

        self.status = MRSRequest.get_status_id(status)
        self.status_datetime = log_datetime or timezone.now()
        self.status_user = user
        self.save()

        if not create_logentry:
            return

        self.logentries.create(
            datetime=self.status_datetime,
            user=self.status_user,
            comment=self.get_status_display(),
            action=self.status
        )

    @classmethod
    def get_status_label(cls, number):
        for flag, label in cls.STATUS_CHOICES:
            if flag == number:
                return label

    @classmethod
    def get_status_id(cls, name):
        if isinstance(name, int):
            return name
        return getattr(cls, 'STATUS_{}'.format(name.upper()))

    def denorm_reset(self):
        self.delay = self.cost = self.saving = None

    @denormalized(
        models.DecimalField,
        decimal_places=2,
        max_digits=10,
        null=True,
    )
    def taxi_cost(self):
        transport = self.transport_set.first()
        num = 1 if transport and not transport.date_return else 2
        return Decimal(
            (
                ((self.distancevp or 0) * 1.62)
                + (1.9 * num * self.transport_set.count())
            ) * 0.91
        ).quantize(TWOPLACES)

    def field_changed(self, fieldname):
        """
        If the field was changed, return its original value.
        """
        # The oldest logentry has the original value.
        if not hasattr(self, '_logentries'):
            self._logentries = self.logentries.order_by('datetime')
        for entry in self._logentries:
            if entry.data and \
               'changed' in entry.data and \
               fieldname in entry.data['changed']:
                val = entry.data['changed'][fieldname][0]
                return val

        return False

    @denormalized(
        models.DecimalField,
        decimal_places=2,
        max_digits=8,
        null=True,
        verbose_name='économie',
    )
    def saving(self):
        if not self.insured or not self.insured.shifted:
            return 0
        if not self.modevp or not self.payment_base:
            return
        return Decimal(
            float(self.taxi_cost) - float(self.payment_base)
        ).quantize(TWOPLACES)

    @denormalized(
        models.DecimalField,
        decimal_places=2,
        max_digits=5,
        null=True,
    )
    def delay(self):
        if not self.mandate_date:
            return
        mandate_datetime = datetime.datetime(
            self.mandate_date.year,
            self.mandate_date.month,
            self.mandate_date.day,
            0,
            tzinfo=pytz.timezone(settings.TIME_ZONE),
        )
        delta = mandate_datetime - self.creation_datetime_normalized
        return delta.days + (delta.seconds / 60 / 60 / 24)

    @property
    def status_days(self):
        return (timezone.now() - self.creation_datetime_normalized).days

    @property
    def days(self):
        return (timezone.now() - self.creation_datetime_normalized).days

    @property
    def creation_day_time(self):
        # french calendar date and tz time for creation_datetime
        return self.creation_datetime.astimezone(
            pytz.timezone(settings.TIME_ZONE)
        )

    @property
    def creation_day(self):
        # french calendar date for creation_datetime
        return self.creation_day_time.date()

    @property
    def waiting(self):
        return self.status not in (
            self.STATUS_VALIDATED,
            self.STATUS_REJECTED
        )

    @property
    def tooltip(self):
        if self.waiting:
            if self.days:
                return 'En attente de traitement depuis {} jours'.format(
                    self.days
                )
            else:
                return 'En attente de traitement depuis aujourd\'hui'
        return 'Traité'

    @property
    def color(self):
        if not self.waiting:
            return ''

        if self.days >= 6:
            return 'red'
        elif self.days >= 4:
            return 'orange'

        return ''

    @property
    def estimate(self):
        result = 0
        if self.distancevp:
            result += self.distancevp * 0.3
        if self.expensevp:
            result += float(self.expensevp)
        if self.expenseatp:
            result += float(self.expenseatp)
        return '%.2f' % result

    def is_allowed(self, request):
        return str(self.id) in request.session.get(self.SESSION_KEY, {})

    def allow(self, request):
        if self.SESSION_KEY not in request.session:
            request.session[self.SESSION_KEY] = {}

        request.session[self.SESSION_KEY].setdefault(str(self.id), dict())

        # The above doesn't use the request.session setter, won't automatically
        # trigger session save unless we do the following
        request.session.modified = True

    def save_bills(self):
        Bill.objects.recorded_uploads(self.id).update(mrsrequest=self)

    def delete_pmt(self):
        PMT.objects.recorded_uploads(self.id).delete()

    def save_pmt(self):
        PMT.objects.recorded_uploads(self.id).update(mrsrequest=self)

    def get_bills(self, mode=None):
        bills = getattr(self, '_bills', None)
        if not bills:
            self._bills = bills = self.bill_set.all()
        if not mode:
            return bills
        return [i for i in bills if i.mode == mode]

    # shortcuts to the above, for stupid django templates
    @property
    def billatps(self):
        return self.get_bills('atp')

    @property
    def billvps(self):
        return self.get_bills('vp')

    @property
    def total_size(self):
        if getattr(self, '_total_size', None) is None:
            self._total_size = sum(
                [
                    f.attachment_file.size
                    for f in
                    [*self.pmt_set.all()] + [*self.bill_set.all()]
                ]
            )
        return self._total_size

    def get_admin_url(self):
        return reverse('admin:mrsrequest_mrsrequest_change', args=[self.pk])

    def get_reject_url(self):
        return reverse('mrsrequest:reject', args=[self.pk])

    def get_validate_url(self):
        return reverse('mrsrequest:validate', args=[self.pk])

    def get_cancel_url(self):
        return reverse('demande-cancel', args=[self.pk, self.token])

    def get_update_url(self):
        return reverse('demande-update', args=[self.pk, self.token])

    @property
    def creation_date_normalized(self):
        return pytz.timezone(settings.TIME_ZONE).normalize(
            self.creation_datetime).strftime('%d/%m/%Y')

    @property
    def creation_datetime_normalized(self):
        return pytz.timezone(settings.TIME_ZONE).normalize(
            self.creation_datetime)

    @property
    def inprogress_day_number(self):
        event = self.logentries.filter(status=self.STATUS_INPROGRESS).first()

        if not event:
            return 0

        dt = pytz.timezone(settings.TIME_ZONE).normalize(event.datetime)
        return '{:03d}'.format(dt.timetuple().tm_yday)

    @property
    def order_number(self):
        previous = type(self).objects.filter(
            insured=self.insured,
            creation_datetime__gte=datetime_min(self.creation_datetime),
            creation_datetime__lte=self.creation_datetime,
        )

        if self.pk:
            previous = previous.exclude(pk=self.pk)

        number = previous.count() + 1

        if number > 99:
            return '99'

        return '{:02d}'.format(number)

    @property
    def mandate_date(self):
        dates = (self.mandate_datevp, self.mandate_dateatp)
        if dates[0] and dates[1]:
            return dates[0] if dates[0] > dates[1] else dates[1]

        for date in dates:
            if date:
                return date

    def make_display_id(self):
        normalized = pytz.timezone(settings.TIME_ZONE).normalize(
            self.creation_datetime)
        prefix = normalized.strftime('%Y%m%d')
        last = MRSRequest.objects.filter(
            display_id__startswith=prefix,
        ).order_by('display_id').last()

        number = 0
        last_display_id = getattr(last, 'display_id', None)
        if last_display_id and len(str(last_display_id)) == 12:
            number = int(str(last_display_id)[-4:]) + 1

        return int('{}{:04d}'.format(prefix, number))

    def save(self, *args, **kwargs):
        """
        Unfortunate display_id conflict handling.

        Despite our recommendations, product owner decided to generate ids
        according to rules which are victim of conflicts. At the beginning it
        was not a problem, but now that there are concurrent users on the
        platform it's of course a problem.

        Please forgive the horrible palliative fix that you are about to
        witness.
        """

        duplicate_display_id = 'duplicate key value violates unique constraint "mrsrequest_mrsrequest_display_id_key"'  # noqa

        if not self.creation_datetime:
            self.creation_datetime = timezone.now()

        if not self.display_id:
            self.display_id = self.make_display_id()

        tries = 100
        while tries:
            try:
                with transaction.atomic():
                    return super().save(*args, **kwargs)
            except IntegrityError as exc:
                # swallow duplicate "insane id" generation
                if not exc.args[0].startswith(duplicate_display_id):
                    raise

                if not tries:
                    raise

            self.display_id = self.display_id + 1
            tries -= 1


def remove_attachments_without_mrsrequest():
    print('--- Removing MRSAttachments without MRSRequest ---')
    try:
        pmts = PMT.objects.filter(
            pk__in=PMT.objects
            .filter(
                mrsrequest__isnull=True,
                creation_datetime__lt=(
                    datetime.datetime.now() - datetime.timedelta(
                        days=8
                    )
                )
            )
            .values_list('pk', flat=True)
        )
        pmts_count = pmts.count()
        pmts.delete()
        print('Deleted {} PMTs'.format(pmts_count))
    except Exception as e:
        print('Error : {}'.format(e))
        raise

    try:
        bills = Bill.objects.filter(
            pk__in=Bill.objects
            .filter(
                mrsrequest__isnull=True,
                creation_datetime__lt=(
                    datetime.datetime.now() - datetime.timedelta(
                        days=8
                    )
                )
            )
            .values_list('pk', flat=True)
        )
        bills_count = bills.count()
        bills.delete()
        print('Deleted {} Bills'.format(bills_count))
    except Exception as e:
        print('Error : {}'.format(e))
        raise
    print('--- END ---')
    return pmts_count, bills_count


def anonymize_mrsrequests_older_than_33_months():
    print('--- Anonymizing MRSRequest older than 33 months ---')
    anon_person, created = Person.objects.get_or_create(
        first_name="Nyme",
        last_name="Ano",
        birth_date=datetime.date(1980, 1, 20),
        email="ano@nyme.com",
        nir="1803333333333"
    )
    old_requests = MRSRequest.objects.filter(
        creation_datetime__lt=(
            datetime.datetime.now() - datetime.timedelta(
                days=33 * 31
            )
        )
    ).exclude(
        insured=anon_person
    )
    old_requests_count = old_requests.count()
    for mrsrequest in old_requests:
        try:
            mrsrequest.data = None
            mrsrequest.adeli = None
            mrsrequest.pel = None
            mrsrequest.insured = anon_person
            mrsrequest.save()
            for pmt in mrsrequest.pmt_set.all():
                pmt.filename = "1x1.png"
                pmt.attachment_file = "1x1.png"
                pmt.save()
            for bill in mrsrequest.bill_set.all():
                bill.filename = "1x1.png"
                bill.attachment_file = "1x1.png"
                bill.save()

        except Exception as e:
            print('Error : {}'.format(e))
            raise
    print('Anonymized {} MRSRequests'.format(
        old_requests_count)
    )
    print('--- END ---')
    return old_requests_count


class MRSRequestLogEntryQuerySet(models.QuerySet):
    def filter(self, **kwargs):
        """Patches any status that's been given as a string."""
        status = kwargs.pop('status', None)
        status__in = kwargs.pop('status__in', [status] if status else None)

        if status__in:
            kwargs['action__in'] = [
                self.model.get_action_id(i) if isinstance(i, str) else i
                for i in status__in
            ]

        return super().filter(**kwargs)


def initial_data(sender, instance, **kwargs):
    if instance.data or not instance.insured:
        return

    insured = instance.insured
    instance.data = dict(
        birth_date=insured.birth_date.strftime(DATE_FORMAT_FR),
        nir=insured.nir,
        email=insured.email,
        first_name=insured.first_name,
        last_name=insured.last_name,
        distancevp=instance.distancevp
    )
signals.pre_save.connect(initial_data, sender=MRSRequest)


class MRSRequestLogEntry(models.Model):
    ACTION_NEW = 1  # same as MRSRequest.STATUS_NEW
    ACTION_UPDATE = 2  # same ids as for django.contrib.admin.LogEntry
    ACTION_CANCELED = 100
    ACTION_CONTACT = 800
    ACTION_SUSPEND = 900
    ACTION_REJECTED = 999
    ACTION_INPROGRESS = 1000
    ACTION_VALIDATED = 2000

    ACTION_CHOICES = (
        (ACTION_NEW, 'Soumise'),
        (ACTION_UPDATE, 'Modifiée'),
        (3, 'Effacée'),  # not used
        (ACTION_CANCELED, 'Annulée'),
        (ACTION_SUSPEND, 'Suspendue'),
        (ACTION_REJECTED, 'Rejetée'),
        (ACTION_INPROGRESS, 'En cours de liquidation'),
        (ACTION_VALIDATED, 'Validée'),
        (ACTION_CONTACT, 'Contacté'),
    )

    datetime = models.DateTimeField(
        verbose_name='Date et heure',
        default=timezone.now,
        editable=False,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        models.CASCADE,
        verbose_name='Utilisateur',
        null=True,
    )
    mrsrequest = models.ForeignKey(
        'MRSRequest',
        on_delete=models.CASCADE,
        related_name='logentries',
    )
    comment = models.TextField('Commentaire', blank=True)
    data = JSONField(
        blank=True,
        null=True,
        encoder=DjangoJSONEncoder,
    )
    action = models.SmallIntegerField(choices=ACTION_CHOICES)
    emailtemplate = models.ForeignKey(
        'mrsemail.EmailTemplate',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )

    objects = MRSRequestLogEntryQuerySet.as_manager()

    class Meta:
        ordering = ('-datetime',)
        verbose_name = 'Historique'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'{self.mrsrequest}: {self.comment}'

    @classmethod
    def get_action_id(cls, name):
        if isinstance(name, int):
            return name

        for value, name in cls.ACTION_CHOICES:
            if name == name:
                return value

    @property
    def date(self):
        return datetime_date(self.datetime)

    def get_icons(self):
        """
        Return a string with possibly more than one icon names
        corresponding to the fields changed in this logentry.
        """
        icons = []
        action_icons = {
            self.ACTION_CONTACT: 'email',
            MRSRequestLogEntry.ACTION_SUSPEND: 'pause',
            MRSRequest.STATUS_REJECTED: 'do_not_disturb_on',
            MRSRequest.STATUS_CANCELED: 'do_not_disturb_on',
            MRSRequest.STATUS_INPROGRESS: 'playlist_add_check',
            MRSRequest.STATUS_VALIDATED: 'check_circle',
        }
        changed = self.data.get('changed', None) if self.data else None
        if changed:
            if 'nir' in changed:
                icons.append('perm_identity')
            if 'birth_date' in changed:
                icons.append('directions_car')
            if 'distancevp' in changed:
                icons.append('date_range')
        elif self.action in action_icons:
            icons.append(action_icons[self.action])
        return ' '.join(icons)


class PMT(MRSAttachment):
    mrsrequest = models.ForeignKey(
        'mrsrequest.MRSRequest',
        null=True,
        on_delete=models.CASCADE,
    )

    def unlink(self):
        self.mrsrequest = None

    def __str__(self):
        return 'PMT: {}'.format(self.mrsrequest_uuid)

    def get_delete_url(self):
        return reverse('mrsrequest:pmt_destroy', args=[self.pk])

    def get_download_url(self):
        return reverse('mrsrequest:pmt_download', args=[self.pk])

    class Meta:
        ordering = ['mrsrequest', 'id']


class TransportQuerySet(models.QuerySet):
    def annotate_duplicates(self):
        seen = set()
        for number, transport in enumerate(self, start=1):
            if not transport.date_depart:
                continue

            transport.date_depart_is_duplicate = transport.date_depart in seen

            if transport.date_return:
                transport.date_return_is_duplicate = (
                    transport.date_return in seen
                )

            seen.add(transport.date_depart)

            if transport.date_return:
                seen.add(transport.date_return)

        return self


class TransportManager(models.Manager):
    def get_queryset(self):
        return TransportQuerySet(self.model, using=self._db)


class Transport(models.Model):
    mrsrequest = models.ForeignKey(
        'mrsrequest.MRSRequest',
        on_delete=models.CASCADE,
    )

    date_depart = models.DateField(
        verbose_name='Aller',
        help_text='Date du trajet aller',
        null=True,
        validators=[
            validators.MinValueValidator(
                datetime.date(year=2000, month=1, day=1)
            ),
            transport_date_validate,
        ],
    )
    date_return = models.DateField(
        verbose_name='Retour',
        help_text='Date du trajet retour',
        null=True,
        validators=[
            validators.MinValueValidator(
                datetime.date(year=2000, month=1, day=1)
            ),
            transport_date_validate,
        ],
    )

    DATES = ('depart', 'return')

    objects = TransportManager()

    class Meta:
        ordering = ['mrsrequest', 'date_depart']

    @property
    def dates(self):
        return [i for i in (self.date_depart, self.date_return) if i]
