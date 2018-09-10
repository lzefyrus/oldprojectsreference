# encode: utf-8
import datetime
import reversion

from reversion.models import Version
from django.core.management.base import BaseCommand
from domain.models import ScheduledExam, ScheduledExamPhoneCall


class Command(BaseCommand):
    help = 'Create version 0 for old calls'

    def handle(self, *args, **options):
        exams = ScheduledExam.objects.filter(status=ScheduledExam.PHONE_CALL_SCHEDULED)
        for exam in exams:
            try:
                call = exam.scheduledexamphonecall
                versions = Version.objects.get_for_object(call)
                if not versions.exists():
                    with reversion.create_revision():
                        call.modified = datetime.datetime.now()
                        call.save()
                        reversion.set_user(exam.prescription_piece.prescription.patient.user)
                        reversion.set_comment("Sara Concierge Backoffice Call Attempt: #{}".format(0))
            except ScheduledExamPhoneCall.DoesNotExist as e:
                print(e)