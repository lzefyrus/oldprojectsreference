# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-08-14 15:21
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('domain', '0106_auto_20170728_2004'),
    ]

    operations = [
        migrations.AddField(
            model_name='medicalprescription',
            name='period_info',
            field=models.TextField(blank=True, null=True),
        ),
    ]
