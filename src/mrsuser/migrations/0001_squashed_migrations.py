import django.contrib.auth.models
import django.contrib.auth.validators
from django.db import migrations, models
import django.utils.timezone
import mrsuser.models


def provision_profile(apps, schema_editor):
    User = apps.get_model('mrsuser', 'User')
    User.objects.filter(
        is_staff=True,
        is_superuser=False
    ).update(profile='upn')
    User.objects.filter(is_superuser=True).update(profile='admin')


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


def add_superviseur(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.get_or_create(name='Superviseur')


def provision_user_number(apps, schema_editor):
    User = apps.get_model('mrsuser', 'User')
    for user in User.objects.all():
        if '_' not in user.username:
            continue

        user.number = user.username.split('_')[-1]
        user.save()


class Migration(migrations.Migration):

    replaces = [('mrsuser', '0001_initial'), ('mrsuser', '0002_user_caisses'), ('mrsuser', '0003_meta'), ('mrsuser', '0004_user_profile'), ('mrsuser', '0005_nonschematic_options'), ('mrsuser', '0006_add_is_superuser'), ('mrsuser', '0007_superviseur'), ('mrsuser', '0008_user_number')]

    initial = True

    dependencies = [
        ('auth', '0009_alter_user_last_name_max_length'),
        ('caisse', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username')),
                ('first_name', models.CharField(blank=True, max_length=30, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='email address')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.Group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.Permission', verbose_name='user permissions')),
                ('caisses', models.ManyToManyField(null=True, to='caisse.Caisse')),
                ('profile', models.CharField(choices=[('admin', 'Admin'), ('upn', 'UPN'), ('stat', 'Stat'), ('support', 'Relation client')], max_length=50, verbose_name='profil')),
                ('number', models.CharField(max_length=30, null=True, verbose_name="Numéro d'agent")),
            ],
            options={
                'db_table': 'auth_user',
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
            },
            managers=[
                ('objects', mrsuser.models.UserManager()),
            ],
        ),
        migrations.RunPython(provision_profile),
        migrations.RemoveField(
            model_name='user',
            name='is_staff',
        ),
        migrations.RunPython(profile_to_groups),
        migrations.RemoveField(
            model_name='user',
            name='profile',
        ),
        migrations.RunPython(add_superviseur),
        migrations.RunPython(provision_user_number),
    ]
