
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from domain.models import ScheduledExam
from domain.utils import grouped_exams_by_lab_date_keygen


class Command(BaseCommand):
    help = "Update group without scheduled time in '/preregister' firebase node"

    @transaction.atomic
    def handle(self, *args, **options):
        try:

            import pyrebase
            firebase = pyrebase.initialize_app(settings.FB_CONFIG)
            db = firebase.database()

            scheduled_exams = ScheduledExam.objects.filter(status=ScheduledExam.EXAM_TIME_SCHEDULED)
            for instance in scheduled_exams:
                exam_scheduled_time = instance.scheduled_time
                group_key = grouped_exams_by_lab_date_keygen(instance)
                existing_data = db.child('preregister').child(group_key).get().val()
                if existing_data and exam_scheduled_time:
                    exam_scheduled_timestamp = int(exam_scheduled_time.timestamp())
                    current_scheduled_time = db.child('preregister').child(group_key).child('scheduledTime').get().val()
                    if not current_scheduled_time or exam_scheduled_timestamp < current_scheduled_time:
                        db.child('preregister').child(group_key).child('scheduledTime').set(exam_scheduled_timestamp)

        except Exception as e:
            print("Unable to sync with firebase from signals ('preregister'): {0}".format(e))