# Generated by Django 3.0.8 on 2020-08-04 19:28

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wgocra', '0005_auto_20200804_1405'),
    ]

    operations = [
        migrations.RenameField(
            model_name='series',
            old_name='SeriesIsOpen',
            new_name='seriesIsOpen',
        ),
        migrations.RenameField(
            model_name='series',
            old_name='TakeCurrentRoundInAccount',
            new_name='takeCurrentRoundInAccount',
        ),
    ]
