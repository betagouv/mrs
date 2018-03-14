# Generated by Django 2.0.2 on 2018-03-14 17:55

import caisse.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('caisse', '0002_initial_data'),
    ]

    operations = [
        migrations.AlterField(
            model_name='caisse',
            name='number',
            field=models.CharField(max_length=3, validators=[caisse.models.validate_caisse_number], verbose_name='numéro'),
        ),
    ]
