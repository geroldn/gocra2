# Generated by Django 3.0.8 on 2021-07-24 19:26

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('wgocra', '0030_auto_20210722_1004'),
    ]

    operations = [
        migrations.AddField(
            model_name='result',
            name='opponent_result',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='participant_result', to='wgocra.Result'),
        ),
    ]