# Generated by Django 3.0.8 on 2020-08-29 07:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wgocra', '0019_participant_score'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='result',
            name='r_string',
        ),
        migrations.AddField(
            model_name='result',
            name='komi',
            field=models.FloatField(default=0.0, null=True),
        ),
    ]
