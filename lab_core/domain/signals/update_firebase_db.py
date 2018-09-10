# encode: utf-8

import logging
import traceback

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from domain.models import (
    Exam,
    MedicalPrescription,
    ScheduledExam,
    ScheduledExamPhoneCall,
    Patient,
    PrescriptionPiece
)
from domain.tasks import populate_firebase_week_schedulings_endpoint, \
    populate_firebase_results_ac_endpoint, populate_firebase_results_rdi_endpoint, populate_firebase_calls_endpoint

from domain.utils import (
    grouped_exams_by_lab_date_keygen,
    clear_empty_firebase_node,
    create_week_scheduling,
    remove_exam_from_firebase_node
)

log = logging.getLogger(__name__)


def remove_nested_nodes_from_expired_prescription(prescription, firebase_db):
    """
    Removes all nested nodes when a prescription expires
    :param prescription:
    :param firebase_db:
    :return:
    """
    # Remove prescription nodes:
    firebase_db.child('prescriptions').child(prescription.pk).remove()
    firebase_db.child('schedules').child(prescription.pk).remove()
    firebase_db.child('calls').child(prescription.pk).remove()

    populate_firebase_week_schedulings_endpoint()


def remove_nested_nodes_from_expired_prescription_piece(prescription_piece):
    """
    Removes all nested nodes when a prescription piece expires
    :param prescription_piece:
    :return:
    """

    # Update exams status and remove firebase nodes:
    exams_to_expire = prescription_piece.scheduled_exams.all().exclude(status__in=ScheduledExam.ATTENDED_SCHEDULED_EXAMS)

    if not exams_to_expire:
        return

    exams_to_expire.update(status=ScheduledExam.EXAM_EXPIRED)

    import pyrebase
    firebase = pyrebase.initialize_app(settings.FB_CONFIG)
    db = firebase.database()

    group = grouped_exams_by_lab_date_keygen(exams_to_expire[0])

    db.child('preregister').child(group).remove()

    for i in exams_to_expire:
        create_week_scheduling(i)

@receiver(post_delete, sender=MedicalPrescription)
def delete_fb_tasks(sender, instance, **kwargs):
    """
    Remove entry from '/prescriptions', '/schedules', 'waiting_patient' and 'archived'
    Google Realtime Database (Firebase) endpoints when a Prescription is deleted

    Concierge screens: 'Prescrição', 'Elegibilidade', 'Aguardando Paciente', 'Arquivados' respectively

    :param sender:
    :param instance:
    :param kwargs:
    :return:
    """
    try:
        import pyrebase
        firebase = pyrebase.initialize_app(settings.FB_CONFIG)
        db = firebase.database()
        for root in ['prescriptions', 'schedules', 'waiting_patient', 'archived']:
            if root == 'prescriptions':
                grouped_key = grouped_exams_by_lab_date_keygen(instance)
                db.child(root).child(grouped_key).child(instance.pk).remove()
                clear_empty_firebase_node(grouped_key, root, db)
            else:db.child(root).child(instance.pk).remove()


    except Exception as e:
        traceback.print_tb(e.__traceback__)
        log.error("Unable to delete prescription from firebase MedicalPrescription: %s" % instance.pk)


@receiver(post_delete, sender=ScheduledExam)
def delete_fb_scheduled_exams_tasks(sender, instance, **kwargs):
    """
    Remove entry from '/preregister', '/canceled', 'waiting_patient' and 'archived' Google Realtime Database (Firebase)
    endpoints when a ScheduledExam is deleted

    Concierge screens: 'Abertura de Ficha', 'Cancelados', 'Aguardando Paciente' and 'Arquivados' respectively

    :param sender:
    :param instance:
    :param kwargs:
    :return:
    """
    try:
        import pyrebase
        firebase = pyrebase.initialize_app(settings.FB_CONFIG)
        db = firebase.database()
        grouped_key = grouped_exams_by_lab_date_keygen(instance)
        db.child('preregister').child(grouped_key).remove()
        clear_empty_firebase_node(grouped_key, 'preregister', db)
        db.child('canceled').child(instance.pk).remove()

        db.child('waiting_patient').child(instance.prescription.pk).child('exams').child(instance.pk).remove()
        db.child('archived').child(instance.prescription.pk).child('exams').child(instance.pk).remove()

    except Exception as e:
        traceback.print_tb(e.__traceback__)
        log.error("Unable to delete exams from firebase ScheduledExam: %s" % instance.pk)


