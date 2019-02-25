from django.db import models


class Rating(models.Model):
    mrsrequest = models.ForeignKey(
        'mrsrequest.MRSRequest',
        on_delete=models.CASCADE
    )
    score = models.SmallIntegerField()
    comment = models.TextField(
        verbose_name='Commentaire',
    )
    creation_datetime = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-creation_datetime']
