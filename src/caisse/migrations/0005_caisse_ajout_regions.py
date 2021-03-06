# Generated by Django 2.1.9 on 2019-06-20 15:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('caisse', '0004_caisse_import_datetime'),
    ]

    operations = [
        migrations.CreateModel(
            name='Region',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=30, verbose_name='nom de la région')),
                ('insee_id', models.CharField(max_length=2, verbose_name='code INSEE de la région')),
                ('cheflieu_code', models.CharField(max_length=5, verbose_name='code commune INSEE du chef lieu de la région')),
            ],
        ),
        migrations.AddField(
            model_name='caisse',
            name='regions',
            field=models.ManyToManyField(to='caisse.Region'),
        ),
        migrations.AlterModelOptions(
            name='region',
            options={'ordering': ['name']},
        ),
    ]
