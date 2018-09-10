# encode: utf-8

from unittest.mock import Mock, patch

from django.core.exceptions import ObjectDoesNotExist
from rest_framework.test import APITestCase

from domain.exceptions import (UnavailableFirebaseServiceError,
                               UnrecorverableFirebaseError)
from domain.firebaser import FirebaseCloudMessaging
from domain.models import Patient
from domain.tests.factory_models import PatientFactory


class TestFirebaseCloudMessaging(APITestCase):

    mock_post_patcher = None
    mock_post = None
    patient = None

    @classmethod
    def setUp(cls):
        cls.mock_post_patcher = patch('domain.firebaser.requests.post')
        cls.mock_post = cls.mock_post_patcher.start()
        cls.patient = PatientFactory()

    @classmethod
    def tearDown(cls):
        cls.mock_post_patcher.stop()

    def test_send_push_notification_no_token_error(self):
        try:
            FirebaseCloudMessaging().send_push_notification(None, "test", "test message")
            self.assertTrue(False, "Wrong token validation")
        except ValueError:
            self.assertTrue(True)

    def test_send_push_notification_no_title_error(self):
        try:
            # Configure the mock to return a response with an OK status code.
            fcm_success_response = {
                "multicast_id": 108,
                "success": 1,
                "failure": 0,
                "canonical_ids": 0,
                "results": [
                    {
                        "message_id": "1:08"
                    }
                ]
            }

            self.mock_post.return_value = Mock()
            self.mock_post.return_value.status_code = 200
            self.mock_post.return_value.json.return_value = fcm_success_response

            response = FirebaseCloudMessaging().send_push_notification(self.patient.token, "", "test message")
            self.assertDictEqual(response, fcm_success_response)
        except ValueError:
            self.assertTrue(True)

    def test_send_push_notification_no_message_error(self):
        try:
            # Configure the mock to return a response with an OK status code.
            fcm_success_response = {
                "multicast_id": 108,
                "success": 1,
                "failure": 0,
                "canonical_ids": 0,
                "results": [
                    {
                        "message_id": "1:08"
                    }
                ]
            }

            self.mock_post.return_value = Mock()
            self.mock_post.return_value.status_code = 200
            self.mock_post.return_value.json.return_value = fcm_success_response

            response = FirebaseCloudMessaging().send_push_notification(self.patient.token, "test", None)
            self.assertDictEqual(response, fcm_success_response)
        except ValueError:
            self.assertTrue(True)

    def test_send_push_notification_invalid_data(self):
        try:
            FirebaseCloudMessaging().send_push_notification(self.patient.token, "test", "test message", 1)
            self.assertTrue(False, "Wrong data validation")
        except ValueError:
            self.assertTrue(True)

    def test_send_push_notification_200_success(self):
        # Configure the mock to return a response with an OK status code.
        fcm_success_response = {
            "multicast_id": 108,
            "success": 1,
            "failure": 0,
            "canonical_ids": 0,
            "results": [
                {
                    "message_id": "1:08"
                }
            ]
        }
        self.mock_post.return_value = Mock()
        self.mock_post.return_value.status_code = 200
        self.mock_post.return_value.json.return_value = fcm_success_response

        # Call the service, which would send a request to the server.
        response = FirebaseCloudMessaging().send_push_notification(self.patient.token, "test", "test message")

        # If the request is sent successfully.
        self.assertDictEqual(response, fcm_success_response)

    def test_send_push_notification_200_success_with_data(self):
        # Configure the mock to return a response with an OK status code.
        fcm_success_response = {
            "multicast_id": 108,
            "success": 1,
            "failure": 0,
            "canonical_ids": 0,
            "results": [
                {
                    "message_id": "1:08"
                }
            ]
        }
        self.mock_post.return_value = Mock()
        self.mock_post.return_value.status_code = 200
        self.mock_post.return_value.json.return_value = fcm_success_response

        # Call the service, which would send a request to the server.
        data = {
            "status": "ELIGIBLE_PATIENT"
        }
        response = FirebaseCloudMessaging().send_push_notification(self.patient.token, "test", "test message", data)

        # If the request is sent successfully.
        self.assertDictEqual(response, fcm_success_response)

    def test_send_push_notification_200_success_update_token(self):
        # Configure the mock to return a response with an OK status code.
        fcm_success_response = {
            "multicast_id": 108,
            "success": 1,
            "failure": 0,
            "canonical_ids": 1,
            "results": [
                {
                    "message_id": "1:08",
                    "registration_id": "123321"
                }
            ]
        }
        self.mock_post.return_value = Mock()
        self.mock_post.return_value.status_code = 200
        self.mock_post.return_value.json.return_value = fcm_success_response

        # Call the service, which would send a request to the server.
        response = FirebaseCloudMessaging().send_push_notification(self.patient.token, "test", "test message")

        # If the request is sent successfully.
        self.assertDictEqual(response, fcm_success_response)

        # If patient token was properly updated.
        try:
            Patient.objects.get(token=fcm_success_response["results"][0]["registration_id"])
        except ObjectDoesNotExist:
            self.assertTrue(False, "Token not properly updated")

    def test_send_push_notification_200_unrecoverable_error_invalid(self):
        # Configure the mock to return a response with an OK status code.
        fcm_success_response = {
            "multicast_id": 108,
            "success": 0,
            "failure": 1,
            "canonical_ids": 0,
            "results": [
                {
                    "error": "InvalidRegistration"
                }
            ]
        }
        self.mock_post.return_value = Mock()
        self.mock_post.return_value.status_code = 200
        self.mock_post.return_value.json.return_value = fcm_success_response

        # Call the service, which would send a request to the server.
        try:
            FirebaseCloudMessaging().send_push_notification(self.patient.token, "test", "test message")
            self.assertTrue(False, "Token not properly deleted")
        except UnrecorverableFirebaseError:
            # If patient token was properly wiped.
            patient = Patient.objects.get(pk=self.patient.user.id)
            self.assertEquals(patient.token, None)

    def test_send_push_notification_200_unrecoverable_error_unregistered(self):
        # Configure the mock to return a response with an OK status code.
        fcm_success_response = {
            "multicast_id": 108,
            "success": 0,
            "failure": 1,
            "canonical_ids": 0,
            "results": [
                {
                    "error": "NotRegistered"
                }
            ]
        }
        self.mock_post.return_value = Mock()
        self.mock_post.return_value.status_code = 200
        self.mock_post.return_value.json.return_value = fcm_success_response

        # Call the service, which would send a request to the server.
        try:
            FirebaseCloudMessaging().send_push_notification(self.patient.token, "test", "test message")
            self.assertTrue(False, "Token not properly deleted")
        except UnrecorverableFirebaseError:
            # If patient token was properly wiped.
            patient = Patient.objects.get(pk=self.patient.user.id)
            self.assertEquals(patient.token, None)

    def test_send_push_notification_200_unavailable_error(self):
        # Configure the mock to return a response with an OK status code.
        fcm_success_response = {
            "multicast_id": 108,
            "success": 0,
            "failure": 1,
            "canonical_ids": 0,
            "results": [
                {
                    "error": "Unavailable"
                }
            ]
        }
        self.mock_post.return_value = Mock()
        self.mock_post.return_value.status_code = 200
        self.mock_post.return_value.json.return_value = fcm_success_response

        # Call the service, which would send a request to the server.
        try:
            FirebaseCloudMessaging().send_push_notification(self.patient.token, "test", "test message")
            self.assertTrue(False, "Unavailable error wrongly catched")
        except UnavailableFirebaseServiceError:
            self.assertTrue(True)
        except Exception:
            self.assertTrue(False, "Unavailable error wrongly catched")

    def test_send_push_notification_400_error(self):
        # Configure the mock to return a response with a 400 status code.
        self.mock_post.return_value = Mock()
        self.mock_post.return_value.status_code = 400

        # Call the service, which would send a request to the server.
        try:
            FirebaseCloudMessaging().send_push_notification(self.patient.token, "test", "test message")
            self.assertTrue(False, "400 error wrongly catched")
        except ValueError:
            self.assertTrue(True)
        except Exception:
            self.assertTrue(False, "400 error wrongly catched")

    def test_send_push_notification_500_error(self):
        # Configure the mock to return a response with 500 status code.
        self.mock_post.return_value = Mock()
        self.mock_post.return_value.status_code = 500

        # Call the service, which would send a request to the server.
        try:
            FirebaseCloudMessaging().send_push_notification(self.patient.token, "test", "test message")
            self.assertTrue(False, "500 error wrongly catched")
        except UnavailableFirebaseServiceError:
            self.assertTrue(True)
        except Exception:
            self.assertTrue(False, "500 error wrongly catched")