@receiver(post_delete, sender=MedicalPrescription)
def delete_fb_phone_call_tasks_1(sender, instance, **kwargs):
    """
    Deletes entry from '/calls' Google Realtime Database (Firebase) endpoint when related MedicalPrescription is deleted

    Concierge screen: 'Ligação'

    :param sender:
    :param instance:
    :param kwargs:
    :return:
    """
    try:
        import pyrebase
        firebase = pyrebase.initialize_app(settings.FB_CONFIG)
        db = firebase.database()

        db.child('calls').child(instance.pk).remove()

    except Exception as e:
        traceback.print_tb(e.__traceback__)
        log.error("Unable to delete phone call exams from firebase MedicalPrescription: %s" % instance.pk)


@receiver(post_delete, sender=ScheduledExamPhoneCall)
def delete_fb_phone_call_tasks_2(sender, instance, **kwargs):
    """
    Updates entry from '/calls' Google Realtime Database (Firebase) endpoint when related ScheduledExamPhoneCall is deleted

    Concierge screen: 'Ligação'

    :param sender:
    :param instance:
    :param kwargs:
    :return:
    """
    try:
        import pyrebase
        from domain.models import Exam, ScheduledExam, ScheduledExamPhoneCall

        firebase = pyrebase.initialize_app(settings.FB_CONFIG)
        db = firebase.database()
        prescription = instance.scheduled_exam.prescription

        db.child('calls').child(prescription.pk).child(instance.pk).remove()

    except Exception as e:
        traceback.print_tb(e.__traceback__)
        log.error("Unable to delete phone call exams from firebase ScheduledExamPhoneCall: %s" % instance.pk)


@receiver(post_save, sender=ScheduledExam)
def sync_scheduled_exams_phone_call_to_firebase_1(sender, instance, **kwargs):
    """
    Sync '/calls' Google Realtime Database (Firebase) endpoint when the Concierge page 'Ligação' sets ScheduledExam status

    Concierge screen: 'Ligação'

    :param sender:
    :param instance:
    :param kwargs:
    :return:
    """
    try:
        if instance._ScheduledExam__original_status == instance.status:
            return

        # ObjectDoesNotExist raises if current exam has no calls
        phone_call = ScheduledExamPhoneCall.objects.get(scheduled_exam=instance.pk)

        import pyrebase
        from domain.models import Exam, ScheduledExam

        firebase = pyrebase.initialize_app(settings.FB_CONFIG)
        db = firebase.database()
        if instance.status in (ScheduledExam.PHONE_CALL_SCHEDULED, ):  # In
            populate_firebase_calls_endpoint(phone_call)

        if instance.status in (ScheduledExam.PHONE_CALL_NOT_ANSWERED, ScheduledExam.EXAM_TIME_SCHEDULED,  # Out
                               ScheduledExam.PATIENT_CANCELED_BY_CALL):
            db.child('calls').child(instance.prescription.pk).child(phone_call.pk).remove()
    except ObjectDoesNotExist:
        pass

    except Exception as e:
        traceback.print_tb(e.__traceback__)
        log.error("Unable to sync phone call exams from firebase ScheduledExam: %s" % instance.pk)


