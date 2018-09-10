# encode: utf-8

import openpyxl

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand
from django.db import transaction
from domain.models import Exam


class Command(BaseCommand):
    help = 'Import data into Exam table'
    YES_NO = {
        "yes": True,
        "no": False,
        "empty": False
    }

    @transaction.atomic
    def handle(self, *args, **options):
        excel_document = openpyxl.load_workbook('{base_dir}/domain/files/SaraxDASAintegration_ALL_insercao_novos_exames_CAMILA.xlsx'
                                                .format(base_dir=settings.BASE_DIR))
        sheet = excel_document.get_sheet_by_name('Exames')

        with transaction.atomic():
            for row in sheet.rows:
                name = row[0].value
                if name in ("codigo_exame", "", None):  # Skip the first line and the empty ones
                    print("First ou empty line, skipping...")
                    continue

                description = row[1].value
                exam_type = row[2].value
                is_scheduled_by_phone = row[3].value or "empty"
                is_scheduled_by_phone = self.YES_NO[is_scheduled_by_phone]

                try:
                    exam = Exam.objects.get(name=name)
                    exam.name = name
                    exam.description = description
                    exam.exam_type = exam_type
                    exam.is_scheduled_by_phone = is_scheduled_by_phone

                    print("Updating existing exam: {0}".format(name))
                except ObjectDoesNotExist:
                    exam = Exam(name=name, description=description, exam_type=exam_type,
                                is_scheduled_by_phone=is_scheduled_by_phone)
                    print("Inserting new exam: {0}".format(name))

                exam.save()

        print("Import is done!")
