# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-04-27 19:32
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('domain', '0067_auto_20170427_1908'),
    ]

    operations = [
        migrations.AlterField(
            model_name='patient',
            name='hash',
            field=models.CharField(blank=True, max_length=32, null=True, unique=True),
        ),
    ]
