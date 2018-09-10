# encode: utf-8

import datetime

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from domain.tests.factory_models import (ExamFactory,
                                         ScheduledExamFactory,
                                         ScheduledExamPhoneCallFactory)

from domain.utils import disable_signals


class ScheduledExamPhoneCallAPITests(APITestCase):

    def setUp(self):
        """
        Setting up things before tests.
        :return:
        """
        # Disabling push notifications signal and firebase sync tasks.
        disable_signals()

        # Getting authenticated for the next requests.
        User.objects.create_user('lab', 'lab@roundpe.gs', password='secret')
        self.client.login(username='lab', password='secret')

        self.exam_by_phone = ExamFactory()
        self.exam_by_phone.is_scheduled_by_phone = True
        self.exam_by_phone.save()

        # Creating scheduled exam.
        self.scheduled_exam = ScheduledExamFactory()

        self.scheduled_exam_by_phone = ScheduledExamFactory()
        self.scheduled_exam_by_phone.exam = self.exam_by_phone
        self.scheduled_exam_by_phone.save()

        # Creating phone call
        self.phone_call = ScheduledExamPhoneCallFactory()

    def test_post_api_201(self):
        """
        Tests POST API for status code 201.
        """
        data = {
            "scheduled_exam_id": self.scheduled_exam_by_phone.id,
            "phone": 5511961991225,
            "call_time": int(datetime.datetime.now().timestamp())
        }
        url = reverse('mobile:phone-call-list')
        response = self.client.post(url, data=data, format="json")
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', response_data)
        self.assertEqual(response_data['scheduled_exam_id'], self.scheduled_exam_by_phone.id)
        self.assertEqual(response_data['call_time_timestamp'], data["call_time"])
        self.assertEqual(response_data['phone'], data['phone'])
        self.assertFalse(response_data['is_canceled'])

    def test_post_api_400_not_scheduled_by_phone_exam(self):
        """
        Tests POST API for status code 400.
        """
        data = {
            "scheduled_exam_id": self.scheduled_exam.id,
            "phone": 5511961991225,
            "call_time": int(datetime.datetime.now().timestamp())
        }
        url = reverse('mobile:phone-call-list')
        response = self.client.post(url, data=data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_api_400_no_exam_id(self):
        """
        Tests POST API for status code 400.
        """
        data = {
            # "scheduled_exam_id": self.scheduled_exam.id,
            "phone": 5511961991225,
            "call_time": int(datetime.datetime.now().timestamp())
        }
        url = reverse('mobile:phone-call-list')
        response = self.client.post(url, data=data, format="json")
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('scheduled_exam_id', response_data)

    def test_post_api_400_no_phone(self):
        """
        Tests POST API for status code 400.
        """
        data = {
            "scheduled_exam_id": self.scheduled_exam.id,
            # "phone": 5511961991225,
            "call_time": int(datetime.datetime.now().timestamp())
        }
        url = reverse('mobile:phone-call-list')
        response = self.client.post(url, data=data, format="json")
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('phone', response_data)

    def test_post_api_400_no_call_time(self):
        """
        Tests POST API for status code 400.
        """
        data = {
            "scheduled_exam_id": self.scheduled_exam.id,
            "phone": 5511961991225,
            # "call_time": int(datetime.datetime.now().timestamp())
        }
        url = reverse('mobile:phone-call-list')
        response = self.client.post(url, data=data, format="json")
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('call_time', response_data)

    def test_post_api_400_invalid_exam_id(self):
        """
        Tests POST API for status code 400.
        """
        data = {
            "scheduled_exam_id": 99999999999,
            "phone": 5511961991225,
            "call_time": int(datetime.datetime.now().timestamp())
        }
        url = reverse('mobile:phone-call-list')
        response = self.client.post(url, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_api_400_invalid_call_time(self):
        """
        Tests POST API for status code 400.
        """
        data = {
            "scheduled_exam_id": self.scheduled_exam.id,
            "phone": 5511961991225,
            "call_time": "2015-01-27 10:45"
        }
        url = reverse('mobile:phone-call-list')
        response = self.client.post(url, data=data, format="json")
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('call_time', response_data)

    def test_put_api_200(self):
        """
        Tests PUT API for status code 200.
        """
        data = {
            "phone": 5511961991226,
            "call_time": 1491318396,
            "is_canceled": True
        }
        url = reverse('mobile:phone-call-detail', kwargs={'pk': self.phone_call.id})
        response = self.client.put(url, data=data, format="json")
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['scheduled_exam_id'], self.phone_call.scheduled_exam.id)
        self.assertEqual(response_data['call_time_timestamp'], data['call_time'])
        self.assertEqual(response_data['phone'], data['phone'])
        self.assertEqual(response_data['is_canceled'], data['is_canceled'])

    def test_put_api_invalid_pk_404(self):
        """
        Tests PUT API for status code 404.
        """
        data = {
            "phone": 5511961991226,
            "call_time": 1491318396,
            "is_canceled": True
        }
        url = reverse('mobile:phone-call-detail', kwargs={'pk': 9999999999})
        response = self.client.put(url, data=data, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_put_api_400_no_phone(self):
        """
        Tests PUT API for status code 400.
        """
        data = {
            "scheduled_exam_id": self.scheduled_exam.id,
            # "phone": 5511961991225,
            "call_time": int(datetime.datetime.now().timestamp())
        }
        url = reverse('mobile:phone-call-detail', kwargs={'pk': self.phone_call.id})
        response = self.client.put(url, data=data, format="json")
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('phone', response_data)

    def test_put_api_400_no_call_time(self):
        """
        Tests PUT API for status code 400.
        """
        data = {
            "scheduled_exam_id": self.scheduled_exam.id,
            "phone": 5511961991225,
            # "call_time": int(datetime.datetime.now().timestamp())
        }
        url = reverse('mobile:phone-call-detail', kwargs={'pk': self.phone_call.id})
        response = self.client.put(url, data=data, format="json")
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('call_time', response_data)

    def test_put_api_400_invalid_call_time(self):
        """
        Tests PUT API for status code 400.
        """
        data = {
            "scheduled_exam_id": self.scheduled_exam.id,
            "phone": 5511961991225,
            "call_time": "2015-01-27 10:45"
        }
        url = reverse('mobile:phone-call-detail', kwargs={'pk': self.phone_call.id})
        response = self.client.put(url, data=data, format="json")
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('call_time', response_data)
