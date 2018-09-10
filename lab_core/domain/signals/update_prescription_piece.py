# encode: utf-8

import datetime
import logging
import traceback

from django.db.models.signals import post_save
from django.dispatch import receiver

from domain.models import PrescriptionPiece, MedicalPrescription, RejectionReason
from domain.signals.send_notification import prescription_notifications
from domain.signals.update_firebase_db import sync_prescription_to_firebase, \
                    remove_nested_nodes_from_expired_prescription_piece

log = logging.getLogger(__name__)


@receiver(post_save, sender=PrescriptionPiece)
def update_prescription_piece_status(sender, instance, created, **kwargs):
    """
    Automatically sets prescription piece status when a given field is updated
    :param sender:
    :param instance:
    :param created:
    :param kwargs:
    :return:
    """
    try:

        # "REQUEST_EXPIRED" when 'expiration_date' is set to older than today
        if instance._PrescriptionPiece__original_expiration_date != instance.expiration_date:
            if instance.expiration_date and instance.expiration_date.date() < datetime.date.today():
                rejected_expired_reason = RejectionReason.objects.get(
                    status=RejectionReason.REJECTED_REQUEST_EXPIRED
                )
                # Using update instead of save() in order to avoid infinity loop on signals:
                PrescriptionPiece.objects.filter(pk=instance.pk).update(status=PrescriptionPiece.REQUEST_EXPIRED)
                remove_nested_nodes_from_expired_prescription_piece(instance)

                prescription = instance.prescription
                prescription_pieces = prescription.pieces.all()
                not_expired_pieces = prescription_pieces.exclude(status=PrescriptionPiece.REQUEST_EXPIRED).count()
                if prescription_pieces.count() == 1 or (prescription_pieces.count() > 1 and not_expired_pieces == 0):
                    MedicalPrescription.objects.filter(pk=prescription.pk).update(status=MedicalPrescription.REQUEST_EXPIRED)
                    prescription.rejection_reasons.add(rejected_expired_reason)
                    prescription.status = MedicalPrescription.REQUEST_EXPIRED

                    sync_prescription_to_firebase(sender, prescription, False, **kwargs)
                    prescription_notifications(sender, prescription, False, **kwargs)

    except Exception as e:
        traceback.print_tb(e.__traceback__)
        log.error("Unable to update Prescription status from signals %s - %s" % (instance.pk, instance.status))
