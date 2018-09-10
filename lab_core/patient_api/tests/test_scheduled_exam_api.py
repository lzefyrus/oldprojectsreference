# encode: utf-8

import datetime
from dateutil import parser

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from domain.tests.factory_models import ExamExpirationFactory, ExamFactory, InsuranceCompanyFactory, LaboratoryFactory,\
    MedicalPrescription, MedicalPrescriptionFactory, ScheduledExamFactory, ScheduledExam
from domain.utils import disable_signals


class ScheduledExamAPITests(APITestCase):

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

        # Creating prescription
        self.prescription = MedicalPrescriptionFactory()

        # Creating scheduled exam.
        self.scheduled_exam = ScheduledExamFactory()

        # Creating lab
        self.laboratory = LaboratoryFactory()

        # Creating exam
        self.exam = ExamFactory()

        # Creating insurance company
        self.insurance_company = InsuranceCompanyFactory()

        # Creating expiration date
        self.exam_expiration = ExamExpirationFactory()
        self.exam_expiration.exam = self.exam
        self.exam_expiration.insurance_company = self.insurance_company
        self.exam_expiration.save()

        self.prescription.insurance_company = self.insurance_company
        self.prescription.save()

        self.scheduled_exam.exam = self.exam
        self.scheduled_exam.prescription = self.prescription
        self.scheduled_exam.save()

    def test_get_api_200(self):
        """
        Tests GET API for status code 200.
        """
        url = reverse('mobile:scheduled-exam-detail', kwargs={'pk': self.scheduled_exam.id})
        response = self.client.get(url)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['exam_id'], self.scheduled_exam.exam.id)
        self.assertEqual(response_data['laboratory_id'], self.scheduled_exam.laboratory.id)
        self.assertEqual(response_data['status'], self.scheduled_exam.status)
        scheduled_time_timestamp = int(parser.parse(self.scheduled_exam.scheduled_time).timestamp())
        self.assertEqual(response_data['scheduled_time_timestamp'], scheduled_time_timestamp)
        self.assertEqual(response_data['procedure_average_duration'], self.scheduled_exam.procedure_average_duration)
        self.assertEqual(response_data['confirmation'], self.scheduled_exam.confirmation)
        self.assertEqual(response_data['suggested_labs_id'], [lab.id for lab in self.scheduled_exam.suggested_labs.all()])
        # self.assertEqual(response_data['status_versions'], self.scheduled_exam.status_versions)

    def test_get_api_404(self):
        """
        Tests GET (Retrieve) API for status code 404.
        """
        url = reverse('mobile:scheduled-exam-detail', kwargs={'pk': 99999999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_put_api_200(self):
        """
        Tests PUT API for status code 200.
        """
        data = {
            "laboratory_id": self.laboratory.id,
            "scheduled_time": 1491318396,
            "status": "EXAM_TIME_SCHEDULED"
        }
        url = reverse('mobile:scheduled-exam-detail', kwargs={'pk': self.scheduled_exam.id})
        response = self.client.put(url, data=data, format="json")
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['exam_id'], self.scheduled_exam.exam.id)
        self.assertEqual(response_data['laboratory_id'], self.laboratory.id)
        self.assertEqual(response_data['status'], "EXAM_TIME_SCHEDULED")
        self.assertEqual(response_data['scheduled_time_timestamp'], 1491318396)
        self.assertEqual(response_data['procedure_average_duration'], self.scheduled_exam.procedure_average_duration)
        self.assertEqual(response_data['confirmation'], self.scheduled_exam.confirmation)
        self.assertEqual(response_data['suggested_labs_id'], [lab.id for lab in self.scheduled_exam.suggested_labs.all()])

    def test_put_api_invalid_pk_404(self):
        """
        Tests PUT API for status code 404.
        """
        data = {
            "laboratory_id": self.laboratory.id,
            "scheduled_time": 1491318396,
            "status": "EXAM_TIME_SCHEDULED"
        }
        url = reverse('mobile:scheduled-exam-detail', kwargs={'pk': 999999999})
        response = self.client.put(url, data=data, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_put_api_400_no_lab(self):
        """
        Tests PUT API for status code 400.
        """
        data = {
            # "laboratory_id": self.laboratory.id,
            "scheduled_time": 1491318396,
            "status": "EXAM_TIME_SCHEDULED"
        }
        url = reverse('mobile:scheduled-exam-detail', kwargs={'pk': self.scheduled_exam.id})
        response = self.client.put(url, data=data, format="json")
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('laboratory_id', response_data)

    def test_put_api_400_no_schedule_time(self):
        """
        Tests PUT API for status code 400.
        """
        data = {
            "laboratory_id": self.laboratory.id,
            # "scheduled_time": 1491318396,
            "status": "EXAM_TIME_SCHEDULED"
        }
        url = reverse('mobile:scheduled-exam-detail', kwargs={'pk': self.scheduled_exam.id})
        response = self.client.put(url, data=data, format="json")
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('scheduled_time', response_data)

    # def test_put_api_400_no_status(self):
    #     """
    #     Tests PUT API for status code 400.
    #     """
    #     data = {
    #         "laboratory_id": self.laboratory.id,
    #         "scheduled_time": 1491318396,
    #         # "status": "EXAM_TIME_SCHEDULED"
    #     }
    #     url = reverse('mobile:scheduled-exam-detail', kwargs={'pk': self.scheduled_exam.id})
    #     response = self.client.put(url, data=data, format="json")
    #     response_data = response.json()
    #
    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    #     self.assertIn('status', response_data)

    def test_put_api_400_invalid_schedule_time(self):
        """
        Tests PUT API for status code 400.
        """
        data = {
            "laboratory_id": self.laboratory.id,
            "scheduled_time": "2015-01-27 10:45",
            "status": "EXAM_TIME_SCHEDULED"
        }
        url = reverse('mobile:scheduled-exam-detail', kwargs={'pk': self.scheduled_exam.id})
        response = self.client.put(url, data=data, format="json")
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('scheduled_time', response_data)

    def test_put_api_400_invalid_lab(self):
        """
        Tests PUT API for status code 400.
        """
        data = {
            "laboratory_id": 99999999,
            "scheduled_time": 1491318396,
            "status": "EXAM_TIME_SCHEDULED"
        }
        url = reverse('mobile:scheduled-exam-detail', kwargs={'pk': self.scheduled_exam.id})
        response = self.client.put(url, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_put_api_400_invalid_status(self):
        """
        Tests PUT API for status code 400.
        """
        data = {
            "laboratory_id": self.laboratory.id,
            "scheduled_time": 1491318396,
            "status": "TEST"
        }
        url = reverse('mobile:scheduled-exam-detail', kwargs={'pk': self.scheduled_exam.id})
        response = self.client.put(url, data=data, format="json")
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('status', response_data)

    def test_put_api_cancel_200(self):
        """
        Tests PUT API for status code 200.
        """

        url = reverse('mobile:scheduled-exam-detail', kwargs={'pk': self.scheduled_exam.id})
        response = self.client.put(url+"cancel/")

        scheduled_exam = ScheduledExam.objects.get(pk=self.scheduled_exam.id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(scheduled_exam.status, ScheduledExam.PATIENT_CANCELED)

    def test_put_api_cancel_404(self):
        """
        Tests PUT API for status code 404.
        """

        url = reverse('mobile:scheduled-exam-detail', kwargs={'pk': 99999999})
        response = self.client.put(url+"cancel/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_post_api_retry_200(self):
        """
        Tests POST API for status code 200.
        """

        url = reverse('mobile:scheduled-exam-detail', kwargs={'pk': self.scheduled_exam.id})
        response = self.client.post(url+"retry/")

        scheduled_exam = ScheduledExam.objects.get(pk=self.scheduled_exam.id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(scheduled_exam.status, ScheduledExam.EXAM_IDENTIFIED)
        self.assertEqual(scheduled_exam.prescription.status, MedicalPrescription.EXAMS_IDENTIFIED)

    def test_post_api_retry_404(self):
        """
        Tests POST API for status code 404.
        """

        url = reverse('mobile:scheduled-exam-detail', kwargs={'pk': 99999999})
        response = self.client.post(url+"retry/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_api_200_pre_defined_expiration_date(self):
        """
        Tests GET API for status code 200.
        """
        url = reverse('mobile:scheduled-exam-detail', kwargs={'pk': self.scheduled_exam.id})
        response = self.client.get(url)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        pre_defined_expiration = self.scheduled_exam.created + datetime.timedelta(days=self.exam_expiration.expiration_in_days)
        self.assertEqual(response_data['expiration_date_timestamp'], int(pre_defined_expiration.timestamp()))

    def test_get_api_200_registered_expiration_date(self):
        """
        Tests GET API for status code 200. It must return the registered_expiration date not a pre defined expiration
        (exam_expiration)
        """
        registered_expiration = datetime.datetime.now()
        self.scheduled_exam.expiration_date = registered_expiration
        self.scheduled_exam.save()

        url = reverse('mobile:scheduled-exam-detail', kwargs={'pk': self.scheduled_exam.id})
        response = self.client.get(url)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['expiration_date_timestamp'], int(registered_expiration.timestamp()))
