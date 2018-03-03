# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-07-01 13:09
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Orders', '0008_listallorders_listordersdone_listordersheretotake_listordersreadytocheck_listordersreadytopay'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderslist',
            name='confirmed_time',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='orderslist',
            name='done_time',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='orderslist',
            name='here_to_take_time',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='orderslist',
            name='ready_to_check_time',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='orderslist',
            name='ready_to_pay_time',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
