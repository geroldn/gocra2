# Generated by Django 3.0.8 on 2020-09-02 19:31

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('wgocra', '0024_auto_20200901_1457'),
    ]

    operations = [
        migrations.AddField(
            model_name='series',
            name='club',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='wgocra.Club'),
        ),
    ]
