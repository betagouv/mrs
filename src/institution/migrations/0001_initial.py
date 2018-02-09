# Generated by Django 2.0.2 on 2018-02-09 15:00

from django.db import migrations, models
import institution.models
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Institution',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('finess', models.IntegerField(validators=[institution.models.institution_finess])),
            ],
            options={
                'ordering': ['finess'],
            },
        ),
    ]
