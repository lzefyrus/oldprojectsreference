# encode: utf-8

import openpyxl

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand
from django.db import transaction
from domain.models import HealthInsurance


class Command(BaseCommand):
    help = 'Import data into HealthInsurance table'

    @transaction.atomic
    def handle(self, *args, **options):
        excel_document = openpyxl.load_workbook('{base_dir}/domain/files/SaraxDASAintegration_final.xlsx'
                                                .format(base_dir=settings.BASE_DIR))
        sheet = excel_document.get_sheet_by_name('Convenio')

        with transaction.atomic():
            for row in sheet.rows:
                external_id = row[1].value
                if external_id in ("Convenio-Codigo", "", None):  # Skip the first line and empty ones
                    print("First or empty line, skipping...")
                    continue

                health_insurance_description = row[2].value
                cnpj = row[4].value

                try:
                    hi = HealthInsurance.objects.get(external_id=external_id)
                    hi.description = health_insurance_description
                    hi.cnpj = cnpj
                    hi.save()
                    print("Updating existing health insurance: {0}".format(external_id))
                except ObjectDoesNotExist:
                    print("Creating new health insurance: {0}".format(external_id))
                    hi = HealthInsurance(external_id=external_id, description=health_insurance_description,
                                         is_active=True, cnpj=cnpj)
                    hi.save()

        print("Import is done!")
