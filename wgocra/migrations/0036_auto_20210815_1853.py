# Generated by Django 3.0.8 on 2021-08-15 18:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wgocra', '0035_auto_20210815_1211'),
    ]

    operations = [
        migrations.AddField(
            model_name='rating',
            name='old_rank',
            field=models.CharField(max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='rating',
            name='rank',
            field=models.CharField(max_length=10, null=True),
        ),
    ]