@receiver(post_save, sender=ScheduledExamPhoneCall)
def sync_scheduled_exams_phone_call_to_firebase_2(sender, instance, created, **kwargs):
    """
    Sync '/calls' Google Realtime Database (Firebase) endpoint when ScheduledExamPhoneCall is created/updated

    Concierge screen: 'Ligação'

    :param sender:
    :param instance:
    :param created:
    :param kwargs:
    :return:
    """
    try:
        import pyrebase
        from domain.models import Exam, ScheduledExam, ScheduledExamPhoneCall

        firebase = pyrebase.initialize_app(settings.FB_CONFIG)
        db = firebase.database()

        prescription = instance.scheduled_exam.prescription

        # If call was canceled, remove node:
        if not instance._ScheduledExamPhoneCall__original_is_canceled and instance.is_canceled:
            db.child('calls').child(prescription.pk).child(instance.pk).remove()
            return

        populate_firebase_calls_endpoint(instance)

    except Exception as e:
        traceback.print_tb(e.__traceback__)
        log.error("Unable to sync with firebase /calls endpoint. {0}".format(e))


@receiver(post_save, sender=MedicalPrescription)
def sync_prescription_to_firebase(sender, instance, created, **kwargs):
    """
    Sync Prescription data to Google Realtime Database (Firebase) on endpoints 'prescriptions' and 'schedules',

    Concierge screens: 'Prescrição' and 'Elegibilidade', respectively

    :param sender:
    :param instance:
    :param created:
    :param kwargs:
    :return:
    """
    try:
        # if not created and instance.status == instance._MedicalPrescription__original_status:
        #     return

        import pyrebase
        firebase = pyrebase.initialize_app(settings.FB_CONFIG)
        db = firebase.database()

        insurance_company_name = "Não definido"

        grouped_exams = grouped_exams_by_lab_date_keygen(instance)

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

        if instance.status in (
                MedicalPrescription.UNREADABLE_PICTURES,
                MedicalPrescription.PICTURES_ID_SELFIE_DONT_MATCH,
                MedicalPrescription.PACKAGE_REJECTED,
                MedicalPrescription.PATIENT_CANCELED_BY_CALL,
                MedicalPrescription.INVALID_HEALDH_CARD_PICTURE,
                MedicalPrescription.INVALID_ID_PICTURE,
                MedicalPrescription.NOT_A_PRESCRIPTION,
                MedicalPrescription.PROCEDURES_NOT_COVERED,
                MedicalPrescription.PICTURES_HEALTHCARD_ID_DONT_MATCH
        ):
            db.child('prescriptions').child(instance.pk).remove()

        elif instance.status in (MedicalPrescription.EXAMS_IDENTIFIED, MedicalPrescription.NOT_REGISTERED_EXAMS_FOUND):
            scheduled_exams = ScheduledExam.objects.filter(
                prescription_piece__prescription__pk=instance.pk,
                status=ScheduledExam.EXAM_IDENTIFIED).all()
            expiration_date = int(instance.expiration_date.timestamp()) if instance.expiration_date else None

            db.child('prescriptions').child(instance.pk).remove()
            if scheduled_exams.exists():
                fb_data.update({
                    "willExpire": True if expiration_date else False,
                    "expirationDate": expiration_date,
                    "exams": [scheduled_exam.exam.description for scheduled_exam in scheduled_exams]
                })
                db.child('schedules').child(instance.pk).set(fb_data)

        elif instance.status == MedicalPrescription.EXAMS_ANALYZED:
            db.child('schedules').child(instance.pk).remove()

        elif instance.status == MedicalPrescription.REQUEST_EXPIRED:
            remove_nested_nodes_from_expired_prescription(instance, db)

    except Exception as e:
        traceback.print_tb(e.__traceback__)
        print(e)
        log.error("Unable to sync with firebase from signals %s - %s" % (instance.pk, instance.status))


