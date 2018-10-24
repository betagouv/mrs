# Generated by Django 2.1 on 2018-10-23 13:48

from django.db import migrations, models


def initial_counter(apps, schema_editor):
    EmailTemplate = apps.get_model('mrsemail', 'EmailTemplate')
    for et in EmailTemplate.objects.all():
        et.counter = et.mrsrequest_set.count()
        et.save()


class Migration(migrations.Migration):

    dependencies = [
        ('mrsemail', '0003_add_emailtemplate_menu'),
    ]

    operations = [
        migrations.AddField(
            model_name='emailtemplate',
            name='counter',
            field=models.IntegerField(default=0),
        ),
        migrations.RunPython(initial_counter),
    ]