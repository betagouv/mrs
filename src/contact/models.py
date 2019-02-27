from django.db import models


class Contact(models.Model):
    SUBJECT_CHOICES = (
        (None, '---------'),
        ('request_error', "J'ai fait une erreur de saisie dans mon dossier"),
        ('request_question', "J'ai une question sur mon dossier"),
        ('website_question', "J'ai une idée d'amélioration pour votre site"),
        ('other', 'Autre sujet'),
    )

    subject = models.CharField(
        verbose_name='motif',
        choices=SUBJECT_CHOICES,
        max_length=25,
        db_index=True,
    )
    caisse = models.ForeignKey(
        'caisse.Caisse',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    name = models.CharField(
        max_length=255,
        verbose_name='nom',
    )
    email = models.EmailField()
    message = models.TextField()
    mrsrequest = models.ForeignKey(
        'mrsrequest.MRSRequest',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    creation_datetime = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f'Contact par {self.name}'

    class Meta:
        ordering = ('-creation_datetime',)
