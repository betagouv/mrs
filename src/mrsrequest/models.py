import io
import uuid

from django.db import models


class MRSAttachement(models.Model):
    filename = models.CharField(max_length=255)
    creation_datetime = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Heure d\'enregistrement du fichier')
    binary = models.BinaryField(
        verbose_name='Prescription Médicale de Transport')

    class Meta:
        abstract = True

    @classmethod
    def get_upload_body(cls, upload):
        body = io.BytesIO()
        for chunk in upload.chunks():
            body.write(chunk)
        body.seek(0)  # rewind read point to beginning of registry
        return body.read()


class MRSRequestManager(models.Manager):
    def allowed_objects(self, request):
        session = getattr(request, 'session', {})
        return self.filter(id__in=session.get(self.model.SESSION_KEY, []))


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
    submiter_email = models.EmailField(
        null=True,
    )
    creation_datetime = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Date et heure d\'enregistrement du formulaire')

    transported = models.ForeignKey(
        'person.Person',
        null=True,
        on_delete=models.SET_NULL,
        related_name='transported_transport_set',
    )
    insured = models.ForeignKey(
        'person.Person',
        null=True,
        on_delete=models.SET_NULL,
        related_name='insured_transport_set',
    )

    status = models.IntegerField(
        choices=STATUS_CHOICES,
        default=0,
    )

    objects = MRSRequestManager()

    def is_allowed(self, request):
        return self.id in request.session.get(self.SESSION_KEY, {})

    def allow(self, request):
        if self.SESSION_KEY not in request.session:
            request.session[self.SESSION_KEY] = {}
        request.session[self.SESSION_KEY][self.id] = dict()
