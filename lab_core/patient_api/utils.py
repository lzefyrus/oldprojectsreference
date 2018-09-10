# encode: utf-8

import json
import requests

from dateutil import parser
from reversion.models import Version
from django.core.files.base import ContentFile
from django.db.models.fields.files import ImageFieldFile
from domain.models import MedicalPrescription

from django.core.exceptions import ObjectDoesNotExist

from concierge.models import Operator
from domain.models import MedicalPrescription, ScheduledExam


def is_user_action(status):
    if status in (MedicalPrescription.PATIENT_REQUESTED,
                  ScheduledExam.PATIENT_CANCELED_BY_CALL,
                  ScheduledExam.PATIENT_CANCELED):
        return True
    return False



def get_prescription_version(prescription, field):
    """
    Get the versions of a field for a medical prescription.
    :param prescription: MedicalPrescription
    :param field: str
    :return: dict
    """
    versions = Version.objects.get_for_object(prescription)

    if not versions:
        raise KeyError

    data = []
    old_value = None

    for version in versions:
        version_data = json.loads(version.serialized_data)[0]['fields']
        who = None
        if version_data[field] != old_value:
            if version_data.get("modified_by", None) and version_data["modified_by"]:
                try:
                    operator = Operator.objects.get(pk=version_data["modified_by"])
                    who = operator.user.username
                except ObjectDoesNotExist:
                    if is_user_action(version_data['status']):
                        who = "PACIENTE"
                    else:
                        who = "Não Identificado"

            data.append({"value": version_data[field],
                         "modified": int(parser.parse(version_data['modified']).timestamp()),
                         "who": who
                         })

        old_value = version_data[field]

    return data

def get_scheduled_exam_version_data(scheduled_exam, fields=None, status=None, kv=False):
    """
    Get the versions of a field for a scheduled exam.
    :param scheduled_exam: ScheduledExam
    :param fields: list
    :param status: list
    :return: dict
    """
    from collections import OrderedDict
    versions = Version.objects.get_for_object(scheduled_exam)

    if not versions:
        raise KeyError

    data = []
    dict_data = {}
    for version in versions:
        version_data = json.loads(version.serialized_data)[0]['fields']
        if (status and version_data.get('status', None) in status) or status is None:
            if fields:
                if kv is True and len(fields) == 2:
                    dict_data[version_data.get(fields[0], '')] = version_data.get(fields[1], '')
                else:
                    tmp = dict(((k, v) for k,v in version_data.items() if k in fields))
                    data.append(tmp)
            else:
                data.append(version_data)
    if dict_data:
        return OrderedDict(sorted(dict_data.items(), key=lambda t: t[0]))
    return data

def get_scheduled_exam_version(scheduled_exam, field):
    """
    Get the versions of a field for a scheduled exam.
    :param scheduled_exam: ScheduledExam
    :param field: str
    :return: dict
    """
    versions = Version.objects.get_for_object(scheduled_exam)

    if not versions:
        raise KeyError

    data = []
    old_value = None

    for version in versions:
        version_data = json.loads(version.serialized_data)[0]['fields']
        who = None

        if version_data[field] != old_value:
            if version_data.get("modified_by", None) and version_data["modified_by"]:
                try:
                    operator = Operator.objects.get(pk=version_data["modified_by"])
                    who = operator.user.username
                except ObjectDoesNotExist:
                    if is_user_action(version_data['status']):
                        who = "PACIENTE"
                    else:
                        who = "Não Identificado"

            data.append({"value": version_data[field],
                         "modified": int(parser.parse(version_data['modified']).timestamp()),
                         "who": who})

        old_value = version_data[field]

    return data


def get_address_component(address_components, component_name):
    for component in address_components:
        name = component["long_name"] if component_name in component["types"] else None
        if name:
            return name


def get_patient_picture_uploadcare(picture, picture_name, patient, latest_prescription_pk=None):
    """
    Retrieves picture as file.
    :param picture:
    :param picture_name:
    :param patient:
    :param latest_prescription_pk:
    :return:
    """
    picture_file = {
        "picture_id_front_uploadcare": "id_front_uploadcare.jpg",
        "picture_id_back_uploadcare": "id_back_uploadcare.jpg",
        "selfie_uploadcare": "selfie_uploadcare.jpg",
    }
    if type(picture) is ImageFieldFile:
        return picture
    img = None
    if picture:
        img = ContentFile(requests.get(picture).content)
        img.name = picture_file[picture_name]
    return img or getattr(patient, picture_name)


def get_picture_as_content_file_uploadcare(picture, picture_name, patient=None, latest_prescription_pk=None):
    """
    Returns picture as ContentFile.
    :param picture:
    :param picture_name:
    :param patient:
    :param latest_prescription_pk:
    :return:
    """
    file_name = {
        "picture_id_front_uploadcare": "id_front_uploadcare.jpg",
        "picture_id_back_uploadcare": "id_back_uploadcare.jpg",
        "selfie_uploadcare": "selfie_uploadcare.jpg",
        "picture_prescription_uploadcare": "medical-prescription_uploadcare.jpg",
        "picture_insurance_card_front_uploadcare": "card-front_uploadcare.jpg",
        "picture_insurance_card_back_uploadcare": "card-back_uploadcare.jpg"
    }
    # Try to get picture from patient data, otherwise get it from the latest prescription
    if type(picture) is ImageFieldFile:
        return picture
    if picture:
        img = ContentFile(requests.get(picture).content)
        img.name = file_name[picture_name]
    else:
        img = None
        if latest_prescription_pk:
            latest_prescription = MedicalPrescription.objects.get(pk=latest_prescription_pk)
            img = getattr(latest_prescription, picture_name)
    return img


def get_piece_picture_as_content_file_uploadcare(picture, picture_name, patient=None):
    """
    Returns picture as ContentFile.
    :param picture:
    :param picture_name:
    :param patient:
    :param latest_prescription_pk:
    :return:
    """
    file_name = {
        "picture_id_front_uploadcare": "id_front_uploadcare.jpg",
        "picture_id_back_uploadcare": "id_back_uploadcare.jpg",
        "selfie_uploadcare": "selfie_uploadcare.jpg",
        "picture_prescription_uploadcare": "medical-prescription_uploadcare.jpg",
        "picture_insurance_card_front_uploadcare": "card-front_uploadcare.jpg",
        "picture_insurance_card_back_uploadcare": "card-back_uploadcare.jpg"
    }
    # Try to get picture from patient data, otherwise get it from the latest prescription
    if type(picture) is ImageFieldFile:
        return picture
    if picture:
        img = ContentFile(requests.get(picture).content)
        img.name = file_name[picture_name]
    else:
        img = None
        # if latest_prescription_pk:
        #     latest_prescription = MedicalPrescription.objects.get(pk=latest_prescription_pk)
        #     img = getattr(latest_prescription, picture_name)
    return img
