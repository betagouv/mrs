# Generated by Django 2.0.2 on 2018-03-14 18:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('caisse', '0004_score'),
    ]

    operations = [
        migrations.AlterField(
            model_name='caisse',
            name='liquidation_email',
            field=models.EmailField(blank=True, max_length=254, null=True, verbose_name='email du service de liquidation'),
        ),
    ]
