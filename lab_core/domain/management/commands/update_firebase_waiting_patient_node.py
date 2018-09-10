# encode: utf-8

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from domain.models import MedicalPrescription, ScheduledExam


class Command(BaseCommand):
    help = "Update '/archived' firebase node"

    @transaction.atomic
    def handle(self, *args, **options):
        try:

            import pyrebase
            firebase = pyrebase.initialize_app(settings.FB_CONFIG)
            db = firebase.database()

            archived_statuses = (MedicalPrescription.UNREADABLE_PICTURES,
                                 MedicalPrescription.PICTURES_ID_SELFIE_DONT_MATCH)

            # Insert prescriptions:
            prescriptions = MedicalPrescription.objects.filter(status__in=archived_statuses)
            db.child('waiting_patient').remove()

            for instance in prescriptions:
                selfie = None
                if bool(instance.patient.selfie_uploadcare) or bool(instance.patient.selfie):
                    try:
                        selfie = instance.patient.selfie_uploadcare.url
                    except (AttributeError, ValueError):
                        selfie = instance.patient.selfie.url

                fb_data = {
                    "avatar": selfie,
                    "exams": [],
                    "key": instance.pk,
                    "modifiedAt": int(instance.modified.timestamp()),
                    "name": instance.patient.full_name,
                }

                db.child('waiting_patient').child(instance.pk).set(fb_data)

            # Insert scheduled exams:
            archived_statuses = (ScheduledExam.ELIGIBLE_PATIENT,
                                 ScheduledExam.PHONE_CALL_NOT_ANSWERED,
                                 ScheduledExam.EXAM_MISSED)

            scheduled_exams = ScheduledExam.objects.filter(status__in=archived_statuses)

            for instance in scheduled_exams:
                selfie = None
                if bool(instance.prescription.patient.selfie_uploadcare) or bool(instance.prescription.patient.selfie):
                    try:
                        selfie = instance.prescription.patient.selfie_uploadcare.url
                    except (AttributeError, ValueError):
                        selfie = instance.prescription.patient.selfie.url

                fb_data = {
                    "avatar": selfie,
                    "exams": [scheduled_exam.exam.name for scheduled_exam in scheduled_exams],
                    "key": instance.prescription.pk,
                    "modifiedAt": int(instance.prescription.modified.timestamp()),
                    "name": instance.prescription.patient.full_name,
                }

                db.child('waiting_patient').child(instance.prescription.pk).set(fb_data)

            print("Import successfully done!")
        except Exception as e:
            print("Unable to sync with firebase from signals ('waiting_patient'): {0}".format(e))
