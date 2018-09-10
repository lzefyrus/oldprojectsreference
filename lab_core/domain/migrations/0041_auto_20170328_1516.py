# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-03-28 15:16
from __future__ import unicode_literals

from django.db import migrations, models
import domain.utils


class Migration(migrations.Migration):

    dependencies = [
        ('domain', '0040_examresult'),
    ]

    operations = [
        migrations.AlterField(
            model_name='examresult',
            name='picture',
            field=models.ImageField(blank=True, null=True, upload_to=domain.utils.exam_result_path),
        ),
    ]