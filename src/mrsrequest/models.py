import datetime
from decimal import Decimal
from denorm import denormalized
import pytz
import uuid

from django.conf import settings
from django.contrib.admin.models import LogEntry
from django.contrib.contenttypes.models import ContentType
from django.core import validators
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import signals
from django.urls import reverse
from django.utils import timezone

from mrsattachment.models import MRSAttachment


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


class Bill(MRSAttachment):
    mrsrequest = models.ForeignKey(
        'MRSRequest',
        null=True,
        on_delete=models.CASCADE,
    )

    class Meta:
        ordering = ['mrsrequest', 'id']
        verbose_name = 'Justificatif'

    def unlink(self):
        self.transport = None

    def get_delete_url(self):
        return reverse('mrsrequest:bill_destroy', args=[self.pk])

    def get_download_url(self):
        return reverse('mrsrequest:bill_download', args=[self.pk])


class MRSRequestQuerySet(models.QuerySet):
    @property
    def logentries(self):
        return LogEntry.objects.filter(
            content_type=ContentType.objects.get_for_model(self.model),
        )

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

        BIGFATWARNING this casts the LogEntry object_id
        values as a python list, because apparently
        comparing object_id's varchar with mrsrequest's
        UUID doesn't work in sql.

        .. py:parameter:: date

            Date or datetime object that will be casted into the datetimes of
            the *first* and *last* datetimes of the same day of
            settings.TIME_ZONE.

        .. py:parameter:: date__gte

            Date or datetime object that will be casted into the datetime of
            the *first* minute of the day of settings.TIME_ZONE, it will be
            used in a *greater than or equal* filter on LogEntry.action_time.

        .. py:parameter:: date__lte

            Date or datetime object that will be casted into the datetime of
            the *last* minute of the day of settings.TIME_ZONE, it will be used
            in a *lesser than or equal* filter on LogEntry.action_time.

        .. py:parameter:: datetime__gte

            Datetime object to pass as-is to LogEntry.action_time greater than
            or equal filter.

        .. py:parameter:: datetime__lte

            Datetime object to pass as-is to LogEntry.action_time lesser than
            or equal filter.

        """
        logentries = self.logentries.filter(
            action_flag__in=[
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
                action_time__gte=datetime__gte,
            )

        if datetime__lte:
            logentries = logentries.filter(
                action_time__lte=datetime__lte,
            )

        return self.filter(
            id__in=list(logentries.values_list('object_id', flat=True))
        ).distinct()

    def in_status_by(self, name, user):
        return self.status(name).status_by(name, user)

    def created(self, date):
        return self.filter(
            creation_datetime__gte=datetime_min(date),
            creation_datetime__lte=datetime_max(date),
        )

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
    distance = models.PositiveIntegerField(
        verbose_name='Distance (km)',
        help_text='Total des kilomètres parcourus',
        null=True,
    )
    expense = models.DecimalField(
        decimal_places=2, max_digits=6,
        default=0,
        validators=[validators.MinValueValidator(Decimal('0.00'))],
        verbose_name='Frais de péage et/ou transports',
        help_text=(
            'Somme totale des frais de péage'
            ' et/ou de transport en commun (en € TTC)'
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
    reject_template = models.ForeignKey(
        'mrsemail.EmailTemplate',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
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

    objects = MRSRequestManager()

    class Meta:
        verbose_name = 'Demande'
        ordering = ['-creation_datetime']

    def __str__(self):
        return str(self.display_id)

    def update_status(self, user, status, log_datetime=None,
                      create_logentry=False):

        self.status = MRSRequest.get_status_id(status)
        self.status_datetime = log_datetime or timezone.now()
        self.status_user = user
        self.save()

        if create_logentry:
            LogEntry.objects.create(
                action_flag=self.status,
                action_time=self.status_datetime,
                content_type=ContentType.objects.get_for_model(type(self)),
                user=self.status_user,
                object_id=self.pk,
            )

    def logentry_set(self):
        return LogEntry.objects.filter(
            content_type=ContentType.objects.get_for_model(type(self)),
            object_id=self.pk,
        ).order_by('-action_time')

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
        return Decimal(
            (
                ((self.distance or 0) * 1.62) +
                (1.9 * 2 * self.transport_set.count())
            ) * 0.91
        ).quantize(TWOPLACES)

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
        dis = self.distance * 0.3
        exp = float(self.expense or 0)
        return '%.2f' % (dis + exp)

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
        event = self.logentry_set().filter(
            action_flag=self.get_status_id('inprogress')
        ).first()

        if not event:
            return 0

        dt = pytz.timezone(settings.TIME_ZONE).normalize(event.action_time)
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