def sync_prescription_to_firebase_after_async_upload(instance, **kwargs):
    """
    Sync Prescription data to Google Realtime Database (Firebase) on endpoints 'prescriptions' only after the
    images async uploading process is done.

    This is called by the async celery task domain.tasks.create_images

    Concierge screens: 'Prescrição'

    :param instance:
    :param kwargs:
    :return:
    """
    if settings.APP_ENVIRONMENT in (settings.CI, ):
        return

    try:
        import pyrebase
        firebase = pyrebase.initialize_app(settings.FB_CONFIG)
        db = firebase.database()

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

        group_key = grouped_exams_by_lab_date_keygen(instance)

        if instance.status == MedicalPrescription.PATIENT_REQUESTED:
            db.child('prescriptions').child(group_key).child(instance.pk).set(fb_data)

    except Exception as e:
        traceback.print_tb(e.__traceback__)
        print(e)
        log.error("Unable to sync with firebase from signals %s - %s" % (instance.pk, instance.status))


@receiver(post_save, sender=ScheduledExam)
def sync_scheduled_exams_to_firebase(sender, instance, created, **kwargs):
    """
    Sync Scheduled Exams data to Google Realtime Database (Firebase) on endpoints 'preregister' and 'canceled'

    Concierge screens: 'Abertura de Ficha' and 'Cancelados', respectively

    :param sender:
    :param instance:
    :param created:
    :param kwargs:
    :return:
    """

    try:
        if not created and instance.status == instance._ScheduledExam__original_status:
            log.warning('Missed {} {} '.format(created, instance.status))
            return

        import pyrebase
        firebase = pyrebase.initialize_app(settings.FB_CONFIG)
        db = firebase.database()

        insurance_company_name = "Não definido"

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

        current_scheduled_time = db.child(fb_root).child(group_key).child('scheduledTime').get().val()
        fb_data = {
            "avatar": selfie,
            "insurancePlan": insurance_company_name,
            "key": group_key,
            "name": instance.prescription.patient.full_name,
            "prefferedLabs": [str(lab) for lab in instance.prescription.patient.preferred_laboratories.all()],
            "patientId": instance.prescription.patient.user.id,
            "prescriptionId": instance.prescription.id,
            "examsIds": [],
            "scheduledTime": current_scheduled_time if current_scheduled_time else None
        }

        current_data = db.child(fb_root).child(group_key).get().val()
        if not current_data:
            current_data = {}

        new_ids = current_data.get('examIds', [])
        log.warning(group_key)

        if instance.status == ScheduledExam.EXAM_TIME_SCHEDULED:
            fb_root = 'preregister'
            exam_scheduled_time = int(instance.scheduled_time.timestamp()) if instance.scheduled_time else None
            lab_name = instance.laboratory.description if instance.laboratory else settings.NOT_FOUND

            fb_data.update({"labName": lab_name})

            if not current_scheduled_time or exam_scheduled_time < current_scheduled_time:
                fb_data.update({
                    "scheduledTime": exam_scheduled_time
                })

            if not current_data:
                db.child(fb_root).child(group_key).set(fb_data)
            new_ids.append(instance.pk)
            db.child(fb_root).child(group_key).set(fb_data)
            db.child(fb_root).child(group_key).child('examIds').set(new_ids)

        elif instance.status == ScheduledExam.PATIENT_CANCELED:

            fb_data = {
                "avatar": selfie,
                "insurancePlan": insurance_company_name,
                "key": instance.pk,
                "name": instance.prescription.patient.full_name,
                "prefferedLabs": [str(lab) for lab in instance.prescription.patient.preferred_laboratories.all()],
                "patientId": instance.prescription.patient.user.id,
                "prescriptionId": instance.prescription.id,
            }
            # In "Cancelados" tab, only show exams that are scheduled by phone
            if not instance.exam.is_scheduled_by_phone:
                # new_ids.remove(instance.pk)
                remove_exam_from_firebase_node(db, new_ids, group_key, instance)
                log.warn('Current canceled exam is not scheduled by phone, aborting fb insertion %s - %s' % (instance.pk, instance.status))
                return
            db.child('canceled').child(instance.pk).remove()
            # new_ids.remove(instance.pk)
            remove_exam_from_firebase_node(db, new_ids, group_key, instance)
            db.child('canceled').child(instance.pk).set(fb_data)
            return
        elif instance.status == ScheduledExam.EXAM_EXPIRED:
            remove_exam_from_firebase_node(db, new_ids, group_key, instance)
            return

        else:
            log.warning('Unable to define the right root for firebase tasks %s - %s' % (instance.pk, instance.status))

            db.child('canceled').child(instance.pk).remove()
            db.child('preregister').child(group_key).remove()

            return

    except Exception as e:
        traceback.print_tb(e.__traceback__)
        log.error("Unable to sync with firebase from signals %s - %s" % (instance.pk, instance.status))


