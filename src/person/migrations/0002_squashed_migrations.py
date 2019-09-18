import datetime
import django.core.validators
from django.db import migrations, models
import person.models


def insured_shift(apps, schema_editor):
    Person = apps.get_model('person', 'Person')
    for p in Person.objects.all():
        for m in p.mrsrequest_set.all():
            if m.insured_shift:
                p.shifted = True
                p.save()
                break

        if p.shifted:
            for m in p.mrsrequest_set.all():
                m.save()


class Migration(migrations.Migration):

    replaces = [('person', '0002_insured_shift_move_to_person'), ('person', '0003_fix_y2k'), ('person', '0004_auto_20181029_1134'),
                ('person', '0005_person_use_email'), ('person', '0006_person_confirms'), ('person', '0007_nir_charfield'),
                ('person', '0008_conflicts_counter_rewrite'), ('person', '0009_remove_conflicts_counters')
                ]

    dependencies = [
        ('person', '0001_initial'),
        ('mrsrequest', '0010_decimal_digits'),
    ]

    operations = [
        migrations.AddField(
            model_name='person',
            name='shifted',
            field=models.NullBooleanField(default=None, verbose_name='Assuré a basculé'),
        ),
        migrations.RunPython(insured_shift),
        migrations.AlterField(
            model_name='person',
            name='birth_date',
            field=models.DateField(null=True, validators=[django.core.validators.MinValueValidator(datetime.date(1900, 1, 1))], verbose_name='Date de naissance'),
        ),
        migrations.AlterField(
            model_name='person',
            name='nir',
            field=models.CharField(max_length=13, validators=[person.models.nir_validate_alphanumeric, django.core.validators.MinLengthValidator(13)], verbose_name='Numéro de sécurité sociale'),
        ),
        migrations.AddField(
            model_name='person',
            name='use_email',
            field=models.BooleanField(blank=True, default=False, null=True, verbose_name="L'assuré autorise à utiliser son email."),
        ),
    ]
