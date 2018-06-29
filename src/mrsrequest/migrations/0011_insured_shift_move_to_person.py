# Generated by Django 2.0.5 on 2018-06-29 05:58

from decimal import Decimal
import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mrsrequest', '0010_decimal_digits'),
        ('person', '0002_insured_shift_move_to_person'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='mrsrequest',
            name='insured_shift',
        ),
        migrations.AlterField(
            model_name='mrsrequest',
            name='expense',
            field=models.DecimalField(decimal_places=2, default=0, help_text='Somme totale des frais de péage et/ou de transport en commun (en € TTC)', max_digits=6, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))], verbose_name='Frais de péage et/ou transports'),
        ),
    ]
