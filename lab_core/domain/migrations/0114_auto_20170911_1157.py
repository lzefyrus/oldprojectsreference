# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-09-11 11:57
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('domain', '0113_prescriptionpiece_status'),
    ]

    operations = [
        migrations.CreateModel(
            name='RejectionReason',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('REJECTED_PIECE_NO_STAMP', 'Carimbo não está visível'), ('REJECTED_PIECE_NO_CRM', 'CRM não está visível'), ('REJECTED_PIECE_NO_SIGNATURE', 'Assinatura não está visível'), ('REJECTED_PIECE_CROPPED', 'A imagem está cortada'), ('REJECTED_PIECE_BAD_CALLIGRAPHY', 'Escrita ilegível'), ('REJECTED_PIECE_ERASURE', 'Apresenta rasuras'), ('REJECTED_PIECE_MULTIPLE_COLORS', 'Mais de uma cor de caneta'), ('REJECTED_PIECE_NOT_IN_INSURANCE_RULES', 'Fora das regras do convênio'), ('REJECTED_PIECE_NOT_A_PRESCRIPTION', 'Não é uma prescrição'), ('REJECTED_PIECE_UNREADABLE_IMAGE', 'Imagem ilegível'), ('REJECTED_PRESCRIPTION_PICTURES_ID_SELFIE_DONT_MATCH', 'Pessoa da selfie difere do documento'), ('REJECTED_PRESCRIPTION_INVALID_HEALTH_CARD_PIC', 'Fotos inválidas da carteirinha'), ('REJECTED_PRESCRIPTION_INVALID_ID_PIC', 'Fotos inválidas do documento'), ('REJECTED_PRESCRIPTION_NOT_A_PRESCRIPTION_PACKAGE', 'Não há um pedido médico no envio')], db_index=True, default='REJECTED_PIECE_NO_STAMP', max_length=150)),
                ('feedback', models.TextField()),
                ('instruction', models.TextField()),
            ],
        ),
        migrations.AlterField(
            model_name='medicalprescription',
            name='status',
            field=models.CharField(choices=[('PATIENT_REQUESTED', 'Paciente submeteu pedido'), ('EXAMS_IDENTIFIED', 'Exames identificados'), ('UNREADABLE_PICTURES', 'Imagem da prescrição está ilegível'), ('NOT_REGISTERED_EXAMS_FOUND', 'Há exame(s) não contemplado(s) pelo Sara'), ('EXAMS_ANALYZED', 'Exames analizados para aprovação/reprovação'), ('REQUEST_EXPIRED', 'Prescrição expirou'), ('PICTURES_ID_SELFIE_DONT_MATCH', 'Imagens do documento e selfie não são correspondentes'), ('PACKAGE_REJECTED', 'Prescrição rejeitada')], db_index=True, default='PATIENT_REQUESTED', max_length=150),
        ),
        migrations.AlterField(
            model_name='prescriptionpiece',
            name='status',
            field=models.CharField(choices=[('PIECE_CREATED', 'Pedaço de prescrição criado'), ('REQUEST_EXPIRED', 'Pedaço de prescrição expirou'), ('PIECE_REJECTED', 'Pedaço de prescrição rejeitada')], db_index=True, default='PIECE_CREATED', max_length=150),
        ),
        migrations.AddField(
            model_name='medicalprescription',
            name='rejection_reasons',
            field=models.ManyToManyField(blank=True, null=True, to='domain.RejectionReason'),
        ),
        migrations.AddField(
            model_name='prescriptionpiece',
            name='rejection_reasons',
            field=models.ManyToManyField(blank=True, null=True, to='domain.RejectionReason'),
        ),
    ]