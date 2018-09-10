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

            archived_statuses = (MedicalPrescription.NOT_REGISTERED_EXAMS_FOUND,
                                 MedicalPrescription.UNREADABLE_PICTURES,
                                 MedicalPrescription.PICTURES_ID_SELFIE_DONT_MATCH,
                                 MedicalPrescription.REQUEST_EXPIRED)

            # Insert prescriptions:
            prescriptions = MedicalPrescription.objects.filter(status__in=archived_statuses)
            db.child('archived').remove()

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
                    "status": instance.status
                }

                db.child('archived').child(instance.pk).set(fb_data)

            # Insert scheduled exams:
            archived_statuses = (ScheduledExam.PATIENT_CANCELED_BY_CALL,
                                 ScheduledExam.LAB_RECORD_CANCELED,
                                 ScheduledExam.RESULTS_RECEIVED,
                                 ScheduledExam.NOT_ELIGIBLE_PATIENT_DUE_TO_AGE_OR_GENDER,
                                 ScheduledExam.PROCEDURES_NOT_COVERED
                                 )

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
                    "status": instance.status
                }

                db.child('archived').child(instance.prescription.pk).set(fb_data)

            print("Import successfully done!")
        except Exception as e:
            print("Unable to sync with firebase from signals ('archived'): {0}".format(e))
