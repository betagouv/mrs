from django.db import models


class EmailTemplateManager(models.Manager):
    def active(self):
        return self.filter(active=True)


class EmailTemplate(models.Model):
    MENU_REJECT = 'reject'
    MENU_CONTACT = 'contact'
    MENU_CHOICES = (
        (MENU_REJECT, 'Rejet'),
        (MENU_CONTACT, 'Contact'),
    )

    name = models.CharField(max_length=50, verbose_name='Nom')
    subject = models.CharField(max_length=255, verbose_name='Sujet du mail')
    body = models.TextField(verbose_name='Contenu du mail')
    active = models.BooleanField(verbose_name='Activé', default=True)
    menu = models.CharField(
        choices=MENU_CHOICES,
        default=MENU_REJECT,
        db_index=True,
        max_length=10,
    )
    counter = models.IntegerField(default=0)

    objects = EmailTemplateManager()

    class Meta:
        ordering = ('name',)
        verbose_name = 'Modèle d\'email'
        verbose_name_plural = 'Modèles d\'emails'

    def __str__(self):
        return self.name
