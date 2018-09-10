from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from domain.models import ScheduledExam
from domain.tasks import send_push_notification
from domain.utils import grouped_exams_by_lab_date_keygen


class Command(BaseCommand):
    help = "Resend notifications for exams scheduled from Feb, 1"

    @transaction.atomic
    def handle(self, *args, **options):
        scheduled_exams = ScheduledExam.objects.filter(
            status=ScheduledExam.EXAM_TIME_SCHEDULED,
            scheduled_time__year=2018,
            scheduled_time__gte__month=3
        )
        for instance in scheduled_exams:
            print(instance)
            first_name = instance.prescription.patient.full_name.split(" ")[0]
            exam_name = instance.exam.name
            expiration_date = instance.prescription.expiration_date

            subject, message, data = "", "", None
            scheduled_time = instance.scheduled_time
            if not scheduled_time:
                print('Scheduled time is null')
                return

            data = {"scheduled_exam_id": instance.id, "status": ScheduledExam.EXAM_TIME_SCHEDULED,
                    "scheduled_time": int(scheduled_time.timestamp()),  "exam_description": instance.exam.description,
                    "is_scheduled_by_phone": instance.exam.is_scheduled_by_phone, "user_first_name": first_name}

            # if start_preparation_in_hours:
            # preparation_eta = scheduled_time - timedelta(hours=start_preparation_in_hours) - timedelta(minutes=settings.NOTIFICATION_BEFORE_EXAM_PREPARATION_IN_MINUTES)
            preparation_eta = scheduled_time - timedelta(days=settings.NOTIFICATION_BEFORE_EXAM_PREPARATION_IN_DAYS)
            preparation_eta = preparation_eta.replace(
                hour=settings.NOTIFICATION_EXACT_TIME_HOURS,
                minute=0,
                second=0,
                microsecond=0
            )

            preparation_future_subject = "Hora de começar a se preparar"
            preparation_future_message = "{0}, você precisa se preparar para seu exame. Vamos ver as instruções?".format(first_name)

            send_push_notification.apply_async(
                args=[instance.prescription.patient.token, preparation_future_subject, preparation_future_message, data],
                eta=preparation_eta,
            )

            eta = scheduled_time - timedelta(minutes=settings.NOTIFICATION_BEFORE_EXAM_IN_MINUTES)
            future_subject = "Você fez o preparo para o exame?"
            future_message = "{0}, toque para confirmar o preparo, ou para avisar que não pôde fazê-lo.".format(first_name)

            send_push_notification.apply_async(
                args=[instance.prescription.patient.token, future_subject, future_message, data],
                eta=eta,
            )

            if expiration_date:
                days = settings.NOTIFICATION_BEFORE_PRESCRIPTION_EXPIRES_IN_DAYS
                expiration_eta = expiration_date - timedelta(days=days)
                expiration_future_subject = "Seu pedido expira em {0} dias".format(days)
                expiration_future_message = "O pedido do exame {0} expira em {1} não esqueça de pedir para Sara fazer o agendamento.".format(
                    exam_name,
                    expiration_date.strftime('%d %B, %Y')
                )
                send_push_notification.apply_async(
                    args=[instance.prescription.patient.token, expiration_future_subject, expiration_future_message, data],
                    eta=expiration_eta,
                )

            subject = "Seu exame foi agendado"
            message = "{0}, toque para ver detalhes do exame.".format(first_name)
            if data:
                data.update({
                    "exam_description": instance.exam.description,
                    "is_scheduled_by_phone": instance.exam.is_scheduled_by_phone,
                    "user_first_name": first_name
                })


            send_push_notification.apply_async(args=[instance.prescription.patient.token, subject, message, data], )
            print('sent: {}'.format(instance.prescription.patient.full_name))
