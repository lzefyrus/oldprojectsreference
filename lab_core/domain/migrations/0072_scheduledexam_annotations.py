# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-05-02 06:22
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('domain', '0071_laboratorybrand_external_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='scheduledexam',
            name='annotations',
            field=models.TextField(blank=True, null=True),
        ),
    ]
