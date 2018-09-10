# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-04-26 19:46
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('domain', '0062_auto_20170424_1940'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='medicalprescription',
            name='plan_product_code',
        ),
        migrations.AddField(
            model_name='scheduledexam',
            name='plan_product_code',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]