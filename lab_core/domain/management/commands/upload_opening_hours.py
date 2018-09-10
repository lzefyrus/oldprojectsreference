# encode: utf-8

import openpyxl

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand
from django.db import transaction
from domain.models import Laboratory, LaboratoryOpeningHours


class Command(BaseCommand):
    help = 'Import data into LaboratoryOpeningHours table'
    DAYS_OF_THE_WEEK = {
        "Seg": 1,
        "Ter": 2,
        "Qua": 3,
        "Qui": 4,
        "Sex": 5,
        "Sáb": 6,
        "Sab": 6,
        "Dom": 7,
        "feriado": 8
    }

    @transaction.atomic
    def handle(self, *args, **options):
        excel_document = openpyxl.load_workbook('{base_dir}/domain/files/SaraxDASAintegration_final.xlsx'
                                                .format(base_dir=settings.BASE_DIR))
        sheet = excel_document.get_sheet_by_name('Unidade-Horarios')

        with transaction.atomic():
            for row in sheet.rows:
                lab_external_id = row[1].value
                if lab_external_id in ("Unidade-Codigo", "", None):  # Skip the first line
                    print("First ou empty line, skipping...")
                    continue

                week_day = self.DAYS_OF_THE_WEEK[row[2].value]

                opens_at = row[3].value
                if opens_at:
                    opens_at = "{hour}:{minutes}".format(hour=opens_at[:2], minutes=opens_at[2:])

                closes_at = row[4].value
                if closes_at:
                    closes_at = "{hour}:{minutes}".format(hour=closes_at[:2], minutes=closes_at[2:])

                is_open = True if opens_at and closes_at else False

                try:
                    lab = Laboratory.objects.get(external_id=lab_external_id)
                except ObjectDoesNotExist:
                    print("Invalid lab {}. Skipping...".format(lab_external_id))
                    continue

                try:
                    loh = LaboratoryOpeningHours.objects.get(laboratory=lab.id, week_day=week_day)
                    loh.opens_at = opens_at
                    loh.closes_at = closes_at
                    loh.is_open = is_open
                    print("Updating existing opening hour: {0} {1}".format(lab_external_id, week_day))
                except ObjectDoesNotExist:
                    print("Creating new opening hour: {0} {1}".format(lab_external_id, week_day))
                    loh = LaboratoryOpeningHours(laboratory=lab, week_day=week_day, is_open=is_open, opens_at=opens_at,
                                                 closes_at=closes_at)
                loh.save()

        print("Import is done!")
