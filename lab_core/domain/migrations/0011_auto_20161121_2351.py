# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-11-21 23:51
from __future__ import unicode_literals

from django.db import migrations, models

import domain.utils


class Migration(migrations.Migration):

    dependencies = [
        ('domain', '0010_auto_20161121_1747'),
    ]

    operations = [
        migrations.RenameField(
            model_name='patient',
            old_name='picture_id',
            new_name='picture_id_front',
        ),
        migrations.AddField(
            model_name='patient',
            name='picture_id_back',
            field=models.ImageField(blank=True, null=True, upload_to=domain.utils.user_data_path),
        ),
    ]