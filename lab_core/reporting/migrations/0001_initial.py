# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-09-26 12:40
from __future__ import unicode_literals

import django.db.models.deletion
import django_extensions.db.fields
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('domain', '0119_auto_20170918_1435'),
    ]

    operations = [
        migrations.CreateModel(
            name='GeneralStatus',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created',
                 django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified',
                 django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('date_set', models.DateTimeField()),
                ('status', models.CharField(max_length=150)),
                ('content_type',
                 models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.ContentType')),
                ('exam',
                 models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='domain.ScheduledExam')),
                ('prescription',
                 models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='domain.MedicalPrescription')),
                ('prescription_piece', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE,
                                                         to='domain.PreparationStep')),
            ],
            options={
                'ordering': ('-modified', '-created'),
                'get_latest_by': 'modified',
                'abstract': False,
            },
        ),
    ]
