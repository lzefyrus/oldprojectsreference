# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-05-09 15:26
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('domain', '0076_medicalprescription_exams_not_registered'),
    ]

    operations = [
        migrations.AlterField(
            model_name='medicalprescription',
            name='status',
            field=models.CharField(choices=[('PATIENT_REQUESTED', 'Paciente submeteu pedido'), ('EXAMS_IDENTIFIED', 'Exames identificados'), ('UNREADABLE_PICTURES', 'Imagem da prescrição está ilegível'), ('EXAMS_ANALYZED', 'Exames analizados para aprovação/reprovação'), ('REQUEST_EXPIRED', 'Prescrição expirou'), ('PICTURES_ID_SELFIE_DONT_MATCH', 'Imagens do documento e selfie não são correspondentes')], default='PATIENT_REQUESTED', max_length=150),
        ),
        migrations.AlterField(
            model_name='scheduledexam',
            name='status',
            field=models.CharField(choices=[('EXAM_IDENTIFIED', 'Exame identificado'), ('ELIGIBLE_PATIENT', 'Paciente elegível'), ('NOT_ELIGIBLE_PATIENT_DUE_TO_AGE_OR_GENDER', 'Paciente não elegível por questão de idade ou sexo'), ('PROCEDURES_NOT_COVERED', 'Exame não cobertos pelo Plano ou laboratório não executa o exame'), ('ALTERNATIVE_LAB_GIVEN', 'Laboratórios alternativos sugeridos'), ('EXAM_TIME_SCHEDULED', 'Paciente agendou horário para o exame'), ('PATIENT_CANCELED', 'Paciente Cancelou'), ('EXAM_MISSED', 'Exame estava agendado mas o paciente não compareceu'), ('LAB_RECORD_OPEN', 'Pré Cadastro criado no laboratório'), ('PROCEDURES_EXECUTED', 'Procedimento executado'), ('LAB_RECORD_CANCELED', 'Ficha no laboratório cancelada'), ('RESULTS_RECEIVED', 'Resultado do exame está pronto')], default='EXAM_IDENTIFIED', max_length=150),
        ),
    ]
