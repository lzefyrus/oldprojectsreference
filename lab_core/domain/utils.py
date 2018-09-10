# encode: utf-8

import base64
import binascii
import copy
import datetime
import logging
import pytz
import smtplib
import socket
import time
import traceback
from base64 import b64decode
from collections import namedtuple

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.hashers import check_password
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.base import ContentFile
from django.db.models.fields.files import ImageFieldFile
from django.utils.decorators import decorator_from_middleware
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.views import exception_handler
import pyrebase
import json

from reversion.models import Version
from dateutil import parser

QUERY_GENERAL = """
SELECT
  date_trunc('%s', date_set) AS txn_month,
  avg(ttl) / 86400              AS media,
  count(1) AS qtd
FROM reporting_generalstatus
WHERE "status" IN ('PACKAGE_REJECTED',
                   'REGISTERED_EXAMS_NOT_FOUND',
                   'ELIGIBLE_PATIENT',
                   'PROCEDURES_NOT_COVERED',
                   'NOT_ELIGIBLE_PATIENT_DUE_TO_AGE_OR_GENDER',
                   'UNREADABLE_IMAGES')
GROUP BY txn_month
ORDER BY txn_month;
"""

QUERY_GENERAL_WORKING_DAYS = """
SELECT
  date_trunc('%s', date_set) AS txn_month,
  avg(ttl) / 86400              AS media,
  count(1) AS qtd
FROM reporting_generalstatus
WHERE "status" IN ('PACKAGE_REJECTED',
                   'REGISTERED_EXAMS_NOT_FOUND',
                   'ELIGIBLE_PATIENT',
                   'PROCEDURES_NOT_COVERED',
                   'NOT_ELIGIBLE_PATIENT_DUE_TO_AGE_OR_GENDER',
                   'UNREADABLE_IMAGES')
      AND
        parent_id IN (SELECT id FROM reporting_generalstatus WHERE
      date_set :: TIME BETWEEN '07:00:00' :: TIME AND '18:00:00' :: TIME
      AND
      EXTRACT(DOW FROM date_set ) NOT IN (0,6))
GROUP BY txn_month
ORDER BY txn_month;
"""


class RequestLogMiddleware(object):
    request_copy = None

    def process_request(self, request):
        request.start_time = time.time()
        self.request_copy = copy.copy(request)

    def process_response(self, request, response):

        if response.get('content-type', None) == 'application/json':
            if getattr(response, 'streaming', False):
                response_body = '<<<Streaming>>>'
            else:
                response_body = response.content
        else:
            response_body = '<<<Not JSON>>>'

        try:
            user = request.user.email
        except AttributeError:
            user = "Anonymous"

        log_data = {
            'user': user,

            'remote_address': request.META['REMOTE_ADDR'],
            'server_hostname': socket.gethostname(),

            'request_method': request.method,
            'request_path': request.get_full_path(),
            'request_body': self.request_copy.body,

            'response_status': response.status_code,
            'response_body': response_body,

            'run_time': time.time() - request.start_time,
        }

        # save log_data in some way
        log = logging.getLogger("default")
        log.info(log_data)

        return response


class RequestLogViewMixin(object):
    """
    Adds RequestLogMiddleware to any Django View by overriding as_view.
    """

    @classmethod
    def as_view(cls, *args, **kwargs):
        view = super(RequestLogViewMixin, cls).as_view(*args, **kwargs)
        view = decorator_from_middleware(RequestLogMiddleware)(view)
        return view


class UserModelEmailBackend(ModelBackend):

    def authenticate(self, username="", password="", **kwargs):
        """
        :param username:
        :param password:
        :param kwargs:
        :return:
        """
        try:
            user = get_user_model().objects.get(email__iexact=username)
            if check_password(password, user.password):
                return user
            else:
                return None
        except get_user_model().DoesNotExist:
            # No user was found, return None - triggers default login failed
            return None


