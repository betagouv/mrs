import datetime
import os
import re
from decimal import Decimal
from django.conf import settings
import django.contrib.postgres.fields.jsonb
import django.core.serializers.json
import django.core.validators
from django.db import migrations, models, transaction
from django.db.models import signals
import django.db.models.deletion
import django.utils.timezone
import mrsrequest.models
from mrsstat.models import stat_update
import secrets

FORMAT_EN = '%Y-%m-%d'
FORMAT_FR = '%d/%m/%Y'


def fix_y2k(apps, schema_editor):
    Transport = apps.get_model('mrsrequest', 'Transport')
    transports = Transport.objects.filter(
        models.Q(date_depart__year__lt=100) | models.Q(date_return__year__lt=100),
        mrsrequest__status__gte=1000,
    ).select_related('mrsrequest')

    for t in transports:
        if t.date_depart.year < 100:
            print(t.mrsrequest.display_id, 'old date depart', t.date_depart)
            t.date_depart = datetime.date(
                year=t.date_depart.year + 2000,
                month=t.date_depart.month,
                day=t.date_depart.day,
            )
            print(t.mrsrequest.display_id, 'new date depart', t.date_depart)

        if t.date_return.year < 100:
            print(t.mrsrequest.display_id, 'old date return', t.date_return)
            t.date_return = datetime.date(
                year=t.date_return.year + 2000,
                month=t.date_return.month,
                day=t.date_return.day,
            )
            print(t.mrsrequest.display_id, 'new date return', t.date_return)

        t.save()


def admin_to_mrs_logentries(apps, schema_editor):
    MRSRequest = apps.get_model('mrsrequest', 'MRSRequest')
    MRSRequestLogEntry = apps.get_model('mrsrequest', 'MRSRequestLogEntry')
    LogEntry = apps.get_model('admin', 'LogEntry')
    ContentType = apps.get_model('contenttypes', 'ContentType')
    c = ContentType.objects.get_for_model(MRSRequest)
    existing = [
        str(i)
        for i in MRSRequest.objects.values_list('pk', flat=True)
    ]

    for l in LogEntry.objects.filter(content_type=c):
        if l.object_id not in existing:
            continue

        MRSRequestLogEntry.objects.create(
            mrsrequest_id=l.object_id,
            user=l.user,
            action=l.action_flag,
            datetime=l.action_time,
            comment=l.change_message,
        )


def provision(apps, schema_editor):
    if 'postgres' not in settings.DATABASES['default']['ENGINE']:
        print('Not postgres -> no JSON field')
        return
    MRSRequest = apps.get_model('mrsrequest', 'MRSRequest')
    for m in MRSRequest.objects.all():
        if not m.insured:
            continue

        m.data = {
            i: getattr(m.insured, i) for i in (
                'first_name',
                'last_name',
                'nir',
                'email',
                'birth_date',
            )
        }
        m.save()


def initial_distancevp(apps, schema_editor):
    MRSRequest = apps.get_model('mrsrequest', 'MRSRequest')
    for m in MRSRequest.objects.all():
        m.data['distancevp'] = m.distancevp
        m.save()


def convert_date(date):
    if date is None:
        return date

    try:
        # skip dates already in the right format (like after a downgrade).
        datetime.strptime(date, FORMAT_FR)
    except ValueError:
        pass
    else:
        return date

    return datetime.strptime(date, FORMAT_EN).strftime(FORMAT_FR)


def change_birth_date_format(apps, schema_editor):
    """
    From birth_date yyy-mm-dd to dd/mm/yyyy.
    """
    MRSRequest = apps.get_model('mrsrequest', 'MRSRequest')
    MRSRequestLogEntry = apps.get_model('mrsrequest', 'MRSRequestLogEntry')

    if 'sqlite' in settings.DATABASES['default']['ENGINE']:
        return  # this migration only works on pg

    requests = MRSRequest.objects.all()
    if len(requests):
        print('--- found: {} requests'.format(len(requests)))

    # request.data = an object with one birth_date
    for request in requests:
        if 'birth_date' not in request.data:
            continue

        new = convert_date(request.data['birth_date'])
        if new == request.data['birth_date']:
            continue

        request.data['birth_date'] = new
        request.save()

    logentries = MRSRequestLogEntry.objects.exclude(
        data__changed__birth_date=None
    )
    print(f'Found {len(logentries)} LogEntries to patch')
    # logentries.data.changed = dict with a list of birth_date
    for entry in logentries:
        if entry.data and 'birth_date' in entry.data.get('changed', {}):
            dates = entry.data['changed']['birth_date']
            for i, date in enumerate(dates):
                new = convert_date(date)
                if new == date:
                    continue

                dates[i] = new

        entry.save()


