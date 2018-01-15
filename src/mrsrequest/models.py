import datetime
from decimal import Decimal
import uuid

from django.conf import settings
from django.core import validators
from django.db import models
from django.db.models import signals
from django.urls import reverse
from django.utils import timezone

from mrsattachment.models import MRSAttachment


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


class MRSRequestManager(models.Manager):
    def allowed_objects(self, request):
        return self.filter(id__in=self.allowed_uuids(request))

    def allowed_uuids(self, request):
        session = getattr(request, 'session', {})
        return session.get(self.model.SESSION_KEY, [])


class MRSRequest(models.Model):
    SESSION_KEY = 'MRSRequest.ids'

    STATUS_NEW = 0
    STATUS_VALIDATED = 1
    STATUS_REJECTED = 2

    STATUS_CHOICES = (
        (STATUS_NEW, 'Soumise'),
        (STATUS_VALIDATED, 'Validée'),
        (STATUS_REJECTED, 'Rejettée'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    form_id = models.CharField(
        max_length=12,
        verbose_name='Identifiant de formulaire',
        unique=True,
    )
    creation_datetime = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        verbose_name='Date et heure d\'enregistrement du formulaire',
    )
    insured = models.ForeignKey(
        'person.Person',
        on_delete=models.SET_NULL,
        null=True,
    )
    distance = models.PositiveIntegerField(
        verbose_name='Distance (km)',
        help_text='Kilométrage total parcouru',
        null=True,
    )
    expense = models.DecimalField(
        decimal_places=2, max_digits=6,
        blank=True, default=0,
        validators=[validators.MinValueValidator(Decimal('0.00'))],
        verbose_name='Montant total des frais (en € TTC)',
        help_text=(
            'Parking et/ou péage ou '
            'justificatif(s) de transport en commun'
        )
    )

    status = models.IntegerField(
        choices=STATUS_CHOICES,
        default=0,
    )

    objects = MRSRequestManager()

    class Meta:
        verbose_name = 'Requête'
        ordering = ['-creation_datetime']

    def __str__(self):
        return self.verbose_id

    @property
    def verbose_id(self):
        return self.form_id if self.form_id else str(self.id)

    def is_allowed(self, request):
        if request.user.is_staff:
            return True
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

    def get_admin_url(self):
        return reverse('admin:mrsrequest_mrsrequest_change', args=[self.pk])

    def get_reject_url(self):
        return reverse('mrsrequest:reject', args=[self.pk])

    def get_validate_url(self):
        return reverse('mrsrequest:validate', args=[self.pk])


def sqlite_form_id_trigger(sender, instance, **kwargs):
    """Postgresql has a trigger for this. SQLite is for testing."""
    i = 0
    prefix = datetime.date.today().strftime('%Y%m%d')

    def _gen():
        return '{}{:04d}'.format(prefix, i)
    form_id = _gen()

    while MRSRequest.objects.filter(form_id=form_id).count():
        i += 1
        form_id = _gen()
    instance.form_id = form_id
if 'postgres' not in settings.DATABASES['default']['ENGINE']:
    # an atomic trigger is setup for postgres by a migration
    signals.pre_save.connect(sqlite_form_id_trigger, sender=MRSRequest)


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


class Transport(models.Model):
    mrsrequest = models.ForeignKey(
        'mrsrequest.MRSRequest',
        on_delete=models.CASCADE,
    )

    date_depart = models.DateField(
        verbose_name='Aller',
        help_text='Date du trajet aller',
        null=True
    )
    date_return = models.DateField(
        verbose_name='Retour',
        help_text='Date du trajet retour',
        null=True
    )

    class Meta:
        ordering = ['mrsrequest']
