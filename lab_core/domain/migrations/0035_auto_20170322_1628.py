# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-03-22 16:28
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('domain', '0034_auto_20170322_1532'),
    ]

    operations = [
        migrations.AlterField(
            model_name='recoverpassword',
            name='expiration_date',
            field=models.DateTimeField(default=datetime.datetime(2017, 3, 23, 16, 28, 36, 924037)),
        ),
        migrations.AlterField(
            model_name='recoverpassword',
            name='token',
            field=models.CharField(default='4466425bb5cc44c9b36b2fc1713f9098', max_length=32, unique=True),
        ),
    ]
