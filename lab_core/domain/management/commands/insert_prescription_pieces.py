# encode: utf-8

from django.core.management.base import BaseCommand
from django.db import transaction

from domain.models import MedicalPrescription, PrescriptionPiece


class Command(BaseCommand):
    help = 'Insert PrescriptionPiece objects for old Prescriptions'

    @transaction.atomic
    def handle(self, *args, **options):
        try:
            with transaction.atomic():

                for prescription in MedicalPrescription.objects.all():

                    if prescription.pieces.exists():
                        print('Skipping, prescription already has piece(s)')
                        continue

                    piece = PrescriptionPiece(
                        prescription=prescription,
                        picture=prescription.picture_prescription_uploadcare or prescription.picture_prescription,
                        annotations=prescription.annotations,
                        doctor_crm=prescription.doctor_crm,
                        exams_not_registered=prescription.exams_not_registered,
                        expiration_date=prescription.expiration_date,
                        prescription_issued_at=prescription.prescription_issued_at
                    )
                    piece.save()
                    print('New piece inserted: {0}'.format(piece))

        except Exception as e:
            print("Rolling back, an Exception occurred: {0}".format(e))