@receiver(post_save, sender=ScheduledExam)
def sync_week_schedulings_to_firebase(sender, instance, created, **kwargs):
    """
    Sync Scheduled Exams data to Google Realtime Database (Firebase) on endpoint '/week_schedulings'

    Concierge screen: 'Comparecimento'

    :param sender:
    :param instance:
    :param created:
    :param kwargs:
    :return:
    """
    try:
        if instance.status not in (
                ScheduledExam.EXAM_TIME_SCHEDULED, ScheduledExam.LAB_RECORD_OPEN,  # In
                ScheduledExam.PROCEDURES_EXECUTED, ScheduledExam.EXAM_MISSED, ScheduledExam.EXAM_EXPIRED, # Out
                ScheduledExam.PATIENT_CANCELED, ScheduledExam.LAB_RECORD_CANCELED):
            return

        create_week_scheduling(instance)

    except Exception as e:
        traceback.print_tb(e.__traceback__)
        log.error("Unable to sync with firebase from signals (populate_firebase_week_schedulings_endpoint)"
                  "ScheduledExam: %s" % (instance.pk))


@receiver(post_save, sender=ScheduledExam)
def sync_results_ac_to_firebase(sender, instance, created, **kwargs):
    """
    Sync Scheduled Exams data to Google Realtime Database (Firebase) on endpoint '/results_ac'

    Concierge screen: 'Resultados AC'

    :param sender:
    :param instance:
    :param created:
    :param kwargs:
    :return:
    """
    try:
        if instance.exam.exam_type != Exam.AC:
            return

        # Update FB when status is about results:
        if instance.status not in [ScheduledExam.PROCEDURES_EXECUTED, ScheduledExam.RESULTS_DELAYED,  # In
                                   ScheduledExam.RESULTS_RECEIVED]:  # Out
            return

        populate_firebase_results_ac_endpoint()

    except Exception as e:
        traceback.print_tb(e.__traceback__)
        log.error("Unable to sync with firebase from signals (populate_firebase_results_ac_endpoint)"
                  "ScheduledExam: %s" % (instance.pk))


@receiver(post_save, sender=ScheduledExam)
def sync_results_rdi_to_firebase(sender, instance, created, **kwargs):
    """
    Sync Scheduled Exams data to Google Realtime Database (Firebase) on endpoint '/results_rdi'

    Concierge screen: 'Resultados RDI'

    :param sender:
    :param instance:
    :param created:
    :param kwargs:
    :return:
    """
    try:
        if instance.exam.exam_type != Exam.RDI:
            return

        # Update FB when status is about results:
        if instance.status not in [ScheduledExam.PROCEDURES_EXECUTED,  ScheduledExam.RESULTS_DELAYED,  # In
                                   ScheduledExam.RESULTS_RECEIVED]:  # Out
            return

        populate_firebase_results_rdi_endpoint()

    except Exception as e:
        traceback.print_tb(e.__traceback__)
        log.error("Unable to sync with firebase from signals (populate_firebase_results_rdi_endpoint)"
                  "ScheduledExam: %s" % (instance.pk))


