# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-06-27 01:58
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('domain', '0091_auto_20170627_0152'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='laboratory',
            options={},
        ),
        migrations.AlterField(
            model_name='laboratory',
            name='external_id',
            field=models.CharField(blank=True, db_index=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='laboratory',
            name='street',
            field=models.CharField(db_index=True, max_length=250),
        ),
        migrations.AlterField(
            model_name='laboratorybrand',
            name='name',
            field=models.CharField(db_index=True, max_length=70),
        ),
        migrations.AlterIndexTogether(
            name='laboratory',
            index_together=set([('is_active', 'brand'), ('is_active', 'point')]),
        ),
    ]
