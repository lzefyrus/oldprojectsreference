# encode: utf-8

import datetime
import logging
import traceback
from datetime import timedelta

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from domain.models import Exam, MedicalPrescription, ScheduledExam, ScheduledExamPhoneCall
from domain.tasks import send_push_notification
from domain import utils

from reporting.utils import status_history

log = logging.getLogger(__name__)


@receiver(post_save, sender=MedicalPrescription)
@status_history()
def prescription_notifications(sender, instance, created, **kwargs):
    """
    Sends a push notification when MedicalPrescription status is updated.
    :param sender:
    :param instance:
    :param created:
    :param kwargs:
    :return:
    """
    print("prescription_notifications: {} {} {}".format(sender, instance, created))

    if created:
        return

    print('PRESCRIPTION SIGNAL {}=={}'.format(instance.status, instance._MedicalPrescription__original_status))

    if instance.status == instance._MedicalPrescription__original_status:
        print('No status change')
        return

    try:
        scheduled_exams = [exam for exam in [piece.scheduled_exams.all() for piece in instance.pieces.all()]]

        if instance.status in MedicalPrescription.CANCEL_STATUS \
                or (instance.status == MedicalPrescription.NOT_REGISTERED_EXAMS_FOUND and not scheduled_exams):

            first_name = instance.patient.full_name.split(" ")[0]

            print ('{} - {}'.format(instance.status, first_name))

            content = utils.get_notification_data(instance.status, first_name)
            data = {"prescription_id": instance.id, "status": instance.status}
            data = {}

            print('{} : {} : {} : {}'.format(instance.patient.token,
                                    content["subject"],
                                    content["message"],
                                    data))


            send_push_notification.apply_async(args=[instance.patient.token,
                                                     content["subject"],
                                                     content["message"],
                                                     data],)


    except Exception as e:
        traceback.print_tb(e.__traceback__)
        log.error("Unable to send push notification from signals MedicalPrescription %s" % (instance.pk))


