from decimal import Decimal
from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import mrsrequest.models
import uuid


def status_to_logentry(apps, schema_editor):
    MRSRequest = apps.get_model('mrsrequest', 'MRSRequest')
    LogEntry = apps.get_model('admin', 'LogEntry')
    ContentType = apps.get_model('contenttypes', 'ContentType')
    c = ContentType.objects.get_for_model(MRSRequest)

    for m in MRSRequest.objects.all():
        # Update to status that is compatible with LogEntry flags
        if m.status == 0:
            m.status = 1  # NEW
        elif m.status == 1:
            m.status = 999  # REJECT
            if m.reject_template_id:
                message = m.reject_template.subject
            else:
                message = 'Rejetée'
        elif m.status == 2:
            m.status = 1000  # PROGRESS
            message = 'En cours de liquidation'
        elif m.status == 9:
            m.status = 2000  # DONE
            message = 'Validée'
        m.save()

        if m.status == 1:
            continue  # nothing left for new requests

        # Delete all LogEntries and start over from scratch
        # They should only in staging, this is supposed to be noop in
        # production
        LogEntry.objects.filter(
            content_type=c,
            object_id=m.pk,
        ).delete()

        if not m.status_datetime:
            continue  # Old requests without status_datetime

        LogEntry.objects.create(
            user=m.status_user,
            action_time=m.status_datetime,
            content_type=c,
            object_id=m.pk,
            object_repr=m.display_id,
            action_flag=m.status,
            change_message=message,
        )


class Migration(migrations.Migration):

    replaces = [('mrsrequest', '0001_initial'), ('mrsrequest', '0002_status_inprogress'), ('mrsrequest', '0003_mrsrequest_reject_template_set_null'), ('mrsrequest', '0004_mrsrequest_logentry'), ('mrsrequest', '0005_stats'), ('mrsrequest', '0006_display_id_bigint'), ('mrsrequest', '0007_status_blank'), ('mrsrequest', '0008_mrsrequest_adeli'), ('mrsrequest', '0009_delay_saving_taxi_cost'), ('mrsrequest', '0010_decimal_digits')]

    initial = True

    dependencies = [
        ('admin', '0001_initial'),
        ('institution', '0001_initial'),
        ('mrsemail', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('person', '0001_initial'),
        ('mrsattachment', '0001_initial'),
        ('caisse', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='MRSRequest',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('creation_datetime', models.DateTimeField(db_index=True, default=django.utils.timezone.now, verbose_name='Date et heure de la demande')),
                ('creation_ip', models.GenericIPAddressField(null=True)),
                ('display_id', models.BigIntegerField(unique=True, verbose_name='Numéro de demande')),
                ('status_datetime', models.DateTimeField(blank=True, db_index=True, null=True, verbose_name='Date et heure de changement de statut')),
                ('distance', models.PositiveIntegerField(help_text='Total des kilomètres parcourus', null=True, verbose_name='Distance (km)')),
                ('expense', models.DecimalField(decimal_places=2, default=0, help_text='Somme totale des frais de stationnement et/ou péage et/ou de transport en commun', max_digits=6, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))], verbose_name='Montant total des frais (en € TTC)')),
                ('status', models.IntegerField(choices=[(1, 'Soumise'), (999, 'Rejetée'), (1000, 'En cours de liquidation'), (2000, 'Validée')], default=1, verbose_name='Statut')),
                ('caisse', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='caisse.Caisse')),
                ('institution', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='institution.Institution')),
                ('insured', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='person.Person')),
                ('reject_template', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='mrsemail.EmailTemplate')),
                ('status_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='Auteur du changement de statut')),
                ('insured_shift', models.NullBooleanField(default=None, verbose_name='Assuré qui bascule')),
                ('mandate_date', models.DateField(blank=True, null=True, verbose_name='Date de mandatement')),
                ('payment_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True, verbose_name='Montant remboursé')),
                ('payment_base', models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True, verbose_name='Base de remboursement')),
                ('adeli', models.IntegerField(blank=True, null=True)),
                ('delay', models.DecimalField(decimal_places=2, editable=False, max_digits=5, null=True)),
                ('saving', models.DecimalField(decimal_places=2, editable=False, max_digits=8, null=True)),
                ('taxi_cost', models.DecimalField(decimal_places=2, editable=False, max_digits=10, null=True)),
            ],
            options={
                'verbose_name': 'Demande',
                'ordering': ['-creation_datetime'],
            },
        ),
        migrations.CreateModel(
            name='PMT',
            fields=[
                ('mrsattachment_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='mrsattachment.MRSAttachment')),
                ('mrsrequest', models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, to='mrsrequest.MRSRequest')),
            ],
            options={
                'ordering': ['mrsrequest', 'id'],
            },
            bases=('mrsattachment.mrsattachment',),
        ),
        migrations.CreateModel(
            name='Transport',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_depart', models.DateField(help_text='Date du trajet aller', null=True, validators=[mrsrequest.models.transport_date_validate], verbose_name='Aller')),
                ('date_return', models.DateField(help_text='Date du trajet retour', null=True, validators=[mrsrequest.models.transport_date_validate], verbose_name='Retour')),
                ('mrsrequest', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='mrsrequest.MRSRequest')),
            ],
            options={
                'ordering': ['mrsrequest', 'date_depart'],
            },
        ),
        migrations.CreateModel(
            name='Bill',
            fields=[
                ('mrsattachment_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='mrsattachment.MRSAttachment')),
                ('mrsrequest', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='mrsrequest.MRSRequest')),
            ],
            options={
                'verbose_name': 'Justificatif',
                'ordering': ['mrsrequest', 'id'],
            },
            bases=('mrsattachment.mrsattachment',),
        ),
        migrations.RunSQL(
            sql='update mrsrequest_mrsrequest set status=9 where status=1',
        ),
        migrations.RunSQL(
            sql='update mrsrequest_mrsrequest set status=1 where status=2',
        ),
        migrations.RunPython(status_to_logentry),
    ]
