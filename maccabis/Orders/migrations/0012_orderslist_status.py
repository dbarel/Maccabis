# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-08-19 08:24
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Orders', '0011_listordersconfirmed'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderslist',
            name='status',
            field=models.CharField(choices=[('0', 'added'), ('1', 'confirmed'), ('2', 'hereToTake'), ('3', 'readyToCheck'), ('4', 'readyToPay'), ('5', 'done')], default='0', max_length=1),
        ),
    ]
