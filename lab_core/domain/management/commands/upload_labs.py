# encode: utf-8

import openpyxl

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand
from django.db import transaction
from domain.models import Laboratory, LaboratoryBrand


class Command(BaseCommand):
    help = 'Import data into Laboratory table'

    @transaction.atomic
    def handle(self, *args, **options):
        excel_document = openpyxl.load_workbook('{base_dir}/domain/files/SaraxDASAintegration_final.xlsx'
                                                .format(base_dir=settings.BASE_DIR))
        sheet = excel_document.get_sheet_by_name('Unidade')

        with transaction.atomic():
            for row in sheet.rows:
                external_id = row[0].value
                if external_id in ("Unidade-Codigo", "", None):  # Skip the first line and the empty ones
                    print("First ou empty line, skipping...")
                    continue

                lab_brand_external_id = row[1].value
                try:
                    lab_brand = LaboratoryBrand.objects.get(external_id=lab_brand_external_id)
                except ObjectDoesNotExist:
                    print("Invalid lab brand {0}, skipping...".format(lab_brand_external_id))
                    return

                description = row[2].value
                # zip_code = row[3].value
                street = row[3].value.split(",")[0]
                street_number = row[3].value.split(",")[1]
                district = row[4].value
                city = row[5].value
                state = row[5].value
                state_abbreviation = row[6].value or "SP"
                complement = row[7].value
                country = "Brasil"
                is_active = True

                try:
                    exam = Laboratory.objects.get(external_id=external_id)
                    exam.brand = lab_brand
                    exam.description = description
                    # exam.zip_code = zip_code
                    exam.street = street
                    exam.street_number = street_number
                    exam.district = district
                    exam.city = city
                    exam.state = state
                    exam.state_abbreviation = state_abbreviation
                    exam.complement = complement
                    exam.country = country
                    exam.is_active = is_active

                    print("Updating existing lab: {0}".format(external_id))
                except ObjectDoesNotExist:
                    exam = Laboratory(external_id=external_id, description=description, street=street,
                                      district=district, city=city, state=state,
                                      state_abbreviation=state_abbreviation, complement=complement, country=country,
                                      is_active=is_active, brand=lab_brand,
                                      street_number=street_number)  # , zip_code=zip_code)
                    print("Inserting new lab: {0}".format(external_id))

                exam.save()

        print("Import is done!")
