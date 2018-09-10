# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-03-27 19:38
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('domain', '0037_auto_20170322_1651'),
    ]

    operations = [
        migrations.AlterField(
            model_name='medicalprescription',
            name='status',
            field=models.CharField(choices=[('PATIENT_REQUESTED', 'Paciente submeteu pedido'), ('EXAMS_IDENTIFIED', 'Exames identificados'), ('ELIGIBLE_LAB', 'Laboratório elegível'), ('ALTERNATIVE_LAB_GIVEN', 'Laboratórios alternativos sugeridos'), ('PROCEDURES_NOT_COVERED', 'Exames não cobertos pelo Plano'), ('EXAMS_TIME_SCHEDULED', 'Paciente agendou horário para os exames'), ('PATIENT_CANCELED', 'Paciente Cancelou'), ('LAB_RECORD_OPEN', 'Pré Cadastro criado no laboratório'), ('PROCEDURES_EXECUTED', 'Procedimentos executaods'), ('LAB_RECORD_CANCELED', 'Ficha no laboratório cancelada'), ('RESULTS_RECEIVED', 'Resultados dos exames estão prontos')], default='PATIENT_REQUESTED', max_length=35),
        ),
    ]