@receiver(post_save, sender=ScheduledExam)
@status_history()
def schedule_exam_notifications(sender, instance, created, **kwargs):
    """
    Schedules a push notification message when ScheduledExam status is updated.
    :param sender:
    :param instance:
    :param created:
    :param kwargs:
    :return:
    """
    print('schedule_exam_notifications')
    print(instance.status)
    if created:
        print('CREATED')
        if instance.status != ScheduledExam.EXAM_TIME_SCHEDULED:
            return

    if instance.status == instance._ScheduledExam__original_status \
            and instance.status != ScheduledExam.RESULTS_DELAYED and not created:  # Notification sent even if status didn't change
        print("No status change")
        return

    first_name = instance.prescription.patient.full_name.split(" ")[0]
    exam_name = instance.exam.name
    expiration_date = instance.prescription.expiration_date

    subject, message, data = "", "", None

    # TODO: Refactor this method to use utils.get_notification_data method
    if instance.status == ScheduledExam.PHONE_CALL_NOT_ANSWERED:
        subject = "Tentamos entrar em contato"
        message = "{0}, tentamos entrar em contato, mas não conseguimos contatá-lo(a). Vamos reagendar a ligação?".format(
            first_name
        )
        data = {"scheduled_exam_id": instance.id, "status": ScheduledExam.PHONE_CALL_NOT_ANSWERED}

    elif instance.status in (ScheduledExam.PATIENT_CANCELED, ScheduledExam.PATIENT_CANCELED_BY_CALL):
        subject = "Seu exame foi desmarcado"
        message = "{0}, o exame {1} foi desmarcado conforme solicitado. Você pode agendar uma nova data se quiser.".format(
            first_name, exam_name
        )
        data = {"scheduled_exam_id": instance.id, "status": ScheduledExam.PATIENT_CANCELED}

    elif instance.status == ScheduledExam.EXAM_TIME_SCHEDULED:
        scheduled_time = instance.scheduled_time
        # start_preparation_in_hours = getattr(instance.exam.preparationstep_set
        #                                      .order_by('-start_preparation_in_hours')
        #                                      .first(),
        #                                      'start_preparation_in_hours', None)

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
        if preparation_eta.date() == datetime.datetime.now().date():
            print('SAME DAY')
            preparation_eta = datetime.datetime.now() + timedelta(minutes=5)


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

    elif instance.status == ScheduledExam.LAB_RECORD_CANCELED:
        subject = "Seu exame foi desmarcado"
        message = "{0}, houve algum problema e o seu exame {1} foi desmarcado. Toque para ver mais informações.	".format(
            first_name,
            exam_name
        )
        data = {"scheduled_exam_id": instance.id, "status": ScheduledExam.LAB_RECORD_CANCELED}

    elif instance.status == ScheduledExam.EXAM_MISSED:
        subject = "Precisamos reagendar o exame"
        message = "{0}, vi que você não compareceu ao laboratório. Vamos reagendar o exame?".format(
            first_name
        )
        data = {"scheduled_exam_id": instance.id, "status": ScheduledExam.EXAM_MISSED}

    elif instance.status == ScheduledExam.PROCEDURES_EXECUTED:
        subject = "Exames realizados"
        message = "Pronto, {0}! Eu te aviso assim que os resultados estiverem disponíveis.".format(
            first_name
        )
        data = {"scheduled_exam_id": instance.id, "status": ScheduledExam.PROCEDURES_EXECUTED}

    elif instance.status == ScheduledExam.RESULTS_DELAYED:
        if instance.results_expected_at == instance._ScheduledExam__original_results_expected_at:
            return

        subject = "O resultado de seu exame sofrerá um breve atraso"
        message = "Seu exame de {0} terá a entrega de resultado levemente atrasada.".format(exam_name)

        results_expected_at = None
        if instance.results_expected_at:
            results_expected_at = datetime.datetime.combine(instance.results_expected_at, datetime.datetime.min.time())
            results_expected_at = int(results_expected_at.timestamp())

        data = {"scheduled_exam_id": instance.id, "status": ScheduledExam.RESULTS_DELAYED,
                "results_expected_at": results_expected_at}

    elif instance.status == ScheduledExam.RESULTS_RECEIVED:
        if instance.exam.exam_type == Exam.AC:
            subject = "O resultado de seu exame chegou"
            message = "{0}, você pode consultar o resultado agora mesmo, pelo aplicativo.".format(first_name)

        data = {"scheduled_exam_id": instance.id, "status": ScheduledExam.RESULTS_RECEIVED}

    elif instance.status == ScheduledExam.LAB_RECORD_OPEN:
        if instance.exam.exam_type == Exam.RDI:
            results_expected_eta = datetime.datetime.combine(
                instance.results_expected_at,
                datetime.datetime.min.time()
            ).replace(hour=settings.NOTIFICATION_EXACT_TIME_HOURS)

            results_expected_subject = "O resultado de seu exame está pronto"
            results_expected_message = "{0}, o resultado de seu exame já está disponível para retirada no laboratório.".format(first_name)
            print(results_expected_eta)
            send_push_notification.apply_async(
                args=[instance.prescription.patient.token, results_expected_subject, results_expected_message, data],
                eta=results_expected_eta,
            )
    else:
        # No notification for another statuses
        return

    if data:
        data.update({
            "exam_description": instance.exam.description,
            "is_scheduled_by_phone": instance.exam.is_scheduled_by_phone,
            "user_first_name": first_name
        })

    # print(data)

    send_push_notification.apply_async(args=[instance.prescription.patient.token, subject, message, data], )


@receiver(post_save, sender=ScheduledExamPhoneCall)
def on_save_scheduled_phone_call(sender, instance, created, **kwargs):
    """
    Sets corresponding ScheduledExam status to "PHONE_CALL_SCHEDULED" and send a Push Notification
    :param sender:
    :param instance:
    :param created:
    :param kwargs:
    :return:
    """
    try:
        # If just canceled the call, do nothing:
        if not instance._ScheduledExamPhoneCall__original_is_canceled and instance.is_canceled:
            return

        # Using update instead of save() in order to avoid infinity loop on signals:
        ScheduledExam.objects.filter(pk=instance.scheduled_exam.id).update(status=ScheduledExam.PHONE_CALL_SCHEDULED)
        #
        # subject = "Você vai receber uma ligação em breve"
        # message = "Sua ligação para agendamento de exame acontecerá em breve."
        # # eta = instance.call_time - timedelta(minutes=settings.NOTIFICATION_BEFORE_CALL_IN_MINUTES)
        # eta = instance.call_time - timedelta(minutes=2)
        # first_name = instance.scheduled_exam.prescription.patient.full_name.split(" ")[0]
        #
        # data = {
        #     "scheduled_exam_id": instance.scheduled_exam.id,
        #     "status": ScheduledExam.PHONE_CALL_SCHEDULED,
        #     "scheduled_call_time": int(instance.call_time.timestamp()),
        #     "exam_description": instance.scheduled_exam.exam.description,
        #     "first_name": first_name
        # }
        #
        # send_push_notification.apply_async(
        #     args=[instance.scheduled_exam.prescription.patient.token, subject, message, data],
        #     eta=eta,
        # )

    except Exception as e:
        traceback.print_tb(e.__traceback__)
        log.error("Unable to update ScheduledExam status from signals scheduled_phone_call %s" % (instance.pk))