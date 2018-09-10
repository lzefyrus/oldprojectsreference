# encode: utf-8

import openpyxl

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand
from django.db import transaction
from domain.models import HealthInsurance, HealthInsurancePlan


class Command(BaseCommand):
    help = 'Import data into HealthInsurancePlan table'

    @transaction.atomic
    def handle(self, *args, **options):
        excel_document = openpyxl.load_workbook('{base_dir}/domain/files/SaraxDASAintegration_final.xlsx'
                                                .format(base_dir=settings.BASE_DIR))
        sheet = excel_document.get_sheet_by_name('Convenio-Plano')

        with transaction.atomic():
            for row in sheet.rows:
                health_insurance_external_id = row[1].value
                if health_insurance_external_id in ("Convenio-codigo", "", None):  # Skip the first line and empty ones
                    print("First or empty line, skipping...")
                    continue

                plan_code = row[2].value
                if not plan_code:
                    print("Empty plan code, skipping...")
                    continue

                try:
                    hi = HealthInsurance.objects.get(external_id=health_insurance_external_id)
                except ObjectDoesNotExist:
                    print("Invalid health insurance, skipping...")
                    continue

                try:
                    HealthInsurancePlan.objects.get(health_insurance=hi.id, plan_code=plan_code)
                    print("Existing health insurance plan {0}, skipping...".format(plan_code))
                    continue
                except ObjectDoesNotExist:
                    print("Creating new health insurance plan {0}".format(plan_code))
                    hip = HealthInsurancePlan(health_insurance=hi, plan_code=plan_code)
                    hip.save()

        print("Import is done!")
