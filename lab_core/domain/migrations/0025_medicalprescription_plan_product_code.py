# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-11-28 21:58
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('domain', '0024_medicalprescription_lab_expected_time'),
    ]

    operations = [
        migrations.AddField(
            model_name='medicalprescription',
            name='plan_product_code',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]