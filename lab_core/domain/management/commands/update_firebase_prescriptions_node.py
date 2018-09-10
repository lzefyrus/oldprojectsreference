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

            # Insert prescriptions:
            prescriptions = MedicalPrescription.objects.filter(status=MedicalPrescription.PATIENT_REQUESTED)
            db.child('prescriptions').remove()

            for instance in prescriptions:
                insurance_company_name = "Não definido"

                if instance.insurance_company:
                    insurance_company_name = instance.insurance_company.name

                selfie = None
                if bool(instance.patient.selfie_uploadcare) or bool(instance.patient.selfie):
                    try:
                        selfie = instance.patient.selfie_uploadcare.url
                    except (AttributeError, ValueError):
                        selfie = instance.patient.selfie.url

                fb_data = {
                    "avatar": selfie,
                    "insurancePlan": insurance_company_name,
                    "key": instance.pk,
                    "name": instance.patient.full_name,
                    "prefferedLabs": [str(lab) for lab in instance.patient.preferred_laboratories.all()],
                    "createdAt": int(instance.created.timestamp()),
                }

                db.child('prescriptions').child(instance.pk).set(fb_data)

            print("Import successfully done!")
        except Exception as e:
            print("Unable to sync with firebase from signals ('prescriptions'): {0}".format(e))