def create_week_scheduling(scheduled_exam, node='week_schedulings'):
    """
    create the shcedule exam on firebase week_schedulings node
    :param scheduled_exam:
    :return:
    """
    from .models import ScheduledExam
    removal_status = (
        ScheduledExam.PROCEDURES_EXECUTED,
        ScheduledExam.EXAM_MISSED,
        ScheduledExam.PATIENT_CANCELED,
        ScheduledExam.LAB_RECORD_CANCELED,
        ScheduledExam.EXAM_EXPIRED
    )

    firebase = pyrebase.initialize_app(settings.FB_CONFIG)
    db = firebase.database()

    try:
        lid = str(scheduled_exam.laboratory_id)
        pid = str(scheduled_exam.prescription_id)

        labs = db.child(node).child(lid).child(pid).get()
        labs = labs.val()

        if scheduled_exam.status in removal_status:
            db.child(node).child(lid).child(pid).child('exams').child(str(scheduled_exam.id)).remove()
            if not db.child(node).child(lid).child(pid).child('exams').get().val():
                db.child(node).child(lid).child(pid).remove()
                if not db.child(node).child(lid).get().val():
                    db.child(node).child(lid).remove()
            return

        prescription = scheduled_exam.prescription
        if not labs or 'exams' not in labs.keys():
            hename = ''
            selfie = None
            patient = prescription.patient
            if bool(patient.selfie_uploadcare) or bool(patient.selfie):
                try:
                    selfie = patient.selfie_uploadcare.url
                except (AttributeError, ValueError):
                    selfie = patient.selfie.url

            if prescription.health_insurance_plan:
                hename = prescription.health_insurance_plan.name

            db.child(node).child(lid).child(pid).update({
                'avatar': selfie,
                'firstExamTime': 0,
                'insurancePlan': hename,
                'laboratoryName': scheduled_exam.laboratory.description,
                'name': patient.full_name})
            firstExamTime = 0

        else:
            firstExamTime = int(labs.get('firstExamTime'))

        examTime = int(scheduled_exam.scheduled_time.timestamp()) if scheduled_exam.scheduled_time is not None else 0
        db.child(node).child(lid).child(pid).child('exams').child(str(scheduled_exam.id)).set({
            "name": scheduled_exam.exam.description,
            "status": scheduled_exam.status,
            "labFileCode": scheduled_exam.lab_file_code,
            "scheduledTime": examTime})

        if firstExamTime > examTime:
            db.child(node).child(lid).child(pid).child('firstExamTime').set(examTime)
    except Exception as e:
        print(e)


def authenticate_user(func_to_decorate):
    """
    Validates if current logged user is the same as the one passed on URL (user_id: pk)
    :param func_to_decorate:
    :return:
    """

    def new_func(*original_args, **original_kwargs):
        request = original_args[1]
        # If not a retrieve/update request, move on:
        try:
            user_id = int(request.resolver_match.kwargs['pk'])
        except (AttributeError, KeyError, ValueError):
            return func_to_decorate(*original_args, **original_kwargs)

        if request.user and request.user.id != user_id:
            raise AuthenticationFailed("This token does not belong to the given user.")

        return func_to_decorate(*original_args, **original_kwargs)

    return new_func


def authenticate_user_by_prescription(func_to_decorate):
    """
    Validates if current logged user is the same as the one belonging to the prescription_id on URL
    :param func_to_decorate:
    :return:
    """

    def new_func(*original_args, **original_kwargs):
        request = original_args[1]
        # If not a retrieve/update request, move on:
        try:
            prescription_id = int(request.resolver_match.kwargs['pk'])
        except (AttributeError, KeyError, ValueError):
            return func_to_decorate(*original_args, **original_kwargs)

        try:
            from domain.models import MedicalPrescription

            prescription = MedicalPrescription.objects.get(pk=prescription_id)
            if request.user and request.user.id != prescription.patient.user.id:
                raise AuthenticationFailed("This token does not belong to the prescription's user.")
        except ObjectDoesNotExist:
            pass

        return func_to_decorate(*original_args, **original_kwargs)

    return new_func


def field_to_type(f):
    """

    :param f:
    :return:
    """
    if isinstance(f, serializers.FloatField):
        return 'number'
    elif isinstance(f, serializers.CharField) or \
            isinstance(f, serializers.IPAddressField):
        return 'string'
    elif isinstance(f, serializers.BooleanField):
        return 'boolean'
    elif isinstance(f, serializers.DateField):
        return 'date'
    elif isinstance(f, serializers.DateTimeField):
        return 'dateTime'
    elif isinstance(f, serializers.IntegerField):
        return 'integer'
    return None


def to_field_format(f):
    """

    :param f:
    :return:
    """
    if isinstance(f, serializers.FloatField):
        return 'float'
    elif isinstance(f, serializers.IntegerField):
        return 'int64'

    return None


