# Generated by Django 2.0.5 on 2018-06-23 13:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dm', '0002_auto_20180623_1501'),
    ]

    operations = [
        migrations.AlterField(
            model_name='otreeinstance',
            name='otree_production',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
