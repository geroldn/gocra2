# Generated by Django 3.0.8 on 2020-08-10 09:15

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('wgocra', '0006_auto_20200804_1928'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='participant',
            name='name',
        ),
        migrations.AddField(
            model_name='participant',
            name='player',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='wgocra.Player'),
        ),
    ]