def swagrize(serializer_class):
    """

    :param serializer_class:
    :return:
    """
    serializer = serializer_class()
    properties = {}
    for field_name in serializer.fields:
        field = serializer.fields[field_name]
        field_spec = {
            'type': field_to_type(field)
        }

        field_format = to_field_format(field)
        if field_format:
            field_spec['format'] = field_format

        field_spec['description'] = field.help_text or ''
        properties[field.field_name] = field_spec

    model_spec = {
        'type': 'object',
        'properties': properties
    }
    return model_spec


def is_base64(content):
    """
    Verifies if a given content has a valid base64 format
    :param content:
    :return:
    """
    # already an image
    if type(content) is ImageFieldFile:
        return True

    # a string
    try:
        base64.decodebytes(content.encode())
        return True
    except binascii.Error:
        return False


def base_64_to_image_file(base_64_img, image_name):
    """
    Parses a base64 string into a ContentFile
    :param base_64_img: mixed
    :param image_name: str
    :return: ContentFile
    """
    # already an image
    if type(base_64_img) is ImageFieldFile:
        return base_64_img

    if not base_64_img:
        return None

    base_64_prefix = "data:image/jpeg;base64,"

    if base_64_img.startswith(base_64_prefix):
        base_64_img = base_64_img.split(base_64_prefix)[1]

    decoded_file = b64decode(base_64_img)
    return ContentFile(decoded_file, image_name)


def prescription_path(instance, filename):
    """
    File will be uploaded to MEDIA_ROOT/<user_id>/user_data/prescriptions/<prescription_id>/<filename>
    :param instance:
    :param filename:
    :return: str
    """
    filename = filename.split(".")
    return '{0}/user_data/prescriptions/{1}/{2}_{3}.{4}'.format(instance.patient.user.id,
                                                                instance.id, filename[0],
                                                                int(datetime.datetime.now().timestamp()),
                                                                filename[1])


def prescription_path_for_prescription_piece(instance, filename):
    """
    File will be uploaded to MEDIA_ROOT/<user_id>/user_data/prescriptions/<prescription_id>/<filename>
    :param instance:
    :param filename:
    :return: str
    """
    filename = filename.split(".")
    return '{0}/user_data/prescriptions/{1}/{2}/{3}_{4}.{5}'.format(instance.prescription.patient.user.id,
                                                                    instance.prescription.id,
                                                                    instance.id,
                                                                    filename[0],
                                                                    int(datetime.datetime.now().timestamp()),
                                                                    filename[1])


def user_data_path(instance, filename):
    """
    File will be uploaded to MEDIA_ROOT/<user_id>/user_data/<filename>
    :param instance:
    :param filename:
    :return: str
    """
    filename = filename.split(".")
    return '{0}/user_data/{1}_{2}.{3}'.format(instance.user.id, filename[0],
                                              int(datetime.datetime.now().timestamp()), filename[1])


def exam_result_path(instance, filename):
    """
    File will be uploaded to MEDIA_ROOT/<user_id>/user_data/prescriptions/<prescription_id>/<filename>
    :param instance:
    :param filename:
    :return: str
    """
    return '{0}/user_data/prescriptions/{1}/exam_results/{2}/{3}' \
        .format(instance.scheduled_exam.prescription.patient.user.id,
                instance.scheduled_exam.prescription.id, instance.scheduled_exam.id, filename)


def has_valid_key(dictionary, key):
    """
    Verifies if there is a non-empty value inside a dict
    :param dictionary:
    :param key:
    :return: bool
    """
    if key not in dictionary:
        return False

    if type(dictionary[key]) == ImageFieldFile:
        return True

    return True if dictionary[key] else False


def validate_fields(dictionary, fields):
    """
    Validates if all the keys inside 'fields' list have valid values
    :param dictionary:
    :param fields:
    :return: dict
    """
    errors = {}
    for key in fields:
        if not has_valid_key(dictionary, key):
            errors.update({key: "This field is required."})

    return errors


def custom_exception_handler(exc, context):
    """
    :param exc:
    :param context:
    :return:
    """
    traceback.print_tb(exc.__traceback__)
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)

    # Now add the HTTP status code to the response.
    if response is not None:
        response.data['status_code'] = response.status_code

    return response


