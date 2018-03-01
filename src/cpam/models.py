from django.db import models


class CPAM(models.Model):
    code = models.CharField(max_length=9)
    label = models.CharField(max_length=50)
    liquidation_email = models.EmailField()

    class Meta:
        ordering = ['code']

    def __str__(self):
        return self.label
