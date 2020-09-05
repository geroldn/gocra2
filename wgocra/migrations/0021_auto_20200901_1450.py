# Generated by Django 3.0.8 on 2020-09-01 14:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wgocra', '0020_auto_20200829_0754'),
    ]

    operations = [
        migrations.AddField(
            model_name='player',
            name='admin_for',
            field=models.ManyToManyField(related_name='admin', to='wgocra.Club'),
        ),
        migrations.RemoveField(
            model_name='player',
            name='club',
        ),
        migrations.AddField(
            model_name='player',
            name='club',
            field=models.ManyToManyField(to='wgocra.Club'),
        ),
    ]