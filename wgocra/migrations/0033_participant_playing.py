# Generated by Django 3.0.8 on 2021-07-28 15:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wgocra', '0032_auto_20210724_2006'),
    ]

    operations = [
        migrations.AddField(
            model_name='participant',
            name='playing',
            field=models.BooleanField(default=False),
        ),
    ]
