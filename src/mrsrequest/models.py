from decimal import Decimal
import pytz
import uuid

from django.conf import settings
from django.core import validators
from django.core.exceptions import ValidationError
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
        (STATUS_REJECTED, 'Rejetée'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    creation_datetime = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        verbose_name='Date et heure de la demande',
    )
    creation_ip = models.GenericIPAddressField(null=True)
    display_id = models.IntegerField(
        verbose_name='Numéro de demande',
        unique=True,
    )
    status_datetime = models.DateTimeField(
        db_index=True,
        null=True,
        verbose_name='Date et heure de changement de statut',
    )
    status_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        db_index=True,
        null=True,
        on_delete=models.SET_NULL,
        verbose_name='Auteur du changement de statut',
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
    distance = models.PositiveIntegerField(
        verbose_name='Distance (km)',
        help_text='Total des kilomètres parcourus',
        null=True,
    )
    expense = models.DecimalField(
        decimal_places=2, max_digits=6,
        default=0,
        validators=[validators.MinValueValidator(Decimal('0.00'))],
        verbose_name='Montant total des frais (en € TTC)',
        help_text=(
            'Somme totale des frais de stationnement et/ou péage'
            ' et/ou de transport en commun'
        )
    )

    status = models.IntegerField(
        choices=STATUS_CHOICES,
        verbose_name='Statut',
        default=0,
    )
    reject_template = models.ForeignKey(
        'mrsemail.EmailTemplate',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    institution = models.ForeignKey(
        'institution.Institution',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    objects = MRSRequestManager()

    class Meta:
        verbose_name = 'Demande'
        ordering = ['-creation_datetime']

    def __str__(self):
        return str(self.display_id)

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

    @property
    def total_size(self):
        return len(self.pmt.binary) + sum(
            [len(b.binary) for b in self.bill_set.all()])

    def get_admin_url(self):
        return reverse('admin:mrsrequest_mrsrequest_change', args=[self.pk])

    def get_reject_url(self):
        return reverse('mrsrequest:reject', args=[self.pk])

    def get_validate_url(self):
        return reverse('mrsrequest:validate', args=[self.pk])


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
        validators=[transport_date_validate],
    )
    date_return = models.DateField(
        verbose_name='Retour',
        help_text='Date du trajet retour',
        null=True,
        validators=[transport_date_validate],
    )

    class Meta:
        ordering = ['mrsrequest', 'date_depart']
