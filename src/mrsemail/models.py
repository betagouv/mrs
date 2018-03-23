from django.db import models


class EmailTemplate(models.Model):
    name = models.CharField(max_length=50)
    subject = models.CharField(max_length=255)
    body = models.TextField()

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.name
