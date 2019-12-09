from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mrsrequest', '0040_expensevp_toll_parking'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='mrsrequest',
            name='mandate_dateatp',
        ),
        migrations.RenameField(
            model_name='mrsrequest',
            old_name='mandate_datevp',
            new_name='mandate_date',
        ),
    ]
