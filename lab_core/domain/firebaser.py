# encode: utf-8

import requests
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

from domain import utils
from domain.exceptions import (UnavailableFirebaseServiceError,
                               UnrecorverableFirebaseError)
from domain.models import Patient


class FirebaseCloudMessaging(object):

    RECOVERABLE_ERRORS = ("Unavailable",)
    UNRECOVERABLE_ERRORS = ("InvalidRegistration", "NotRegistered")

    def __init__(self):
        """
        Sets the Auth headers.
        """
        self.url = settings.FCM_URL
        self.key = settings.FCM_KEY
        self.headers = {"Authorization": "key={0}".format(self.key), "Content-Type": "application/json"}

    def send_push_notification(self, token, title, message="", data=None):
        """
        Sends a push notification through FCM.

        :param token:
        :param title:
        :param message:
        :param data:
        :return:
        """
        validate_fields = (token, )
        if None in validate_fields or "" in validate_fields:
            raise ValueError("Fields: 'token' cannot be empty")

        if data and type(data) is not dict:
            raise ValueError("Field 'data' must be a valid dict")

        json = {
            "to": token,
        }

        if message:
            json.update(
                {
                    "notification": {
                        "title": title,
                        "body": message,
                        "icon": "notification_icon",
                        "sound": "default",
                        "color": settings.FCM_DEFAULT_NOTIFICATION_ICON_COLOR,
                    }
                }
            )

        if data:
            json.update({"data": data})

        try:
            response = requests.post(url=self.url, headers=self.headers, json=json)
        except Exception:
            raise UnavailableFirebaseServiceError

        if str(response.status_code).startswith("2"):
            response = response.json()
        elif str(response.status_code).startswith("4"):
            raise ValueError("Wrong request (4xx): {0}".format(response.text))
        elif str(response.status_code).startswith("5"):
            raise UnavailableFirebaseServiceError

        if self.is_success(response):
            self.update_token(response, token)
            return response

        if self.is_unrecoverable_error(response):
            self.remove_token_from_db(token)
            raise UnrecorverableFirebaseError("Invalid Token. It has been removed from database: {0}.".format(token))

        raise UnavailableFirebaseServiceError

    @staticmethod
    def is_success(response):
        """
        Verifies if FCM response is a success.

        :param response:
        :return:
        """
        return utils.has_valid_key(response, "success")

    @staticmethod
    def update_token(response, old_token):
        """
        Updates Patient's token on database in case FCM provides a new one to be updated.

        :param response:
        :param old_token:
        :return:
        """
        if not utils.has_valid_key(response, "canonical_ids"):
            return

        try:
            new_token = response["results"][0]["registration_id"]
            patient = Patient.objects.get(token=old_token)
            patient.token = new_token
            patient.save()
        except ObjectDoesNotExist:
            pass

    @classmethod
    def is_unrecoverable_error(cls, response):
        """
        Verifies if FCM response is an unrecoverable error.

        :param response:
        :return:
        """
        return response["results"][0]["error"] in cls.UNRECOVERABLE_ERRORS

    @staticmethod
    def remove_token_from_db(token):
        """
        Removes Patient token from database.

        :param token:
        :return:
        """
        try:
            patient = Patient.objects.get(token=token)
            patient.token = None
            patient.save()
        except ObjectDoesNotExist:
            pass
