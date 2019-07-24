from django.db import migrations, models
import django.db.models.deletion
from django.core.management import call_command


def update(apps, schema_editor):
    MRSRequest = apps.get_model('mrsrequest', 'MRSRequest')
    for m in MRSRequest.objects.all():
        m.save()

    Stat = apps.get_model('mrsstat', 'Stat')
    for s in Stat.objects.all():
        s.save()

    call_command('mrsstat')


class Migration(migrations.Migration):

    replaces = [('mrsstat', '0001_initial'), ('mrsstat', '0002_labels_and_decimal_digits'), ('mrsstat', '0003_update'), ('mrsstat', '0004_change_denorm'), ('mrsstat', '0005_stat_insured_shifts'), ('mrsstat', '0006_stat_mrsrequest_count_inprogress'), ('mrsstat', '0007_totals'), ('mrsstat', '0008_conflicting_mrsrequest_counts'), ('mrsstat', '0009_add_stat_mrsrequest_count_resolved'), ('mrsstat', '0010_meta')]

    initial = True

    dependencies = [
        ('caisse', '0002_caisse_meta_option_change'),
        ('institution', '0002_unique_finess'),
    ]

    operations = [
        migrations.CreateModel(
            name='Stat',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('validation_average_delay', models.DecimalField(decimal_places=2, editable=False, max_digits=5, null=True, verbose_name='Délai moyen de paiement (en jours)')),
                ('mrsrequest_count_new', models.IntegerField(editable=False, verbose_name='Nombre de demandes soumises')),
                ('mrsrequest_count_inprogress', models.IntegerField(default=0, editable=False, verbose_name='Nombre de demandes en cours')),
                ('mrsrequest_count_validated', models.IntegerField(editable=False, verbose_name='Nombre de demandes validées')),
                ('mrsrequest_count_rejected', models.IntegerField(editable=False, verbose_name='Nombre de demandes rejettées')),
                ('savings', models.DecimalField(decimal_places=2, editable=False, max_digits=9, null=True, verbose_name='Econnomie réalisée')),
                ('caisse', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='caisse.Caisse')),
                ('institution', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='institution.Institution')),
                ('insured_shifts', models.IntegerField(default=0, editable=False, verbose_name='Nombre de bascules')),
                ('insured_shifts_total', models.IntegerField(default=0, editable=False, verbose_name='Nombre cumulé de bascules')),
                ('mrsrequest_total_inprogress', models.IntegerField(default=0, editable=False, verbose_name='Nombre cumulé de demandes en cours')),
                ('mrsrequest_total_new', models.IntegerField(default=0, editable=False, verbose_name='Nombre cumulé de demandes soumises')),
                ('mrsrequest_total_rejected', models.IntegerField(default=0, editable=False, verbose_name='Nombre cumulé de demandes rejettées')),
                ('mrsrequest_total_validated', models.IntegerField(default=0, editable=False, verbose_name='Nombre cumulé de demandes validées')),
                ('mrsrequest_count_resolved', models.IntegerField(default=0, editable=False, verbose_name='Nb. demandes en conflit resolu (non-soumise inclues)')),
                ('mrsrequest_count_conflicted', models.IntegerField(default=0, verbose_name='Nb. affichages page de confirmation')),
                ('mrsrequest_count_conflicting', models.IntegerField(default=0, verbose_name='Nb. demandes soumises avec conflit non resolu')),
            ],
            options={'ordering': ('date', 'caisse', 'institution')},
        ),
        migrations.RunPython(update),
    ]
