# encode: utf-8

from django.core.management.base import BaseCommand
from django.db import transaction

from domain.models import ScheduledExam, PrescriptionPiece


class Command(BaseCommand):
    help = 'Attach PrescriptionPiece object to ScheduledExam'

    @transaction.atomic
    def handle(self, *args, **options):
        try:
            with transaction.atomic():

                for exam in ScheduledExam.objects.all():
                    if not exam.prescription_piece:
                        exam.prescription_piece = PrescriptionPiece.objects.filter(prescription=exam.prescription).first()
                        exam.save()
                        print("Attached Piece to ScheduledExam {0}".format(exam))

        except Exception as e:
            print("Rolling back, an Exception occurred: {0}".format(e))
