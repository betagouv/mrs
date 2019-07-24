from django.db import migrations, models


def initial_counter(apps, schema_editor):
    EmailTemplate = apps.get_model('mrsemail', 'EmailTemplate')
    for et in EmailTemplate.objects.all():
        et.counter = et.mrsrequest_set.count()
        et.save()


def provision_counter(apps, schema_editor):
    EmailTemplate = apps.get_model('mrsemail', 'emailtemplate')

    reject_templates = EmailTemplate.objects.filter(
        menu='reject'
    )

    for i in reject_templates:
        i.counter = i.mrsrequest_set.count()
        i.save()


class Migration(migrations.Migration):

    replaces = [('mrsemail', '0001_initial'), ('mrsemail', '0002_labels'), ('mrsemail', '0003_add_emailtemplate_menu'), ('mrsemail', '0004_add_mrsemail_counter'), ('mrsemail', '0005_counter'), ('mrsemail', '0006_meta')]

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='EmailTemplate',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, verbose_name='Nom')),
                ('subject', models.CharField(max_length=255, verbose_name='Sujet du mail')),
                ('body', models.TextField(verbose_name='Contenu du mail')),
                ('active', models.BooleanField(default=True, verbose_name='Activé')),
                ('menu', models.CharField(choices=[('reject', 'Rejet'), ('contact', 'Contact')], db_index=True, default='reject', max_length=10)),
                ('counter', models.IntegerField(default=0)),
            ],
            options={
                'verbose_name': 'Gabarit',
                'ordering': ('name',),
            },
        ),
        migrations.RunPython(initial_counter),
        migrations.RunPython(provision_counter),
    ]
