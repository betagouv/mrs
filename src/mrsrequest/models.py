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


class MRSRequest(models.Model):
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

    def is_allowed(self, request):
        return self.id in request.session.get('MRSRequest.ids', {})

    def allow(self, request):
        if 'MRSRequest.ids' not in request.session:
            request.session['MRSRequest.ids'] = {}
        request.session['MRSRequest.ids'][self.id] = dict()
