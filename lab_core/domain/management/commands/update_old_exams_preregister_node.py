# encode: utf-8

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from domain.models import ScheduledExam
from domain.utils import grouped_exams_by_lab_date_keygen


class Command(BaseCommand):
    help = "Update old prescriptions to group representation in '/preregister' firebase node"

    @transaction.atomic
    def handle(self, *args, **options):
        try:

            import pyrebase
            firebase = pyrebase.initialize_app(settings.FB_CONFIG)
            db = firebase.database()

            scheduled_exams = ScheduledExam.objects.filter(status=ScheduledExam.EXAM_TIME_SCHEDULED)
            insurance_company_name = "Não definido"
            for instance in scheduled_exams:

                if instance.prescription.insurance_company:
                    insurance_company_name = instance.prescription.insurance_company.name

                selfie = None
                if bool(instance.prescription.patient.selfie_uploadcare) or bool(instance.prescription.patient.selfie):
                    try:
                        selfie = instance.prescription.patient.selfie_uploadcare.url
                    except (AttributeError, ValueError):
                        selfie = instance.prescription.patient.selfie.url

                group_key = grouped_exams_by_lab_date_keygen(instance)

                fb_root = 'preregister'
                #
                current_data = db.child(fb_root).child(group_key).get().val()
                if not current_data:
                    current_data = {}

                new_ids = current_data.get('examIds', [])

                fb_data = {
                    "avatar": selfie,
                    "insurancePlan": insurance_company_name,
                    "key": group_key,
                    "name": instance.prescription.patient.full_name,
                    "prefferedLabs": [str(lab) for lab in instance.prescription.patient.preferred_laboratories.all()],
                    "patientId": instance.prescription.patient.user.id,
                    "prescriptionId": instance.prescription.id,
                    'examsIds': []
                }
                exam_scheduled_time = int(instance.scheduled_time.timestamp()) if instance.scheduled_time else None
                lab_name = instance.laboratory.description if instance.laboratory else settings.NOT_FOUND

                fb_data.update({"labName": lab_name})
                if exam_scheduled_time:
                    fb_data.update({
                        "scheduledTime": exam_scheduled_time
                    })

                db.child(fb_root).child(instance.pk).remove()
                if not current_data:
                    db.child(fb_root).child(group_key).set(fb_data)
                if instance.pk not in new_ids:
                    new_ids.append(instance.pk)
                db.child(fb_root).child(group_key).child('examIds').set(new_ids)
            print("Update successfully done!")
        except Exception as e:
            print("Unable to sync with firebase from signals ('preregister'): {0}".format(e))