def provision_emailtemplate(apps, schema_editor):
    EmailTemplate = apps.get_model('mrsemail', 'EmailTemplate')
    MRSRequestLogEntry = apps.get_model('mrsrequest', 'MRSRequestLogEntry')

    templates = {
        et.subject.replace(
            '{{ display_id }}',
            '\d+',
        ).replace(
            '******** A renseigner ********',
            '.*',
        ): et for et in EmailTemplate.objects.all()
    }

    for logentry in MRSRequestLogEntry.objects.exclude(data=None):
        title = logentry.data.get('subject', None)

        if title is None:
            continue

        for subject, template in templates.items():
            if re.match(subject, title):
                logentry.emailtemplate = template
                logentry.save()
                break


class Migration(migrations.Migration):

    replaces = [('mrsrequest', '0011_insured_shift_move_to_person'), ('mrsrequest', '0012_mrsrequest_insured_shift'), ('mrsrequest', '0013_fix_y2k'), ('mrsrequest', '0014_mrsrequestlogentry'), ('mrsrequest', '0015_migrate_logentries'), ('mrsrequest', '0016_instance_data'), ('mrsrequest', '0017_expense_rename_expensevp'), ('mrsrequest', '0018_distance_rename_distancevp'), ('mrsrequest', '0019_add_bill_mode'), ('mrsrequest', '0020_add_billatp'), ('mrsrequest', '0021_save_modes'), ('mrsrequest', '0022_drop_mrsrequest_reject_template_relation'), ('mrsrequest', '0023_mrsrequest_modevp_default_false'), ('mrsrequest', '0024_nonschematic_options'), ('mrsrequest', '0025_initial_data_distancevp'), ('mrsrequest', '0026_rename_mandate_date_mandate_datevp'), ('mrsrequest', '0027_add_mrsrequest_mandate_dateatp'), ('mrsrequest', '0028_initial_data_distancevp'), ('mrsrequest', '0029_convert_birth_dates_to_fr_format'), ('mrsrequest', '0030_add_mrsrequest_confirms'), ('mrsrequest', '0031_null_expense_fields'), ('mrsrequest', '0032_remove_mrsrequest_creation_ip'), ('mrsrequest', '0033_conflicts_counter_rewrite'), ('mrsrequest', '0034_mrsrequest_token'), ('mrsrequest', '0035_cancel_mrsrequest'), ('mrsrequest', '0036_multiple_pmts'), ('mrsrequest', '0037_add_mrsrequest_suspended'), ('mrsrequest', '0038_add_mrsrequest_pel'), ('mrsrequest', '0039_mrsrequestlogentry_email_template'), ('mrsrequest', '0040_expensevp_toll_parking')]

    dependencies = [
        ('mrsrequest', '0010_decimal_digits'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('mrsemail', '0005_counter'),
        ('person', '0002_insured_shift_move_to_person'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='mrsrequest',
            name='insured_shift',
        ),
        migrations.RenameField(
            model_name='mrsrequest',
            old_name='expense',
            new_name='expensevp',
        ),
        migrations.AlterField(
            model_name='mrsrequest',
            name='expensevp',
            field=models.DecimalField(decimal_places=2, default=0, help_text='Somme totale des frais de péage et/ou de transport en commun (en € TTC)', max_digits=6, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))], verbose_name='Frais de péage et/ou transports'),
        ),
        migrations.AddField(
            model_name='mrsrequest',
            name='insured_shift',
            field=models.NullBooleanField(default=None, verbose_name='Assuré a basculé sur cette demande'),
        ),
        migrations.RunPython(fix_y2k),
        migrations.RenameField(
            model_name='mrsrequest',
            old_name='mandate_date',
            new_name='mandate_datevp',
        ),
        migrations.AlterField(
            model_name='mrsrequest',
            name='mandate_datevp',
            field=models.DateField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(datetime.date(2000, 1, 1))], verbose_name='Date de mandatement'),
        ),
        migrations.AlterField(
            model_name='transport',
            name='date_depart',
            field=models.DateField(help_text='Date du trajet aller', null=True, validators=[django.core.validators.MinValueValidator(datetime.date(2000, 1, 1)), mrsrequest.models.transport_date_validate], verbose_name='Aller'),
        ),
        migrations.AlterField(
            model_name='transport',
            name='date_return',
            field=models.DateField(help_text='Date du trajet retour', null=True, validators=[django.core.validators.MinValueValidator(datetime.date(2000, 1, 1)), mrsrequest.models.transport_date_validate], verbose_name='Retour'),
        ),
        migrations.AddField(
            model_name='mrsrequest',
            name='data',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, encoder=django.core.serializers.json.DjangoJSONEncoder, null=True, verbose_name="Formulaire tel que soumit par l'usager"),
        ),
        migrations.RunPython(provision),
        migrations.RenameField(
            model_name='mrsrequest',
            old_name='distance',
            new_name='distancevp',
        ),
        migrations.CreateModel(
            name='BillVP',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
            },
            bases=('mrsrequest.bill',),
        ),
        migrations.AddField(
            model_name='bill',
            name='mode',
            field=models.CharField(choices=[('vp', 'Vehicule Personnel'), ('atp', 'Transports en commun')], db_index=True, default='vp', max_length=3),
        ),
        migrations.CreateModel(
            name='BillATP',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
            },
            bases=('mrsrequest.bill',),
        ),
        migrations.AlterField(
            model_name='mrsrequest',
            name='distancevp',
            field=models.PositiveIntegerField(help_text='Total des kilomètres parcourus: en cas de transports aller retour, ou de transports itératifs indiquer le nombre total de km parcours. (ex.pour 2 trajets de 40 km, indiquer 80 km)', null=True, verbose_name='Distance (km)'),
        ),
        migrations.RemoveField(
            model_name='mrsrequest',
            name='reject_template',
        ),
        migrations.AddField(
            model_name='mrsrequest',
            name='modevp',
            field=models.BooleanField(blank=True, default=False, help_text='(Voiture, moto)', verbose_name='Avez vous voyagé en véhicule personnel ?'),
        ),
        migrations.AlterField(
            model_name='mrsrequest',
            name='distancevp',
            field=models.PositiveIntegerField(blank=True, help_text='Total des kilomètres parcourus: en cas de transports aller retour, ou de transports itératifs indiquer le nombre total de km parcours. (ex.pour 2 trajets de 40 km, indiquer 80 km)', null=True, verbose_name='Distance (km)'),
        ),
        migrations.AddField(
            model_name='mrsrequest',
            name='expenseatp',
            field=models.DecimalField(blank=True, decimal_places=2, default=0, help_text='Somme totale des frais de transport en commun (en € TTC)', max_digits=6, null=True, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))], verbose_name='Frais de transports'),
        ),
        migrations.AlterField(
            model_name='mrsrequest',
            name='expensevp',
            field=models.DecimalField(blank=True, decimal_places=2, default=0, help_text='Somme totale des frais de péage et/ou de transport en commun (en € TTC)', max_digits=6, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))], verbose_name='Frais de péage et/ou transports'),
        ),
        migrations.AddField(
            model_name='mrsrequest',
            name='modeatp',
            field=models.BooleanField(blank=True, default=False, help_text='(Avion, bus, métro, train, bateau…)', verbose_name='Avez vous voyagé en transports en commun ?'),
        ),
        migrations.AddField(
            model_name='mrsrequest',
            name='mandate_dateatp',
            field=models.DateField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(datetime.date(2000, 1, 1))], verbose_name='Date de mandatement ATP'),
        ),
        migrations.AlterField(
            model_name='mrsrequest',
            name='mandate_datevp',
            field=models.DateField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(datetime.date(2000, 1, 1))], verbose_name='Date de mandatement VP'),
        ),
        migrations.AlterField(
            model_name='mrsrequest',
            name='saving',
            field=models.DecimalField(decimal_places=2, editable=False, max_digits=8, null=True, verbose_name='économie'),
        ),
        migrations.AlterField(
            model_name='mrsrequest',
            name='expensevp',
            field=models.DecimalField(blank=True, decimal_places=2, default=0, help_text='Somme totale des frais de péage et/ou de transport en commun (en € TTC)', max_digits=6, null=True, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))], verbose_name='Frais de péage et/ou transports'),
        ),
        migrations.RemoveField(
            model_name='mrsrequest',
            name='creation_ip',
        ),
        migrations.AddField(
            model_name='mrsrequest',
            name='conflicts_accepted',
            field=models.PositiveIntegerField(default=0, help_text='Nombre de signalements acceptés pour cette demande', verbose_name='Nb. signalements acceptés'),
        ),
        migrations.AddField(
            model_name='mrsrequest',
            name='conflicts_resolved',
            field=models.PositiveIntegerField(default=0, help_text='Nombre de signalements résolus avant soumission', verbose_name='Nb. signalements résolus'),
        ),
        migrations.AddField(
            model_name='mrsrequest',
            name='token',
            field=models.CharField(default=secrets.token_urlsafe, editable=False, max_length=255, null=True, verbose_name="Token d'authentification pour modifier la demande"),
        ),
        migrations.AlterField(
            model_name='mrsrequest',
            name='status',
            field=models.IntegerField(choices=[(1, 'Soumise'), (100, 'Annulée'), (999, 'Rejetée'), (1000, 'En cours de liquidation'), (2000, 'Validée')], default=1, verbose_name='Statut'),
        ),
        migrations.AlterField(
            model_name='pmt',
            name='mrsrequest',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='mrsrequest.MRSRequest'),
        ),
        migrations.AddField(
            model_name='mrsrequest',
            name='suspended',
            field=models.BooleanField(blank=True, db_index=True, default=False),
        ),
        migrations.AlterField(
            model_name='mrsrequest',
            name='status',
            field=models.IntegerField(choices=[(1, 'Soumise'), (100, 'Annulée'), (600, 'Suspendue'), (999, 'Rejetée'), (1000, 'En cours de liquidation'), (2000, 'Validée')], default=1, verbose_name='Statut'),
        ),
        migrations.AddField(
            model_name='mrsrequest',
            name='pel',
            field=models.CharField(blank=True, max_length=14, null=True, validators=[django.core.validators.RegexValidator('[a-zA-Z0-9]{14}', message='Le numéro de PMET doit comporter 14 caractères alpha numériques')], verbose_name='Numéro de PMET'),
        ),
        migrations.AlterField(
            model_name='mrsrequest',
            name='institution',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='institution.Institution', verbose_name='Établissement'),
        ),
        migrations.AlterField(
            model_name='mrsrequest',
            name='status',
            field=models.IntegerField(choices=[(1, 'Soumise'), (100, 'Annulée'), (999, 'Rejetée'), (1000, 'En cours de liquidation'), (2000, 'Validée')], default=1, verbose_name='Statut'),
        ),
        migrations.CreateModel(
            name='MRSRequestLogEntry',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('datetime', models.DateTimeField(default=django.utils.timezone.now, editable=False, verbose_name='Date et heure')),
                ('comment', models.TextField(blank=True, verbose_name='Commentaire')),
                ('data', django.contrib.postgres.fields.jsonb.JSONField(blank=True, encoder=django.core.serializers.json.DjangoJSONEncoder, null=True)),
                ('action', models.SmallIntegerField(choices=[(1, 'Soumise'), (2, 'Modifiée'), (3, 'Effacée'), (100, 'Annulée'), (900, 'Suspendue'), (999, 'Rejetée'), (1000, 'En cours de liquidation'), (2000, 'Validée'), (800, 'Contacté')])),
                ('mrsrequest', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='logentries', to='mrsrequest.MRSRequest')),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Utilisateur')),
                ('emailtemplate', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='mrsemail.EmailTemplate')),
            ],
            options={
                'ordering': ('-datetime',),
                'verbose_name': 'Historique',
                'verbose_name_plural': 'Historique',
            },
        ),
        migrations.RunPython(admin_to_mrs_logentries),
        migrations.AddField(
            model_name='mrsrequest',
            name='expensevp_parking',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Somme totale des frais de stationnement (en € TTC)', max_digits=6, null=True, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))], verbose_name='Frais de stationnement'),
        ),
        migrations.AddField(
            model_name='mrsrequest',
            name='expensevp_toll',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Somme totale des frais de péage (en € TTC)', max_digits=6, null=True, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))], verbose_name='Frais de péage'),
        ),
        migrations.AlterField(
            model_name='mrsrequest',
            name='expensevp',
            field=models.DecimalField(blank=True, decimal_places=2, editable=False, help_text='Somme des frais de péage et stationnement (en € TTC)', max_digits=6, null=True, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))], verbose_name='Total des frais'),
        ),
        migrations.RunPython(initial_distancevp),
        migrations.RunPython(
            change_birth_date_format,
            lambda apps, schema_editor: True  # allow migration reveres
        ),
        migrations.RunPython(provision_emailtemplate),
    ]
