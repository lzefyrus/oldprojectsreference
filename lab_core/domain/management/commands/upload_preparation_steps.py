# encode: utf-8

import openpyxl

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand
from django.db import transaction
from domain.models import Exam, Laboratory, LaboratoryBrand, PreparationStep


class Command(BaseCommand):
    help = 'Import data into PreparationStep table'
    exam = None
    lab_brand = None
    labs = []

    @transaction.atomic
    def handle(self, *args, **options):
        excel_document = openpyxl.load_workbook('{base_dir}/domain/files/SaraxDASAintegration_ALL_insercao_novos_exames_CAMILA.xlsx'
                                                .format(base_dir=settings.BASE_DIR))
        sheet = excel_document.get_sheet_by_name('Exame-Preparo')

        with transaction.atomic():
            lab_brand_external_id = None
            exam_name = None

            for row in sheet.rows:
                if row[0].value in("LABORATORIO_CODIGO", "", None):  # Skip the first line or empty ones
                    print("First or empty line skipped")
                    continue

                is_another_brand = row[0].value != lab_brand_external_id
                lab_brand_external_id = row[0].value

                is_another_exam = row[1].value != exam_name
                exam_name = row[1].value
                step_description = row[2].value
                step_title = row[3].value or "INFORMAÇÕES DO PREPARO"

                if not exam_name or not step_description:
                    print("Exam or step information is empty, skipping...")
                    continue

                if is_another_exam:
                    print("New Exam id found...")
                    try:
                        self.exam = Exam.objects.get(name=exam_name)
                    except ObjectDoesNotExist:
                        print("Exam does not exist on database: {0}".format(exam_name))
                        continue

                if not self.exam:
                    continue

                try:
                    if is_another_brand:
                        print("New Lab Brand found...")
                        self.lab_brand = LaboratoryBrand.objects.get(external_id=lab_brand_external_id)
                        self.labs = Laboratory.objects.filter(brand=self.lab_brand).all()

                    for lab in self.labs:
                        # Skip if there's an equal existing step:
                        if PreparationStep.objects.filter(exam=self.exam, laboratory=lab,
                                                          description=step_description).all():
                            print("Preparation Step already exist, skipping: {0} - {1} - {2}"
                                  .format(lab, self.exam, step_description))
                            continue

                        print("Adding new Preparation Step: {0}".format(lab, self.exam, step_description))
                        step = PreparationStep(laboratory=lab, exam=self.exam, description=step_description,
                                               title=step_title)
                        step.save()

                except ObjectDoesNotExist:
                    print("Lab Brand does not exist on database: {0}".format(lab_brand_external_id))
                    continue

        print("Import is done!")
