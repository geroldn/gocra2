# Generated by Django 3.0.8 on 2020-09-01 14:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wgocra', '0022_auto_20200901_1453'),
    ]

    operations = [
        migrations.AlterField(
            model_name='player',
            name='admin_for',
            field=models.ManyToManyField(null=True, related_name='admin', to='wgocra.Club'),
        ),
        migrations.AlterField(
            model_name='player',
            name='club',
            field=models.ManyToManyField(null=True, to='wgocra.Club'),
        ),
    ]
