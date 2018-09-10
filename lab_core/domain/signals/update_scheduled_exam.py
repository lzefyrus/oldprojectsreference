# encode: utf-8

import logging
import traceback

from django.db.models.signals import post_save
from django.dispatch import receiver

from domain.models import ScheduledExam


log = logging.getLogger(__name__)


@receiver(post_save, sender=ScheduledExam)
def remove_scheduled_exam_from_group(sender, instance, created, **kwargs):
    """
    Automatically removes the scheduled exam from its group when exam time is scheduled or canceled by call:
    :param sender:
    :param instance:
    :param created:
    :param kwargs:
    :return:
    """
    if instance._ScheduledExam__original_status == instance.status:
        return

    if instance.status != ScheduledExam.EXAM_TIME_SCHEDULED:
        return

    try:
        # Using update instead of save() in order to avoid infinity loop on signals:
        ScheduledExam.objects.filter(pk=instance.pk).update(is_grouped=False)

    except Exception as e:
        traceback.print_tb(e.__traceback__)
        log.error("Unable to remove ScheduledExam from group %s - %s" % (instance.pk, instance.status))