@receiver(post_save, sender=Exam)
def sync_exam_results_to_firebase(sender, instance, created, **kwargs):
    """
    Sync Scheduled Exams data to Google Realtime Database (Firebase) on endpoints '/results_ac' and '/results_rdi'

    Concierge screens: 'Resultados AC' and 'Resultados RDI', respectively

    :param sender:
    :param instance:
    :param created:
    :param kwargs:
    :return:
    """
    try:
        # Update FB when exam type is updated:
        if instance._Exam__original_exam_type != instance.exam_type:

            populate_firebase_results_ac_endpoint()
            populate_firebase_results_rdi_endpoint()

    except Exception as e:
        traceback.print_tb(e.__traceback__)
        log.error("Unable to sync with firebase from signals ('/results_ac' and '/results_rdi')"
                  "Exam: %s" % (instance.pk))


@receiver(post_save, sender=MedicalPrescription)
def sync_waiting_for_patient_to_firebase(sender, instance, created, **kwargs):
    """
    Sync MedicalPrescription data to Google Realtime Database (Firebase) on endpoints '/waiting_patient'

    Concierge screen: 'Aguardando paciente'

    :param sender:
    :param instance:
    :param created:
    :param kwargs:
    :return:
    """
    try:
        if created:
            return

        if instance._MedicalPrescription__original_status == instance.status:
            return

        import pyrebase
        firebase = pyrebase.initialize_app(settings.FB_CONFIG)
        db = firebase.database()

        if instance.status not in (
                MedicalPrescription.UNREADABLE_PICTURES,
                MedicalPrescription.PICTURES_ID_SELFIE_DONT_MATCH,
        ):

            db.child('waiting_patient').child(instance.pk).remove()
            return

        selfie = None
        if bool(instance.patient.selfie_uploadcare) or bool(instance.patient.selfie):
            try:
                selfie = instance.patient.selfie_uploadcare.url
            except (AttributeError, ValueError):
                selfie = instance.patient.selfie.url

        fb_data = {
            "avatar": selfie,
            "exams": [],
            "key": instance.pk,
            "modifiedAt": int(instance.modified.timestamp()),
            "name": instance.patient.full_name,
        }

        db.child('waiting_patient').child(instance.pk).set(fb_data)

    except Exception as e:
        traceback.print_tb(e.__traceback__)
        log.error("Unable to sync with firebase from signals ('waiting_patient')"
                  "MedicalPrescription: %s" % (instance.pk))


@receiver(post_save, sender=ScheduledExam)
def sync_waiting_for_patient_to_firebase_2(sender, instance, created, **kwargs):
    """
    Sync ScheduledExam data to Google Realtime Database (Firebase) on endpoints '/waiting_patient'

    Concierge screen: 'Aguardando paciente'

    :param sender:
    :param instance:
    :param created:
    :param kwargs:
    :return:
    """
    try:
        if created:
            return

        if instance._ScheduledExam__original_status == instance.status:
            return

        if instance.status != ScheduledExam.ELIGIBLE_PATIENT:
            return

        import pyrebase
        firebase = pyrebase.initialize_app(settings.FB_CONFIG)
        db = firebase.database()

        scheduled_exams = instance.prescription.scheduledexam_set.filter(status=ScheduledExam.ELIGIBLE_PATIENT)
        if not scheduled_exams:
            db.child('waiting_patient').child(instance.prescription.pk).remove()
            return

        selfie = None
        if bool(instance.prescription.patient.selfie_uploadcare) or bool(instance.prescription.patient.selfie):
            try:
                selfie = instance.prescription.patient.selfie_uploadcare.url
            except (AttributeError, ValueError):
                selfie = instance.prescription.patient.selfie.url

        fb_data = {
            "avatar": selfie,
            "exams": [scheduled_exam.exam.name for scheduled_exam in scheduled_exams],
            "key": instance.prescription.pk,
            "modifiedAt": int(instance.prescription.modified.timestamp()),
            "name": instance.prescription.patient.full_name,
        }

        db.child('waiting_patient').child(instance.prescription.pk).set(fb_data)

    except Exception as e:
        traceback.print_tb(e.__traceback__)
        log.error("Unable to sync with firebase from signals ('waiting_patient')"
                  "ScheduledExam: %s" % (instance.pk))


