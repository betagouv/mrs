from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    replaces = [('institution', '0001_initial'), ('institution', '0002_unique_finess')]

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Institution',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('finess', models.IntegerField(unique=True)),
                ('origin', models.CharField(default='', help_text='URI du site patients', max_length=255)),
                ('dynamic_allow', models.BooleanField(default=False, help_text="Cocher pour les hebergeurs non-HDS qui ne veulent pas de controle d'origine", verbose_name='Autorisation CORS dynamique')),
            ],
            options={
                'verbose_name': 'Établissement',
                'ordering': ['finess'],
            },
        ),
    ]
