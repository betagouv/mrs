import uuid

from django.db import models


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
    creation_datetime = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Date et heure d\'enregistrement du formulaire')

    insured = models.ForeignKey(
        'person.Person',
        null=True,
        on_delete=models.SET_NULL,
    )

    status = models.IntegerField(
        choices=STATUS_CHOICES,
        default=0,
    )

    objects = MRSRequestManager()

    def is_allowed(self, request):
        return str(self.id) in request.session.get(self.SESSION_KEY, {})

    def allow(self, request):
        if self.SESSION_KEY not in request.session:
            request.session[self.SESSION_KEY] = {}
        request.session[self.SESSION_KEY][str(self.id)] = dict()

        # The above doesn't use the request.session setter, won't automatically
        # trigger session save unless we do the following
        request.session.modified = True
