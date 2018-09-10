# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-09-28 10:06
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('reporting', '0003_auto_20170927_1119'),
    ]

    operations = [
        migrations.AlterField(
            model_name='generalstatus',
            name='exam',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='domain.ScheduledExam'),
        ),
        migrations.AlterField(
            model_name='generalstatus',
            name='parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='reporting.GeneralStatus'),
        ),
    ]