def firebase_token(user):
    """
    Return firebase auth token.
    :param user: 
    :return: 
    """
    try:
        import pyrebase

        firebase = pyrebase.initialize_app(settings.FB_CONFIG)
        token = firebase.auth().create_custom_token(user.user.id, additional_claims={"manager": False})
        return token
    except Exception as e:
        print("Error creating custom token: ")
        print(e)
        return None


def send_email_via_ssl(to, subject, text):
    message = 'Subject: {}\n\n{}'.format(subject, text).encode('utf-8')

    server = smtplib.SMTP_SSL(settings.EMAIL_HOST, settings.EMAIL_PORT)
    server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
    server.sendmail(settings.EMAIL_HOST_USER, to, message)


def remove_milliseconds_from_timestamp(timestamp):
    return timestamp / 1000.0 if len(str(timestamp)) == 13 else timestamp


def get_notification_data(status, *args):
    """
    Returns subject and message to a given status in order to send push notification
    :param status:
    :return:
    """
    data = {"subject": "", "message": ""}

    from domain.models import MedicalPrescription, ScheduledExam
    if status in MedicalPrescription.CANCEL_STATUS:
        data["subject"] = "Não foi possível agendar seu exame"
        data["message"] = "{0}, tive alguns problemas para aprovar seu pedido de exame."

    elif status == ScheduledExam.ELIGIBLE_PATIENT:
        data["subject"] = "Pedido verificado"
        data["message"] = "{0}, já analisei seu pedido de exame. Vamos ver os próximos passos?"

    data["subject"] = data["subject"].format(*args)
    data["message"] = data["message"].format(*args)

    return data


def clear_empty_firebase_node(group, root, db):
    if len(db.child(root).child(group).get().val()) == 0:
        db.child(root).child(group).remove()


def grouped_exams_by_lab_date_keygen(se, way='encode'):
    """
    Groups the scheduled date and lab for scheduled exams, always sorted by date, lab
    :param scheduled_exams:
    :return: list
    """

    try:
        if way == 'encode':
            lab = se.laboratory.id if se.laboratory else 0
            if se.scheduled_time:
                scheduled_time = se.scheduled_time.strftime("%Y%m%d")
            else:
                scheduled_time = se.created.strftime("%Y%m%d")
            return '{}:{}:{}'.format(scheduled_time,
                                     se.prescription.patient.user.id,
                                     lab)
        d, user, lab = se.split(':')
        return datetime.date(int(d[:4]), int(d[4:6]), int(d[6:])), int(user), int(lab)
    except Exception as e:
        print(e)
        return ''


def namedtuplefetchall(cursor):
    "Return all rows from a cursor as a namedtuple"
    desc = cursor.description
    nt_result = namedtuple('Result', [col[0] for col in desc])
    return [nt_result(*row) for row in cursor.fetchall()]


def get_register_data(grouping):
    from django.db import connection

    result = {}
    with connection.cursor() as cursor:
        cursor.execute(QUERY_GENERAL % grouping)
        result['all'] = namedtuplefetchall(cursor)
        cursor.execute(QUERY_GENERAL_WORKING_DAYS % grouping)
        result['wdays'] = namedtuplefetchall(cursor)

    return result