@receiver(post_save, sender=MedicalPrescription)
def sync_archived_to_firebase(sender, instance, created, **kwargs):
    """
    Sync MedicalPrescription data to Google Realtime Database (Firebase) on endpoints '/archived'

    Concierge screen: 'Arquivados'

    :param sender:
    :param instance:
    :param created:
    :param kwargs:
    :return:
    """
    try:
        if created:
            return

        if instance._MedicalPrescription__original_status == instance.status:
            return

        import pyrebase
        firebase = pyrebase.initialize_app(settings.FB_CONFIG)
        db = firebase.database()
        if instance.status in (MedicalPrescription.EXAMS_ANALYZED,
                               MedicalPrescription.EXAMS_IDENTIFIED):
            return
        if instance.status not in (MedicalPrescription.NOT_REGISTERED_EXAMS_FOUND,
                                   MedicalPrescription.UNREADABLE_PICTURES,
                                   MedicalPrescription.PICTURES_ID_SELFIE_DONT_MATCH,
                                   MedicalPrescription.REQUEST_EXPIRED,
                                   MedicalPrescription.PACKAGE_REJECTED,
                                   MedicalPrescription.INVALID_HEALDH_CARD_PICTURE,
                                   MedicalPrescription.INVALID_ID_PICTURE,
                                   MedicalPrescription.NOT_A_PRESCRIPTION,
                                   MedicalPrescription.PROCEDURES_NOT_COVERED,
                                   MedicalPrescription.PATIENT_CANCELED_BY_CALL,
                                   MedicalPrescription.PICTURES_HEALTHCARD_ID_DONT_MATCH):

            db.child('archived').child(instance.pk).remove()
            return

        selfie = None
        if bool(instance.patient.selfie_uploadcare) or bool(instance.patient.selfie):
            try:
                selfie = instance.patient.selfie_uploadcare.url
            except (AttributeError, ValueError):
                selfie = instance.patient.selfie.url

        fb_data = {
            "avatar": selfie,
            "exams": [],
            "key": instance.pk,
            "modifiedAt": int(instance.modified.timestamp()),
            "name": instance.patient.full_name,
            "status": instance.status
        }
        db.child('archived').child(instance.pk).set(fb_data)

    except Exception as e:
        print(e)
        traceback.print_tb(e.__traceback__)
        log.error("Unable to sync with firebase from signals ('archived')"
                  "MedicalPrescription: %s" % (instance.pk))


@receiver(post_save, sender=ScheduledExam)
def sync_archived_to_firebase_2(sender, instance, created, **kwargs):
    """
    Sync ScheduledExam data to Google Realtime Database (Firebase) on endpoints '/archived'

    Concierge screen: 'Arquivados'

    :param sender:
    :param instance:
    :param created:
    :param kwargs:
    :return:
    """
    try:
        if created:
            return

        if instance._ScheduledExam__original_status == instance.status:
            return

        import pyrebase
        firebase = pyrebase.initialize_app(settings.FB_CONFIG)
        db = firebase.database()

        archived_statuses = (ScheduledExam.PATIENT_CANCELED_BY_CALL,
                             ScheduledExam.LAB_RECORD_CANCELED,
                             ScheduledExam.RESULTS_RECEIVED,
                             ScheduledExam.NOT_ELIGIBLE_PATIENT_DUE_TO_AGE_OR_GENDER,
                             ScheduledExam.PROCEDURES_NOT_COVERED,
                             ScheduledExam.PHONE_CALL_NOT_ANSWERED,
                             ScheduledExam.EXAM_MISSED
                             )
        if instance.status not in archived_statuses:
            return
        scheduled_exams = instance.prescription.scheduledexam_set.filter(status__in=archived_statuses)
        if not scheduled_exams:
            rejected_pieces = instance.prescription.pieces.filter(
                status__in=(
                    PrescriptionPiece.REQUEST_EXPIRED,
                    PrescriptionPiece.PIECE_REJECTED
                )
            )
            if rejected_pieces.exists():
                return
            db.child('archived').child(instance.prescription.pk).remove()
            return

        selfie = None
        if bool(instance.prescription.patient.selfie_uploadcare) or bool(instance.prescription.patient.selfie):
            try:
                selfie = instance.prescription.patient.selfie_uploadcare.url
            except (AttributeError, ValueError):
                selfie = instance.prescription.patient.selfie.url

        fb_data = {
            "avatar": selfie,
            "exams": [scheduled_exam.exam.name for scheduled_exam in scheduled_exams],
            "key": instance.prescription.pk,
            "modifiedAt": int(instance.prescription.modified.timestamp()),
            "name": instance.prescription.patient.full_name,
            "status": instance.status
        }

        db.child('archived').child(instance.prescription.pk).set(fb_data)

    except Exception as e:
        traceback.print_tb(e.__traceback__)
        log.error("Unable to sync with firebase from signals ('archived')"
                  "ScheduledExam: %s" % (instance.pk))


