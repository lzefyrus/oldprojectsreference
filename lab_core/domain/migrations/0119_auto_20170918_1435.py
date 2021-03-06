# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-09-18 14:35
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('domain', '0118_auto_20170915_1603'),
    ]

    operations = [
        migrations.AlterField(
            model_name='rejectionreason',
            name='status',
            field=models.CharField(choices=[('REJECTED_PIECE_NO_STAMP', 'Carimbo não está visível'), ('REJECTED_PIECE_NO_CRM', 'CRM não está visível'), ('REJECTED_PIECE_NO_SIGNATURE', 'Assinatura não está visível'), ('REJECTED_PIECE_CROPPED', 'A imagem está cortada'), ('REJECTED_PIECE_BAD_CALLIGRAPHY', 'Escrita ilegível'), ('REJECTED_PIECE_ERASURE', 'Apresenta rasuras'), ('REJECTED_PIECE_MULTIPLE_COLORS', 'Mais de uma cor de caneta'), ('REJECTED_PIECE_NOT_IN_INSURANCE_RULES', 'Fora das regras do convênio'), ('REJECTED_PIECE_NOT_A_PRESCRIPTION', 'Não é uma prescrição'), ('REJECTED_PIECE_UNREADABLE_IMAGE', 'Imagem ilegível'), ('REJECTED_PRESCRIPTION_PICTURES_ID_SELFIE_DONT_MATCH', 'Pessoa da selfie difere do documento'), ('REJECTED_PRESCRIPTION_INVALID_HEALTH_CARD_PIC', 'Fotos inválidas da carteirinha'), ('REJECTED_PRESCRIPTION_INVALID_ID_PIC', 'Fotos inválidas do documento'), ('REJECTED_PRESCRIPTION_NOT_A_PRESCRIPTION_PACKAGE', 'Não há um pedido médico no envio'), ('REJECTED_REQUEST_EXPIRED', 'Prescrição expirou')], db_index=True, default='REJECTED_PIECE_NO_STAMP', max_length=150),
        ),
    ]
