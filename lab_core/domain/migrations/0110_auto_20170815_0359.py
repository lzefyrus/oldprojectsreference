# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-08-15 03:59
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('domain', '0109_auto_20170815_0352'),
    ]

    operations = [
        migrations.AlterField(
            model_name='prescriptionpiece',
            name='prescription',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pieces', to='domain.MedicalPrescription'),
        ),
        migrations.AlterField(
            model_name='scheduledexam',
            name='prescription_piece',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='scheduled_exams', to='domain.PrescriptionPiece'),
        ),
    ]