# Generated by Django 2.0.7 on 2018-07-25 22:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('om', '0002_auto_20180725_1031'),
    ]

    operations = [
        migrations.AddField(
            model_name='otreeinstance',
            name='otree_room_name',
            field=models.CharField(blank=True, max_length=200),
        ),
    ]
