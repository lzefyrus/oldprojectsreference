# encode: utf-8

import logging
import traceback

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from django.conf import settings
from domain.models import MedicalPrescription
from domain.signals.send_notification import prescription_notifications
from domain.tasks import zendesk_prescription
from general_utils.utils import close_zendesk_ticket
log = logging.getLogger(__name__)


@receiver(pre_save, sender=MedicalPrescription)
def update_zendesk_ticket(instance, raw, using, update_fields, **kwargs):
    """
    Update the ticket if the original status is patient_requested
    :param instance:
    :param raw:
    :param using:
    :param update_fields:
    :return:
    """
    try:
        if settings.APP_ENVIRONMENT in (settings.PROD,):
            old = MedicalPrescription.objects.get(id=instance.id)

            if old:
                print("####### {} == {} #######".format(old.status, instance.status))

            if old and old.status == MedicalPrescription.PATIENT_REQUESTED and instance.status != MedicalPrescription.PATIENT_REQUESTED:
                close_zendesk_ticket(instance)
    except Exception as e:
        print(e)

        
@receiver(post_save, sender=MedicalPrescription)
def update_prescription_status(sender, instance, created, **kwargs):
    """
    Automatically sets prescription status when a given field is updated
    :param sender:
    :param instance:
    :param created:
    :param kwargs:
    :return:
    """
    try:
        # "NOT_REGISTERED_EXAMS_FOUND" when 'exams_not_registered' field is filled
        if not instance._MedicalPrescription__original_exams_not_registered and instance.exams_not_registered:

            # Using update instead of save() in order to avoid infinity loop on signals:
            MedicalPrescription.objects.filter(pk=instance.pk).update(status=MedicalPrescription.NOT_REGISTERED_EXAMS_FOUND)
            instance.status = MedicalPrescription.NOT_REGISTERED_EXAMS_FOUND

            prescription_notifications(sender, instance, created, **kwargs)

    except Exception as e:
        traceback.print_tb(e.__traceback__)
        log.error("Unable to update Prescription status from signals %s - %s" % (instance.pk, instance.status))
