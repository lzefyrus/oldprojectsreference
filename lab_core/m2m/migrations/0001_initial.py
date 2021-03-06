# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2018-01-03 12:55
from __future__ import unicode_literals

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion
import django_extensions.db.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('domain', '0129_auto_20171222_1259'),
    ]

    operations = [
        migrations.CreateModel(
            name='ZendeskTicket',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('external_id', models.CharField(blank=True, db_index=True, max_length=50, null=True)),
                ('content', django.contrib.postgres.fields.jsonb.JSONField()),
                ('prescription', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='domain.MedicalPrescription')),
            ],
            options={
                'ordering': ['external_id'],
            },
        ),
    ]
