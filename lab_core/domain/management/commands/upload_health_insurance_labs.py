# encode: utf-8

import openpyxl

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand
from django.db import transaction
from domain.models import Laboratory, HealthInsurance


class Command(BaseCommand):
    help = 'Import data into HealthInsurance table'

    @transaction.atomic
    def handle(self, *args, **options):
        excel_document = openpyxl.load_workbook('{base_dir}/domain/files/SaraxDASAintegration_final.xlsx'
                                                .format(base_dir=settings.BASE_DIR))
        sheet = excel_document.get_sheet_by_name('Unidade-Convenio')

        with transaction.atomic():
            for row in sheet.rows:
                lab_external_id = row[1].value
                if lab_external_id in ("Unidade-Codigo", "", None):  # Skip the first line and empty ones
                    print("First ou empty line, skipping...")
                    continue

                insurance_health_external_id = row[2].value
                if not insurance_health_external_id:
                    print("Empty line for insurance_health_external_id, skipping...")
                    continue

                try:
                    lab = Laboratory.objects.get(external_id=lab_external_id)
                except ObjectDoesNotExist:
                    print("Invalid lab: {0}. Skipping...".format(lab_external_id))
                    continue

                try:
                    hi = HealthInsurance.objects.get(external_id=insurance_health_external_id)
                    hi.laboratories.add(lab)
                    print("Adding lab {0} to Health Insurance {1}.".format(lab_external_id, insurance_health_external_id))
                except ObjectDoesNotExist:
                    print("Invalid Health Insurance: {0}. Skipping...".format(insurance_health_external_id))
                    continue

        print("Import is done!")
