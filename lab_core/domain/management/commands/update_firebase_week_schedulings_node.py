# encode: utf-8
import datetime

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from domain.models import ScheduledExam
from domain.utils import create_week_scheduling


class Command(BaseCommand):
    help = "Clear and update '/week_schedulings' firebase node"

    @transaction.atomic
    def handle(self, *args, **options):
        try:

            import pyrebase
            firebase = pyrebase.initialize_app(settings.FB_CONFIG)
            db = firebase.database()

            db.child('week_schedulings').remove()

            exams = ScheduledExam.objects.filter(
                scheduled_time__gte=datetime.date(year=2017, month=10, day=1),
                status__in=(ScheduledExam.EXAM_TIME_SCHEDULED, ScheduledExam.LAB_RECORD_OPEN))

            for exam in exams:
                create_week_scheduling(exam)

        except Exception as e:
            print(e)