# Generated by Django 2.0 on 2017-12-14 18:40

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('mrsrequest', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Bill',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('filename', models.CharField(max_length=255)),
                ('creation_datetime', models.DateTimeField(auto_now_add=True, verbose_name="Heure d'enregistrement du fichier")),
                ('binary', models.BinaryField(verbose_name='Justificatif de Transport')),
            ],
            options={
                'verbose_name': 'Justificatif',
                'ordering': ['transport', 'id'],
            },
        ),
        migrations.CreateModel(
            name='Transport',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_depart', models.DateField(null=True, verbose_name="Date d'aller")),
                ('date_return', models.DateField(null=True, verbose_name='Date de retour')),
                ('distance', models.IntegerField(null=True, verbose_name='Kilométrage total parcouru')),
                ('expense', models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=6, verbose_name='Montant total des frais (parking et/ ou péage)')),
                ('mrsrequest', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='mrsrequest.MRSRequest')),
            ],
            options={
                'ordering': ['mrsrequest'],
            },
        ),
        migrations.AddField(
            model_name='bill',
            name='transport',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='transport.Transport'),
        ),
    ]
