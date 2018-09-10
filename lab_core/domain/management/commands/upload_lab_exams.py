# encode: utf-8

import openpyxl

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand
from django.db import transaction
from domain.models import Exam, Laboratory


class Command(BaseCommand):
    help = 'Import data into Exam table'
    YES_NO = {
        "yes": True,
        "no": False
    }

    @transaction.atomic
    def handle(self, *args, **options):
        excel_document = openpyxl.load_workbook('{base_dir}/domain/files/SaraxDASAintegration_final.xlsx'
                                                .format(base_dir=settings.BASE_DIR))
        sheet = excel_document.get_sheet_by_name('Unidade-Exame')

        with transaction.atomic():
            for row in sheet.rows:
                lab_external_id = row[1].value
                if lab_external_id in ("Unidade-Codigo", "", None):  # Skip the first line and the empty ones
                    print("First ou empty line, skipping...")
                    continue
                exam_name = row[2].value

                try:
                    lab = Laboratory.objects.get(external_id=lab_external_id)
                except ObjectDoesNotExist:
                    print("Invalid lab: {0}. Skipping...".format(lab_external_id))
                    continue

                try:
                    exam = Exam.objects.get(name=exam_name)
                except ObjectDoesNotExist:
                    print("Invalid exam: {0}. Skipping...".format(exam_name))
                    continue

                print("Adding exam {0} to lab {1}".format(exam_name, lab_external_id))
                lab.exams.add(exam)
                lab.save()

        print("Import is done!")
