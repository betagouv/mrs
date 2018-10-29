# Generated by Django 2.1 on 2018-11-05 21:55

from django.db import migrations, models
import mrsuser.models


def profile_to_groups(apps, schema_editor):
    User = apps.get_model('mrsuser', 'User')
    Group = apps.get_model('auth', 'Group')
    groups = dict(
        admin=Group.objects.get_or_create(name='Admin')[0],
        upn=Group.objects.get_or_create(name='UPN')[0],
        stat=Group.objects.get_or_create(name='Stat')[0],
        support=Group.objects.get_or_create(name='Support')[0],
    )
    for u in User.objects.all():
        if not u.profile:
            continue

        if u.profile == 'admin':
            u.is_superuser = True
            u.save()
            continue

        if u.profile not in groups:
            print('Unknown profile {u.profile} for {u}')
            continue
        u.groups.add(groups[u.profile])


class Migration(migrations.Migration):

    dependencies = [
        ('mrsuser', '0005_nonschematic_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='is_superuser',
            field=models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status'),
        ),
        migrations.RunPython(profile_to_groups),
        migrations.RemoveField(
            model_name='user',
            name='profile',
        ),
    ]
