import datetime
from decimal import Decimal
from denorm import denormalized
import pytz
import uuid

from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.core import validators
from django.core.exceptions import ValidationError
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db.models import signals
from django.urls import reverse
from django.utils import timezone

from mrsattachment.models import MRSAttachment, MRSAttachmentManager

TWOPLACES = Decimal(10) ** -2


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


def datetime_min(date):
    return to_date_datetime(date, 0, 0, 0, 0)


def datetime_max(date):
    return to_date_datetime(date, 23, 59, 59, 999999)


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
                datetime__lte=None):

        if date:
            date__gte = date
            date__lte = date

        if date__gte:
            datetime__gte = datetime_min(date__gte)
        if date__lte:
            datetime__lte = datetime_max(date__lte)

        qs = self
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
    STATUS_REJECTED = 999
    STATUS_INPROGRESS = 1000
    STATUS_VALIDATED = 2000

    STATUS_CHOICES = (
        (STATUS_NEW, 'Soumise'),
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
    creation_ip = models.GenericIPAddressField(null=True)
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
        help_text='Total des kilomètres parcourus:'
        ' en cas de transports aller retour, ou de transports itératifs'
        ' indiquer le nombre total de km parcours.'
        ' (ex.pour 2 trajets de 40 km, indiquer 80 km)',
        null=True,
        blank=True,
    )
    expensevp = models.DecimalField(
        blank=True,
        decimal_places=2, max_digits=6,
        default=0,
        validators=[validators.MinValueValidator(Decimal('0.00'))],
        verbose_name='Frais de péage et/ou transports',
        help_text=(
            'Somme totale des frais de péage'
            ' et/ou de transport en commun (en € TTC)'
        )
    )
    modeatp = models.BooleanField(
        blank=True,
        default=False,
        verbose_name='Avez vous voyagé en transports en commun ?',
        help_text='(Avion, bus, métro, train, bateau…)',
    )
    expenseatp = models.DecimalField(
        blank=True,
        decimal_places=2, max_digits=6,
        default=0,
        validators=[validators.MinValueValidator(Decimal('0.00'))],
        verbose_name='Frais de transports',
        help_text=(
            'Somme totale des frais de'
            ' transport en commun (en € TTC)'
        )
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
    institution = models.ForeignKey(
        'institution.Institution',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    mandate_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Date de mandatement',
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

    objects = MRSRequestManager()

    class Meta:
        verbose_name = 'Demande'
        ordering = ['-creation_datetime']

    def __str__(self):
        return str(self.display_id)

    @property
    def modes(self):
        modes = []
        for mode in ['atp', 'vp']:
            if getattr(self, f'mode{mode}', None):
                modes.append(mode)
        return modes

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
    def get_status_label(self, number):
        for flag, label in self.STATUS_CHOICES:
            if flag == number:
                return label

    @classmethod
    def get_status_id(self, name):
        if isinstance(name, int):
            return name
        return getattr(self, 'STATUS_{}'.format(name.upper()))

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
        FORMAT_YMD = '%Y-%m-%d'
        entries = self.logentries.order_by('-datetime')
        for entry in entries:
            if entry.data and \
               'changed' in entry.data and \
               fieldname in entry.data['changed']:
                val = entry.data['changed'][fieldname][0]
                # parse the date string.
                if fieldname == 'birth_date':
                    val = datetime.datetime.strptime(val, FORMAT_YMD)
                    val = val.date()
                return val

        return False

    @denormalized(
        models.DecimalField,
        decimal_places=2,
        max_digits=8,
        null=True,
    )
    def saving(self):
        if not self.insured or not self.insured.shifted:
            return 0
        if not self.payment_base:
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
        request.session[self.SESSION_KEY][str(self.id)] = dict()

        # The above doesn't use the request.session setter, won't automatically
        # trigger session save unless we do the following
        request.session.modified = True

    def save_attachments(self):
        self.save_bills()
        self.save_pmt()

    def save_bills(self):
        Bill.objects.recorded_uploads(self.id).update(mrsrequest=self)

    def save_pmt(self):
        new_pmt = PMT.objects.recorded_uploads(self.id).last()

        try:
            current_pmt = self.pmt
        except PMT.DoesNotExist:
            pass
        else:
            if current_pmt == new_pmt:
                return
            else:
                current_pmt.delete()

        if new_pmt:
            new_pmt.mrsrequest = self
            new_pmt.save()

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
        if self.pmt:
            return len(self.pmt.binary) + sum(
                [len(b.binary) for b in self.bill_set.all()])
        return 0

    def get_admin_url(self):
        return reverse('admin:mrsrequest_mrsrequest_change', args=[self.pk])

    def get_reject_url(self):
        return reverse('mrsrequest:reject', args=[self.pk])

    def get_validate_url(self):
        return reverse('mrsrequest:validate', args=[self.pk])

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

    instance.data = {
        i: getattr(instance.insured, i) for i in (
            'first_name',
            'last_name',
            'nir',
            'email',
            'birth_date',
        )
    }
signals.pre_save.connect(initial_data, sender=MRSRequest)


class MRSRequestLogEntryManager(models.Manager):
    def get_queryset(self):
        return MRSRequestLogEntryQuerySet(self.model, using=self._db)


class MRSRequestLogEntry(models.Model):
    ACTION_UPDATE = 2  # same ids as for django.contrib.admin.LogEntry
    ACTION_CONTACT = 800

    ACTION_CHOICES = (
        (MRSRequest.STATUS_NEW, 'Soumise'),
        (ACTION_UPDATE, 'Modifiée'),
        (3, 'Effacée'),  # not used
        (MRSRequest.STATUS_REJECTED, 'Rejetée'),
        (MRSRequest.STATUS_INPROGRESS, 'En cours de liquidation'),
        (MRSRequest.STATUS_VALIDATED, 'Validée'),
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

    objects = MRSRequestLogEntryManager()

    class Meta:
        ordering = ('-datetime',)

    def __str__(self):
        return f'{self.mrsrequest}: {self.comment}'

    @classmethod
    def get_action_id(self, name):
        if isinstance(name, int):
            return name

        for value, name in self.ACTION_CHOICES:
            if name == name:
                return value


def creation_datetime_and_display_id(sender, instance, **kwargs):
    """Signal receiver executed at the beginning of MRSRequest.save()"""
    if instance.display_id:
        return

    if not instance.creation_datetime:
        instance.creation_datetime = timezone.now()

    normalized = pytz.timezone(settings.TIME_ZONE).normalize(
        instance.creation_datetime)
    prefix = normalized.strftime('%Y%m%d')
    last = MRSRequest.objects.filter(
        display_id__startswith=prefix,
    ).order_by('display_id').last()

    number = 0
    if getattr(last, 'display_id', None) and len(str(last.display_id)) == 12:
        number = int(str(last.display_id)[-4:]) + 1

    instance.display_id = '{}{:04d}'.format(prefix, number)
signals.pre_save.connect(creation_datetime_and_display_id, sender=MRSRequest)


class PMT(MRSAttachment):
    mrsrequest = models.OneToOneField(
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


def transport_date_validate(value):
    if value > timezone.now().date():
        raise ValidationError(
            'La date doit être égale ou anterieure à la date du jour',
        )


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

    class Meta:
        ordering = ['mrsrequest', 'date_depart']