def disable_signals():
    """
    Disables push notifications signal and firebase sync tasks (used on unit tests)
    :return:
    """
    from django.db.models.signals import post_save
    from domain.models import ScheduledExam, MedicalPrescription, ScheduledExamPhoneCall, Exam, Patient
    from domain.signals.send_notification import schedule_exam_notifications, prescription_notifications, \
        on_save_scheduled_phone_call
    from domain.signals.update_firebase_db import sync_prescription_to_firebase, delete_fb_tasks, \
        sync_scheduled_exams_to_firebase, delete_fb_scheduled_exams_tasks, sync_week_schedulings_to_firebase, \
        delete_fb_phone_call_tasks_1, delete_fb_phone_call_tasks_2, sync_scheduled_exams_phone_call_to_firebase_1, \
        sync_scheduled_exams_phone_call_to_firebase_2, sync_results_ac_to_firebase, sync_results_rdi_to_firebase, \
        sync_exam_results_to_firebase, sync_waiting_for_patient_to_firebase, sync_waiting_for_patient_to_firebase_2, \
        sync_archived_to_firebase, sync_archived_to_firebase_2, remove_nodes_from_deleted_user

    post_save.disconnect(schedule_exam_notifications, sender=ScheduledExam)
    post_save.disconnect(sync_prescription_to_firebase, sender=MedicalPrescription)
    post_save.disconnect(prescription_notifications, sender=MedicalPrescription)
    post_save.disconnect(delete_fb_tasks, sender=MedicalPrescription)
    post_save.disconnect(sync_scheduled_exams_to_firebase, sender=ScheduledExam)
    post_save.disconnect(delete_fb_scheduled_exams_tasks, sender=ScheduledExam)
    post_save.disconnect(on_save_scheduled_phone_call, sender=ScheduledExamPhoneCall)
    post_save.disconnect(sync_week_schedulings_to_firebase, sender=ScheduledExam)
    post_save.disconnect(delete_fb_phone_call_tasks_1, sender=MedicalPrescription)
    post_save.disconnect(delete_fb_phone_call_tasks_2, sender=ScheduledExamPhoneCall)
    post_save.disconnect(sync_scheduled_exams_phone_call_to_firebase_1, sender=ScheduledExam)
    post_save.disconnect(sync_scheduled_exams_phone_call_to_firebase_2, sender=ScheduledExamPhoneCall)
    post_save.disconnect(sync_results_ac_to_firebase, sender=ScheduledExam)
    post_save.disconnect(sync_results_rdi_to_firebase, sender=ScheduledExam)
    post_save.disconnect(sync_exam_results_to_firebase, sender=Exam)
    post_save.disconnect(sync_waiting_for_patient_to_firebase, sender=MedicalPrescription)
    post_save.disconnect(sync_waiting_for_patient_to_firebase_2, sender=ScheduledExam)
    post_save.disconnect(sync_archived_to_firebase, sender=MedicalPrescription)
    post_save.disconnect(sync_archived_to_firebase_2, sender=ScheduledExam)
    post_save.disconnect(remove_nodes_from_deleted_user, sender=Patient)


def get_results_expected_date(data):
    """
    Sets results_expected_at field from timestamp to  datetime.
    :param data:
    :return:
    """
    # Parses timestamp into datetime
    results_expected_at = data.get("results_expected_at", None)

    if results_expected_at:
        results_expected_at = remove_milliseconds_from_timestamp(results_expected_at)
        return datetime.datetime.fromtimestamp(results_expected_at)

    return None


def get_date_from_timestamp(data, key):
    """
    Sets given field from timestamp to  datetime.
    :param key:
    :return:
    """
    # Parses timestamp into datetime
    timestamp = data.get(key, None)

    if timestamp:
        timestamp = remove_milliseconds_from_timestamp(timestamp)
        return datetime.datetime.fromtimestamp(timestamp)

    return None


def get_gmt_time(hour):
    tz = pytz.timezone('America/Sao_Paulo')
    dt = datetime.datetime.now().replace(hour=hour, minute=0, second=0, microsecond=0)
    norm_dt = tz.normalize(tz.localize(dt))
    gmt = norm_dt.astimezone(pytz.utc)
    return gmt.replace(tzinfo=None)


def get_phone_call_history(scheduled_exam):
    versions = Version.objects.get_for_object(scheduled_exam.scheduledexamphonecall)

    data = {
        "scheduled_time": scheduled_exam.scheduledexamphonecall.call_time.strftime("%Y-%m-%d %H:%M:%S") if scheduled_exam.scheduledexamphonecall.created else 0,
        "call_time": ''}
    vdata = []
    tmp_call = 0
    for version in versions:
        version_data = json.loads(version.serialized_data)[0]['fields']
        vdata.append({"scheduled_time": parser.parse(version_data.get('call_time', '')).strftime("%Y-%m-%d %H:%M:%S") if version_data.get('call_time',
                                                                                            None) else '',
            "call_time": tmp_call
        })
        tmp_call = version.revision.date_created.strftime("%Y-%m-%d %H:%M:%S") if version.revision.date_created else ''

    if len(vdata) > 0:
        vdata.reverse()
        vdata.pop()
    vdata.append(data)
    return vdata


def remove_exam_from_firebase_node(db, new_ids, group_key, instance):
    new_ids.remove(instance.pk)
    if len(new_ids) > 0:
        db.child('preregister').child(group_key).child('examIds').set(new_ids)
    else:
        db.child('preregister').child(group_key).remove()