@receiver(post_save, sender=PrescriptionPiece)
def sync_archived_to_firebase_3(sender, instance, created, **kwargs):
    """
    Sync ScheduledExam data to Google Realtime Database (Firebase) on endpoints '/archived'

    Concierge screen: 'Arquivados'

    :param sender:
    :param instance:
    :param created:
    :param kwargs:
    :return:
    """
    try:
        if created:
            return

        if instance._PrescriptionPiece__original_status == instance.status:
            return

        import pyrebase
        firebase = pyrebase.initialize_app(settings.FB_CONFIG)
        db = firebase.database()

        archived_statuses = (
            PrescriptionPiece.REQUEST_EXPIRED,
            PrescriptionPiece.PIECE_REJECTED
        )

        pieces = instance.prescription.pieces.filter(status__in=archived_statuses)

        if not pieces:
            db.child('archived').child(instance.prescription.pk).remove()
            return

        selfie = None
        if bool(instance.prescription.patient.selfie_uploadcare) or bool(instance.prescription.patient.selfie):
            try:
                selfie = instance.prescription.patient.selfie_uploadcare.url
            except (AttributeError, ValueError):
                selfie = instance.prescription.patient.selfie.url

        fb_data = {
            "avatar": selfie,
            "pieces": [piece.pk for piece in pieces],
            "key": instance.prescription.pk,
            "modifiedAt": int(instance.prescription.modified.timestamp()),
            "name": instance.prescription.patient.full_name,
            "status": instance.status
        }

        db.child('archived').child(instance.prescription.pk).set(fb_data)

    except Exception as e:
        traceback.print_tb(e.__traceback__)
        log.error("Unable to sync with firebase from signals ('archived')"
                  "ScheduledExam: %s" % (instance.pk))


@receiver(post_delete, sender=Patient)
def remove_nodes_from_deleted_user(sender, instance, **kwargs):
    """
    Updates tabs 'Comparecimento', 'Resultados AC' and 'Resultados RDI' after removing a patient via Django Admin
    :return:
    """
    try:
        import pyrebase
        firebase = pyrebase.initialize_app(settings.FB_CONFIG)
        db = firebase.database()
        ws = ScheduledExam.objects.filter(
            status__in=(ScheduledExam.LAB_RECORD_OPEN, ScheduledExam.EXAM_TIME_SCHEDULED),
            prescription_piece__prescription__patient=instance
        )
        for i in ws:
            db.child('week_schedulings').child(
                str(i.laboratory_id)).child(str(i.prescription_id)).remove()
        canceled_exams = ScheduledExam.objects.filter(
            status=ScheduledExam.PATIENT_CANCELED,
            prescription_piece__prescription__patient=instance
        )
        for exam in canceled_exams:
            db.child('canceled').child(exam.pk).remove()
        populate_firebase_results_ac_endpoint()
        populate_firebase_results_rdi_endpoint()

    except Exception as e:
        traceback.print_tb(e.__traceback__)
        log.error("Unable to sync with firebase from signals (remove_nodes_from_deleted_user)"
                  "ScheduledExam: %s" % instance.pk)

