# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-04-10 16:28
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('domain', '0053_examexpiration'),
    ]

    operations = [
        migrations.AddField(
            model_name='scheduledexam',
            name='expiration_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]