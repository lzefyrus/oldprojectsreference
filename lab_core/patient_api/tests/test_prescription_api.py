# encode: utf-8
import io

from dateutil import parser
import logging
from unittest.mock import patch

from django.contrib.auth.models import User

from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from domain.models import MedicalPrescription

from domain.tests.factory_models import (ExamFactory, ExamResultFactory, LaboratoryFactory, ExamResultDetailFactory,
                                         MedicalPrescriptionFactory, PatientFactory, PreparationStepFactory,
                                         ScheduledExam, ScheduledExamFactory, ScheduledExamPhoneCallFactory,
                                         ScheduledExamPhoneCall)
from domain.utils import disable_signals

log = logging.getLogger(__name__)


class Response(object):
    def __init__(self, status, content):
        self.status = status
        self.content = content


def mock_image_response(self):
    image_path = 'domain/tests/test-image.jpg'
    content = io.open(image_path, 'rb').read()
    response = Response(200, bytearray(content))
    return response


@override_settings(
    task_always_eager=True,
)
class PrescriptionAPITests(APITestCase):

    patient = None
    laboratory = None

    def setUp(self):
        """
        Setting up things before tests.
        :return:
        """
        # Disabling push notifications signal and firebase sync tasks.
        disable_signals()

        # Getting authenticated for the next requests.
        user = User.objects.create_user('stewart', 'stewart@roundpe.gs', password='secret')
        user_two = User.objects.create_user('stewart2', 'stewart2@roundpe.gs', password='secret2')
        self.client.login(username='stewart', password='secret')

        self.prescription = MedicalPrescriptionFactory()

        # Creating Exams (dependency for POST tests).
        self.exam_one = ExamFactory()
        self.exam_one.save()
        self.exam_two = ExamFactory()
        self.exam_two.save()

        # Creating Patient and Laboratory (dependency for POST tests).
        self.patient = PatientFactory()
        self.patient.user = user
        self.patient.save()
        self.laboratory = LaboratoryFactory()

        # Creating Preparation Steps (dependency for GET tests).
        self.preparation_step = PreparationStepFactory()
        self.preparation_step.exam = self.exam_one
        self.preparation_step.laboratory = self.laboratory
        self.preparation_step.save()

        # Creating Scheduled Exam
        self.scheduled_exam = ScheduledExamFactory()
        self.scheduled_exam.exam = self.exam_one
        self.scheduled_exam.prescription = self.prescription
        self.scheduled_exam.laboratory = self.laboratory

        # Creating prescription with suggested laboratories
        suggested_laboratory_one = LaboratoryFactory()
        suggested_laboratory_two = LaboratoryFactory()
        self.scheduled_exam.suggested_labs.add(suggested_laboratory_one, suggested_laboratory_two)
        self.scheduled_exam.save()

        # Creating exam phone call:
        self.scheduled_exam_phone_call = ScheduledExamPhoneCallFactory()
        self.scheduled_exam_phone_call.scheduled_exam = self.scheduled_exam
        self.scheduled_exam_phone_call.save()

        # Creating prescription without suggested laboratories
        self.prescription_two = MedicalPrescriptionFactory()

        # Creating Patient without prescriptions
        self.patient_two = PatientFactory()
        self.patient_two.user = user_two
        self.patient_two.save()

        # Creating Exam Result/Details for prescription and exam one
        self.exam_result = ExamResultFactory()
        self.exam_result.scheduled_exam = self.scheduled_exam
        self.exam_result.save()

        self.exam_result_detail = ExamResultDetailFactory()
        self.exam_result_detail.exam_result = self.exam_result
        self.exam_result_detail.save()

    def test_get_api_200(self):
        """
        Tests GET (retrieve) API for status code 200.
        """
        url = reverse('mobile:prescription-detail', kwargs={'pk': self.prescription.id})
        response = self.client.get(url)
        data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Get prescription's scheduled exam
        scheduled_exam = data['scheduled_exams'][0]

        # self.assertEqual(data['insurance_plan_code'], self.prescription.insurance_plan_code)
        self.assertEqual(data['status'], self.prescription.status)
        self.assertEqual(data['doctor_crm'], self.prescription.doctor_crm)
        self.assertEqual(data['doctor_name'], self.prescription.doctor_name)
        # self.assertEqual(data['lab_file_code'], self.prescription.lab_file_code)
        self.assertIn('jpg', self.prescription.picture_insurance_card_front.url)
        self.assertIn('jpg', self.prescription.picture_insurance_card_back.url)
        self.assertIn('jpg', self.prescription.picture_prescription.url)
        self.assertEqual(data['patient_id'], self.prescription.patient.user.id)
        self.assertEqual(data['insurance_company_id'], self.prescription.insurance_company.id)

        self.assertEqual(scheduled_exam['laboratory']['id'], self.scheduled_exam.laboratory.id)
        self.assertEqual(scheduled_exam['exam']['id'], self.scheduled_exam.exam.id)

        scheduled_time_timestamp = int(parser.parse(self.scheduled_exam.scheduled_time).timestamp())
        self.assertEqual(scheduled_exam['scheduled_time_timestamp'], scheduled_time_timestamp)
        self.assertEqual(scheduled_exam['status'], self.scheduled_exam.status)
        self.assertEqual(scheduled_exam['procedure_average_duration'], self.scheduled_exam.procedure_average_duration)
        self.assertEqual(scheduled_exam['confirmation'], self.scheduled_exam.confirmation)
        self.assertEqual(scheduled_exam['suggested_labs_id'], [lab.id for lab in self.scheduled_exam.suggested_labs.all()])

    def test_get_api_404(self):
        """
        Tests GET (retrieve) API for status code 404.
        """
        url = reverse('mobile:prescription-detail', kwargs={'pk': 9999999999})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch('requests.get', mock_image_response)
    def test_put_api_200(self):
        """
        Tests PUT (update) API for status code 200.
        """
        User.objects.filter(username="user@email.com").delete()
        prescription = MedicalPrescriptionFactory()
        prescription.save()

        url = reverse('mobile:prescription-detail', kwargs={'pk': prescription.id})

        # JSON (payload)
        data = {
            # "insurance_plan_code": "102030",
            "status": MedicalPrescription.PATIENT_REQUESTED,
            "doctor_crm": "908070605040",
            # "lab_expected_time": 1488367860,
            # "lab_file_code": "12d33310503690",
            "patient_id": prescription.patient.user.id,
            # "laboratory_id": prescription.laboratory.id,
            "insurance_company_id": prescription.insurance_company.id,
            "picture_insurance_card_front": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "picture_insurance_card_back": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "picture_prescription": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "picture_insurance_card_front_uploadcare": "https://ucarecdn.com/e20532cd-bff1-43b4-8783-e55ee65b6312/8.png",
            "picture_insurance_card_back_uploadcare": "https://ucarecdn.com/e20532cd-bff1-43b4-8783-e55ee65b6312/8.png",
            "picture_prescription_uploadcare": "https://ucarecdn.com/e20532cd-bff1-43b4-8783-e55ee65b6312/8.png"
        }

        response = self.client.put(url, data=data, format="json")
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('id', data)
        # self.assertEqual(data['insurance_plan_code'], '102030')
        self.assertEqual(data['status'], MedicalPrescription.PATIENT_REQUESTED)
        self.assertEqual(data['doctor_crm'], '908070605040')
        # self.assertEqual(data['lab_expected_time'], 1488367860)
        # self.assertEqual(data['lab_file_code'], '12d33310503690')
        # self.assertEqual(data['patient']['user']['email'], prescription.patient.user.email)
        # self.assertEqual(data['laboratory_id'], prescription.laboratory.id)
        self.assertEqual(data['insurance_company_id'], prescription.insurance_company.id)
        self.assertIn('jpg', data['picture_insurance_card_front_url'])
        self.assertIn('ucarecdn', data['picture_insurance_card_front_uploadcare_url'])
        self.assertIn('jpg', data['picture_insurance_card_back_url'])
        self.assertIn('jpg', data['picture_prescription_url'])
        self.assertIn('jpg', data['picture_id_front_url'])
        self.assertIn('jpg', data['picture_id_back_url'])
        self.assertIn('jpg', data['selfie_url'])

    def test_put_api_200_partial(self):
        """
        Tests PUT (for partial update) API for status code 200.
        """
        User.objects.filter(username="user@email.com").delete()
        prescription = MedicalPrescriptionFactory()
        prescription.save()

        laboratory = LaboratoryFactory()
        laboratory.save()

        url = reverse('mobile:prescription-detail', kwargs={'pk': prescription.id})

        # JSON (payload)
        data = {
            "status": MedicalPrescription.EXAMS_IDENTIFIED,
            # "laboratory_id": laboratory.id,
        }

        response = self.client.put(url, data=data, format="json")
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('id', data)
        # self.assertEqual(data['insurance_plan_code'], prescription.insurance_plan_code)
        self.assertEqual(data['status'], MedicalPrescription.EXAMS_IDENTIFIED)
        self.assertEqual(data['doctor_crm'], prescription.doctor_crm)
        # self.assertEqual(data['lab_expected_time'], 1481110200)
        # self.assertEqual(data['lab_file_code'], prescription.lab_file_code)
        # self.assertEqual(data['patient']['user']['email'], prescription.patient.user.email)
        # self.assertEqual(data['laboratory_id'], laboratory.id)
        self.assertEqual(data['insurance_company_id'], prescription.insurance_company.id)
        self.assertIn('jpg', data['picture_insurance_card_front_url'])
        self.assertIn('jpg', data['picture_insurance_card_back_url'])
        self.assertIn('jpg', data['picture_prescription_url'])
        self.assertIn('jpg', data['picture_id_front_url'])
        self.assertIn('jpg', data['picture_id_back_url'])
        self.assertIn('jpg', data['selfie_url'])

    def test_put_api_no_prescription_id_400(self):
        """
        Tests PUT (update) API for status code 400.
        """
        User.objects.filter(username="user@email.com").delete()
        prescription = MedicalPrescriptionFactory()
        prescription.save()

        url = reverse('mobile:prescription-detail', kwargs={'pk': None})

        # JSON (payload)
        data = {
            # "insurance_plan_code": "102030",
            "status": MedicalPrescription.PATIENT_REQUESTED,
            "doctor_crm": "908070605040",
            # "lab_file_code": "12d33310503690",
            "insurance_company_id": prescription.insurance_company.id,
            "picture_insurance_card_front": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "picture_insurance_card_back": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "picture_prescription": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs="
        }

        response = self.client.put(url, data=data, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_put_api_invalid_prescription_id_404(self):
        """
        Tests PUT (update) API for status code 404.
        """
        User.objects.filter(username="user@email.com").delete()
        prescription = MedicalPrescriptionFactory()
        prescription.save()

        url = reverse('mobile:prescription-detail', kwargs={'pk': 99999999999999999})

        # JSON (payload)
        data = {
            # "insurance_plan_code": "102030",
            "status": MedicalPrescription.PATIENT_REQUESTED,
            "doctor_crm": "908070605040",
            # "lab_file_code": "12d33310503690",
            "insurance_company_id": prescription.insurance_company.id,
            "picture_insurance_card_front": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "picture_insurance_card_back": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "picture_prescription": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs="
        }

        response = self.client.put(url, data=data, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # def test_put_api_invalid_laboratory_id_400(self):
    #     """
    #     Tests PUT (update) API for status code 400.
    #     """
    #     User.objects.filter(username="user@email.com").delete()
    #     prescription = MedicalPrescriptionFactory()
    #     prescription.save()
    #
    #     url = reverse('mobile:prescription-detail', kwargs={'pk': prescription.id})
    #
    #     # JSON (payload)
    #     data = {
    #         "insurance_plan_code": "102033",
    #         "status": "ELIGIBLE_LAB",
    #         "doctor_crm": "908070605041",
    #         "lab_expected_time": 1488465490,
    #         "lab_file_code": "12d33310503691",
    #         "laboratory_id": 9999999999,
    #         "insurance_company_id": prescription.insurance_company.id,
    #         "exams_id": [self.exam_one.id, self.exam_two.id],
    #         "picture_insurance_card_front": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
    #         "picture_insurance_card_back": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
    #         "picture_prescription": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs="
    #     }
    #
    #     response = self.client.put(url, data=data, format="json")
    #
    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_put_api_invalid_insurance_company_id_400(self):
        """
        Tests PUT (update) API for status code 400.
        """
        User.objects.filter(username="user@email.com").delete()
        prescription = MedicalPrescriptionFactory()
        prescription.save()

        url = reverse('mobile:prescription-detail', kwargs={'pk': prescription.id})

        # JSON (payload)
        data = {
            # "insurance_plan_code": "102033",
            "status": "ELIGIBLE_PATIENT",
            "doctor_crm": "908070605041",
            # "lab_expected_time": 1488465490,
            # "lab_file_code": "12d33310503691",
            # "laboratory_id": prescription.laboratory.id,
            "insurance_company_id": 999999999,
            "picture_insurance_card_front": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "picture_insurance_card_back": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "picture_prescription": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs="
        }

        response = self.client.put(url, data=data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # def test_put_api_invalid_exam_id_400(self):
    #     """
    #     Tests PUT (update) API for status code 400.
    #     """
    #     User.objects.filter(username="user@email.com").delete()
    #     prescription = MedicalPrescriptionFactory()
    #     prescription.save()
    #
    #     url = reverse('mobile:prescription-detail', kwargs={'pk': prescription.id})
    #
    #     # JSON (payload)
    #     data = {
    #         "insurance_plan_code": "102033",
    #         "status": "ELIGIBLE_LAB",
    #         "doctor_crm": "908070605041",
    #         "lab_expected_time": 1488465490,
    #         "lab_file_code": "12d33310503691",
    #         "laboratory_id": prescription.laboratory.id,
    #         "insurance_company_id": prescription.insurance_company.id,
    #         "exams_id": [self.exam_one.id, 9999999999],
    #         "picture_insurance_card_front": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
    #         "picture_insurance_card_back": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
    #         "picture_prescription": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs="
    #     }
    #
    #     response = self.client.put(url, data=data, format="json")
    #
    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_api_no_patient_400(self):
        """
        Tests POST (create) API for status code 400.
        """
        url = reverse('mobile:prescription-list')

        # JSON (payload)
        data = {
            # "patient": {
            #     "user": self.patient_two.user.id,
            #     "preferred_laboratories_id": [self.laboratory.id],
            #     "picture_id_front": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            #     "picture_id_back": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            #     "selfie": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs="
            # },
            "picture_insurance_card_front": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "picture_prescription": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs="
        }

        response = self.client.post(url, data=data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_api_no_user_400(self):
        """
        Tests POST (create) API for status code 400.
        """
        url = reverse('mobile:prescription-list')

        # JSON (payload)
        data = {
            "patient": {
                # "user": self.patient_two,
                "preferred_laboratories_id": [self.laboratory.id],
                "picture_id_front": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
                "picture_id_back": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
                "selfie": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs="
            },
            "picture_insurance_card_front": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "picture_prescription": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs="
        }

        response = self.client.post(url, data=data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('requests.get', mock_image_response)
    def test_post_api_no_preferred_laboratories_201(self):
        """
        Tests POST (create) API for status code 201.
        """
        url = reverse('mobile:prescription-list')
        # JSON (payload)
        data = {
            "patient": {
                "user_id": self.patient_two.user.id,
                # "preferred_laboratories_id": self.laboratory.id,
                "picture_id_front": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
                "picture_id_back": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
                "selfie": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
                "picture_id_front_uploadcare": "https://ucarecdn.com/e20532cd-bff1-43b4-8783-e55ee65b6312/8.png",
                "picture_id_back_uploadcare": "https://ucarecdn.com/e20532cd-bff1-43b4-8783-e55ee65b6312/8.png",
                "selfie_uploadcare": "https://ucarecdn.com/e20532cd-bff1-43b4-8783-e55ee65b6312/8.png"
            },
            "picture_prescription": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "picture_prescription_uploadcare": "https://ucarecdn.com/e20532cd-bff1-43b4-8783-e55ee65b6312/8.png"
        }

        response = self.client.post(url, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_post_api_no_picture_id_front_400(self):
        """
        Tests POST (create) API for status code 400.
        """
        url = reverse('mobile:prescription-list')

        # JSON (payload)
        data = {
            "patient": {
                "user_id": self.patient_two.user.id,
                "preferred_laboratories_id": [self.laboratory.id],
                # "picture_id_front": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
                "picture_id_back": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
                "selfie": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs="
            },
            "picture_insurance_card_front": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "picture_prescription": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs="
        }

        response = self.client.post(url, data=data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_api_no_picture_id_back_400(self):
        """
        Tests POST (create) API for status code 400.
        """
        url = reverse('mobile:prescription-list')

        # JSON (payload)
        data = {
            "patient": {
                "user_id": self.patient_two.user.id,
                "preferred_laboratories_id": [self.laboratory.id],
                "picture_id_front": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
                # "picture_id_back": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
                "selfie": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs="
            },
            "picture_insurance_card_front": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "picture_prescription": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs="
        }

        response = self.client.post(url, data=data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_api_no_selfie_400(self):
        """
        Tests POST (create) API for status code 400.
        """
        url = reverse('mobile:prescription-list')

        # JSON (payload)
        data = {
            "patient": {
                "user_id": self.patient_two.user.id,
                "preferred_laboratories_id": [self.laboratory.id],
                "picture_id_front": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
                "picture_id_back": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
                # "selfie": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs="
            },
            "picture_insurance_card_front": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "picture_prescription": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs="
        }

        response = self.client.post(url, data=data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_api_no_picture_insurance_card_front_400(self):
        """
        Tests POST (create) API for status code 400.
        """
        url = reverse('mobile:prescription-list')

        # JSON (payload)
        data = {
            "patient": {
                "user_id": self.patient_two.user.id,
                "preferred_laboratories_id": [self.laboratory.id],
                "picture_id_front": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
                "picture_id_back": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
                "selfie": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs="
            },
            "picture_insurance_card_front": "",
            "picture_prescription": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs="
        }

        response = self.client.post(url, data=data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_api_no_picture_prescription_400(self):
        """
        Tests POST (create) API for status code 400.
        """
        url = reverse('mobile:prescription-list')

        # JSON (payload)
        data = {
            "patient": {
                "user_id": self.patient_two.user.id,
                "preferred_laboratories_id": [self.laboratory.id],
                "picture_id_front": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
                "picture_id_back": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
                "selfie": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs="
            },
            "picture_insurance_card_front": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            # "picture_prescription": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs="
        }

        response = self.client.post(url, data=data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('requests.get', mock_image_response)
    def test_post_api_no_picture_id_back_201(self):
        """
        Tests POST (create) API for status code 201.
        """
        url = reverse('mobile:prescription-list')

        # Creates a prescription for this user
        data = {
            "patient": {
                "user_id": self.patient.user.id,
                "preferred_laboratories_id": [self.laboratory.id],
                "picture_id_front": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
                "picture_id_back": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
                "selfie": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
                "picture_id_front_uploadcare": "https://ucarecdn.com/e20532cd-bff1-43b4-8783-e55ee65b6312/8.png",
                "picture_id_back_uploadcare": "https://ucarecdn.com/e20532cd-bff1-43b4-8783-e55ee65b6312/8.png",
                "selfie_uploadcare": "https://ucarecdn.com/e20532cd-bff1-43b4-8783-e55ee65b6312/8.png"
            },
            "picture_insurance_card_front": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "picture_prescription": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "picture_insurance_card_front_uploadcare": "https://ucarecdn.com/e20532cd-bff1-43b4-8783-e55ee65b6312/8.png",
            "picture_prescription_uploadcare": "https://ucarecdn.com/e20532cd-bff1-43b4-8783-e55ee65b6312/8.png"
        }
        self.client.post(url, data=data, format="json")

        # JSON (payload)
        # From now on picture_id_back is not required anymore.
        # It will be taken from the latest prescription.
        data = {
            "patient": {
                "user_id": self.patient.user.id,
                "preferred_laboratories_id": [self.laboratory.id],
                "picture_id_front": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
                # "picture_id_back": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
                "selfie": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
                "picture_id_front_uploadcare": "https://ucarecdn.com/e20532cd-bff1-43b4-8783-e55ee65b6312/8.png",
                # "picture_id_back_uploadcare": "https://ucarecdn.com/e20532cd-bff1-43b4-8783-e55ee65b6312/8.png",
                "selfie_uploadcare": "https://ucarecdn.com/e20532cd-bff1-43b4-8783-e55ee65b6312/8.png"
            },
            "picture_insurance_card_front": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "picture_prescription": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "picture_insurance_card_front_uploadcare": "https://ucarecdn.com/e20532cd-bff1-43b4-8783-e55ee65b6312/8.png",
            "picture_prescription_uploadcare": "https://ucarecdn.com/e20532cd-bff1-43b4-8783-e55ee65b6312/8.png"
        }

        response = self.client.post(url, data=data, format="json")
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertIn('id', data)
        self.assertIn('scheduled_exams', data)
        # self.assertIsNone(data['insurance_plan_code'])
        self.assertEqual(data['status'], MedicalPrescription.PATIENT_REQUESTED)
        self.assertIsNone(data['doctor_crm'])
        # self.assertIsNone(data['lab_file_code'])
        self.assertEqual(data['patient_id'], self.patient.user.id)
        self.assertIsNone(data['insurance_company_id'])
        self.assertIn('jpg', data['picture_insurance_card_front_url'])
        self.assertEqual('', data['picture_insurance_card_back_url'])
        self.assertIn('jpg', data['picture_prescription_url'])
        self.assertIn('jpg', data['picture_id_front_url'])
        self.assertIn('jpg', data['picture_id_back_url'])
        self.assertIn('jpg', data['selfie_url'])

    @patch('requests.get', mock_image_response)
    def test_post_api_no_selfie_201(self):
        """
        Tests POST (create) API for status code 201.
        """
        url = reverse('mobile:prescription-list')

        # Creates a prescription for this user
        data = {
            "patient": {
                "user_id": self.patient.user.id,
                "preferred_laboratories_id": [self.laboratory.id],
                "picture_id_front": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
                "picture_id_back": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
                "selfie": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
                "picture_id_front_uploadcare": "https://ucarecdn.com/e20532cd-bff1-43b4-8783-e55ee65b6312/8.png",
                "picture_id_back_uploadcare": "https://ucarecdn.com/e20532cd-bff1-43b4-8783-e55ee65b6312/8.png",
                "selfie_uploadcare": "https://ucarecdn.com/e20532cd-bff1-43b4-8783-e55ee65b6312/8.png"
            },
            "picture_insurance_card_front": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "picture_prescription": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "picture_insurance_card_front_uploadcare": "https://ucarecdn.com/e20532cd-bff1-43b4-8783-e55ee65b6312/8.png",
            "picture_prescription_uploadcare": "https://ucarecdn.com/e20532cd-bff1-43b4-8783-e55ee65b6312/8.png",
        }
        self.client.post(url, data=data, format="json")

        # JSON (payload)
        # From now on selfie is not required anymore.
        # It will be taken from the latest prescription.
        data = {
            "patient": {
                "user_id": self.patient.user.id,
                "preferred_laboratories_id": [self.laboratory.id],
                "picture_id_front": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
                "picture_id_back": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
                # "selfie": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
                "picture_id_front_uploadcare": "https://ucarecdn.com/e20532cd-bff1-43b4-8783-e55ee65b6312/8.png",
                "picture_id_back_uploadcare": "https://ucarecdn.com/e20532cd-bff1-43b4-8783-e55ee65b6312/8.png",
                # "selfie_uploadcare": "https://ucarecdn.com/e20532cd-bff1-43b4-8783-e55ee65b6312/8.png"
            },
            "picture_insurance_card_front": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "picture_prescription": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "picture_insurance_card_front_uploadcare": "https://ucarecdn.com/e20532cd-bff1-43b4-8783-e55ee65b6312/8.png",
            "picture_prescription_uploadcare": "https://ucarecdn.com/e20532cd-bff1-43b4-8783-e55ee65b6312/8.png",
        }

        response = self.client.post(url, data=data, format="json")
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertIn('id', data)
        self.assertIn('scheduled_exams', data)
        # self.assertIsNone(data['insurance_plan_code'])
        self.assertEqual(data['status'], MedicalPrescription.PATIENT_REQUESTED)
        self.assertIsNone(data['doctor_crm'])
        # self.assertIsNone(data['lab_file_code'])
        self.assertEqual(data['patient_id'], self.patient.user.id)
        self.assertIsNone(data['insurance_company_id'])
        self.assertIn('jpg', data['picture_insurance_card_front_url'])
        self.assertEqual('', data['picture_insurance_card_back_url'])
        self.assertIn('jpg', data['picture_prescription_url'])
        self.assertIn('jpg', data['picture_id_front_url'])
        self.assertIn('jpg', data['picture_id_back_url'])
        self.assertIn('jpg', data['selfie_url'])

    @patch('requests.get', mock_image_response)
    def test_post_api_no_picture_id_front_201(self):
        """
        Tests POST (create) API for status code 201.
        """
        url = reverse('mobile:prescription-list')

        # Creates a prescription for this user
        data = {
            "patient": {
                "user_id": self.patient.user.id,
                "preferred_laboratories_id": [self.laboratory.id],
                "picture_id_front": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
                "picture_id_back": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
                "selfie": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
                "picture_id_front_uploadcare": "https://ucarecdn.com/e20532cd-bff1-43b4-8783-e55ee65b6312/8.png",
                "picture_id_back_uploadcare": "https://ucarecdn.com/e20532cd-bff1-43b4-8783-e55ee65b6312/8.png",
                "selfie_uploadcare": "https://ucarecdn.com/e20532cd-bff1-43b4-8783-e55ee65b6312/8.png"
            },
            "picture_insurance_card_front": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "picture_prescription": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "picture_insurance_card_front_uploadcare": "https://ucarecdn.com/e20532cd-bff1-43b4-8783-e55ee65b6312/8.png",
            "picture_prescription_uploadcare": "https://ucarecdn.com/e20532cd-bff1-43b4-8783-e55ee65b6312/8.png",
        }
        self.client.post(url, data=data, format="json")

        # JSON (payload)
        # From now on picture_id_front is not required anymore.
        # It will be taken from the latest prescription.
        data = {
            "patient": {
                "user_id": self.patient.user.id,
                "preferred_laboratories_id": [self.laboratory.id],
                # "picture_id_front": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
                "picture_id_back": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
                "selfie": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
                # "picture_id_front_uploadcare": "https://ucarecdn.com/e20532cd-bff1-43b4-8783-e55ee65b6312/8.png",
                "picture_id_back_uploadcare": "https://ucarecdn.com/e20532cd-bff1-43b4-8783-e55ee65b6312/8.png",
                "selfie_uploadcare": "https://ucarecdn.com/e20532cd-bff1-43b4-8783-e55ee65b6312/8.png"
            },
            "picture_insurance_card_front": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "picture_prescription": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "picture_insurance_card_front_uploadcare": "https://ucarecdn.com/e20532cd-bff1-43b4-8783-e55ee65b6312/8.png",
            "picture_prescription_uploadcare": "https://ucarecdn.com/e20532cd-bff1-43b4-8783-e55ee65b6312/8.png"
        }

        response = self.client.post(url, data=data, format="json")
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertIn('id', data)
        self.assertIn('scheduled_exams', data)
        # self.assertIsNone(data['insurance_plan_code'])
        self.assertEqual(data['status'], MedicalPrescription.PATIENT_REQUESTED)
        self.assertIsNone(data['doctor_crm'])
        # self.assertIsNone(data['lab_file_code'])
        self.assertEqual(data['patient_id'], self.patient.user.id)
        self.assertIsNone(data['insurance_company_id'])
        self.assertIn('jpg', data['picture_insurance_card_front_url'])
        self.assertEqual('', data['picture_insurance_card_back_url'])
        self.assertIn('jpg', data['picture_prescription_url'])
        self.assertIn('jpg', data['picture_id_front_url'])
        self.assertIn('jpg', data['picture_id_back_url'])
        self.assertIn('jpg', data['selfie_url'])

    @patch('requests.get', mock_image_response)
    def test_post_api_no_picture_insurance_card_front_201(self):
        """
        Tests POST (create) API for status code 201.
        """
        url = reverse('mobile:prescription-list')

        # Creates a prescription for this user
        data = {
            "patient": {
                "user_id": self.patient.user.id,
                "preferred_laboratories_id": [self.laboratory.id],
                "picture_id_front": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
                "picture_id_back": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
                "selfie": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
                "picture_id_front_uploadcare": "https://ucarecdn.com/e20532cd-bff1-43b4-8783-e55ee65b6312/8.png",
                "picture_id_back_uploadcare": "https://ucarecdn.com/e20532cd-bff1-43b4-8783-e55ee65b6312/8.png",
                "selfie_uploadcare": "https://ucarecdn.com/e20532cd-bff1-43b4-8783-e55ee65b6312/8.png"
            },
            "picture_insurance_card_front": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "picture_prescription": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "picture_insurance_card_front_uploadcare": "https://ucarecdn.com/e20532cd-bff1-43b4-8783-e55ee65b6312/8.png",
            "picture_prescription_uploadcare": "https://ucarecdn.com/e20532cd-bff1-43b4-8783-e55ee65b6312/8.png",
        }
        self.client.post(url, data=data, format="json")

        # JSON (payload)
        # From now on picture_insurance_card_front is not required anymore.
        # It will be taken from the latest prescription.
        data = {
            "patient": {
                "user_id": self.patient.user.id,
                "preferred_laboratories_id": [self.laboratory.id],
                "picture_id_front": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
                "picture_id_back": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
                "selfie": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
                "picture_id_front_uploadcare": "https://ucarecdn.com/e20532cd-bff1-43b4-8783-e55ee65b6312/8.png",
                "picture_id_back_uploadcare": "https://ucarecdn.com/e20532cd-bff1-43b4-8783-e55ee65b6312/8.png",
                "selfie_uploadcare": "https://ucarecdn.com/e20532cd-bff1-43b4-8783-e55ee65b6312/8.png"
            },
            # "picture_insurance_card_front": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "picture_prescription": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            # "picture_insurance_card_front_uploadcare": "https://ucarecdn.com/e20532cd-bff1-43b4-8783-e55ee65b6312/8.png",
            "picture_prescription_uploadcare": "https://ucarecdn.com/e20532cd-bff1-43b4-8783-e55ee65b6312/8.png",
        }

        response = self.client.post(url, data=data, format="json")
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertIn('id', data)
        self.assertIn('scheduled_exams', data)
        # self.assertIsNone(data['insurance_plan_code'])
        self.assertEqual(data['status'], MedicalPrescription.PATIENT_REQUESTED)
        self.assertIsNone(data['doctor_crm'])
        # self.assertIsNone(data['lab_file_code'])
        self.assertEqual(data['patient_id'], self.patient.user.id)
        self.assertIsNone(data['insurance_company_id'])
        self.assertIn('jpg', data['picture_insurance_card_front_url'])
        self.assertEqual('', data['picture_insurance_card_back_url'])
        self.assertIn('jpg', data['picture_prescription_url'])
        self.assertIn('jpg', data['picture_id_front_url'])
        self.assertIn('jpg', data['picture_id_back_url'])
        self.assertIn('jpg', data['selfie_url'])

    def test_post_api_no_picture_prescription_400_again(self):
        """
        Tests POST (create) API for status code 400.
        """
        url = reverse('mobile:prescription-list')

        # Creates a prescription for this user
        data = {
            "patient": {
                "user_id": self.patient.user.id,
                "preferred_laboratories_id": [self.laboratory.id],
                "picture_id_front": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
                "picture_id_back": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
                "selfie": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs="
            },
            "picture_insurance_card_front": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "picture_prescription": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs="
        }
        self.client.post(url, data=data, format="json")

        # JSON (payload)
        # Even creating a prescription before, picture_prescription is still necessary.
        data = {
            "patient": {
                "user_id": self.patient.user.id,
                "preferred_laboratories_id": [self.laboratory.id],
                "picture_id_front": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
                "picture_id_back": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
                "selfie": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs="
            },
            "picture_insurance_card_front": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            # "picture_prescription": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs="
        }

        response = self.client.post(url, data=data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('picture_prescription', response.json())

    def test_post_api_invalid_patient_400(self):
        """
        Tests POST (create) API for status code 400.
        """
        url = reverse('mobile:prescription-list')

        # JSON (payload)
        data = {
            "patient": self.patient.user.id,  # it must be object, not id.
            "picture_insurance_card_front": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "picture_prescription": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs="
        }

        response = self.client.post(url, data=data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_api_invalid_user_400(self):
        """
        Tests POST (create) API for status code 400.
        """
        url = reverse('mobile:prescription-list')

        # JSON (payload)
        data = {
            "patient": {
                "user_id": 999999999,  # invalid user id
                "preferred_laboratories_id": [self.laboratory.id],
                "picture_id_front": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
                "picture_id_back": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
                "selfie": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs="
            },
            "picture_insurance_card_front": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "picture_prescription": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs="
        }

        response = self.client.post(url, data=data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_api_invalid_preferred_laboratories_400(self):
        """
        Tests POST (create) API for status code 400.
        """
        url = reverse('mobile:prescription-list')

        # JSON (payload)
        data = {
            "patient": {
                "user_id": self.patient.user.id,
                "preferred_laboratories_id": [999999999],  # invalid laboratory id
                "picture_id_front": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
                "picture_id_back": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
                "selfie": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs="
            },
            "picture_insurance_card_front": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "picture_prescription": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs="
        }

        response = self.client.post(url, data=data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_api_invalid_picture_id_front_400(self):
        """
        Tests POST (create) API for status code 400.
        """
        url = reverse('mobile:prescription-list')

        # JSON (payload)
        data = {
            "patient": {
                "user_id": self.patient.user.id,
                "preferred_laboratories_id": [self.laboratory.id],
                "picture_id_front": "XXX",  # invalid base64
                "picture_id_back": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
                "selfie": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs="
            },
            "picture_insurance_card_front": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "picture_prescription": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs="
        }

        response = self.client.post(url, data=data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_api_invalid_picture_id_back_400(self):
        """
        Tests POST (create) API for status code 400.
        """
        url = reverse('mobile:prescription-list')

        # JSON (payload)
        data = {
            "patient": {
                "user_id": self.patient.user.id,
                "preferred_laboratories_id": [self.laboratory.id],
                "picture_id_front": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
                "picture_id_back": "XXX",  # invalid base64
                "selfie": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs="
            },
            "picture_insurance_card_front": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "picture_prescription": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs="
        }

        response = self.client.post(url, data=data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_api_invalid_selfie_400(self):
        """
        Tests POST (create) API for status code 400.
        """
        url = reverse('mobile:prescription-list')

        # JSON (payload)
        data = {
            "patient": {
                "user_id": self.patient.user.id,
                "preferred_laboratories_id": [self.laboratory.id],
                "picture_id_front": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
                "picture_id_back": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
                "selfie": "XXX"  # invalid base64
            },
            "picture_insurance_card_front": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "picture_prescription": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs="
        }

        response = self.client.post(url, data=data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_api_invalid_picture_insurance_card_front_400(self):
        """
        Tests POST (create) API for status code 400.
        """
        url = reverse('mobile:prescription-list')

        # JSON (payload)
        data = {
            "patient": {
                "user_id": self.patient.user.id,
                "preferred_laboratories_id": [self.laboratory.id],
                "picture_id_front": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
                "picture_id_back": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
                "selfie": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs="
            },
            "picture_insurance_card_front": "XXX",  # invalid base64
            "picture_prescription": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs="
        }

        response = self.client.post(url, data=data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_api_invalid_picture_prescription_400(self):
        """
        Tests POST (create) API for status code 400.
        """
        url = reverse('mobile:prescription-list')

        # JSON (payload)
        data = {
            "patient": {
                "user_id": self.patient.user.id,
                "preferred_laboratories_id": [self.laboratory.id],
                "picture_id_front": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
                "picture_id_back": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
                "selfie": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs="
            },
            "picture_insurance_card_front": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "picture_prescription": "XXX"  # invalid base64
        }

        response = self.client.post(url, data=data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # def test_get_suggested_laboratories_400(self):
    #     """
    #     Tests GET (retrieve) API for status code 400.
    #     """
    #     url = reverse('mobile:prescription-suggested-labs', kwargs={'pk': 99999999999})
    #     response = self.client.get(url)
    #
    #     self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    #
    # def test_get_suggested_laboratories_403(self):
    #     """
    #     Tests GET (retrieve) API for status code 403.
    #     Logged auth user is different from the one who owns the prescription
    #     """
    #     # Logged user owns only prescription_one
    #     url = reverse('mobile:prescription-suggested-labs', kwargs={'pk': self.prescription_two.id})
    #     response = self.client.get(url)
    #
    #     self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # def test_get_suggested_laboratories_404(self):
    #     """
    #     Tests GET (retrieve) API for status code 404.
    #     """
    #     self.prescription_two.patient = self.patient_two
    #     self.prescription_two.save()
    #
    #     self.client.login(username='stewart2', password='secret2')
    #
    #     url = reverse('mobile:prescription-suggested-labs', kwargs={'pk': self.prescription_two.id})
    #     response = self.client.get(url)
    #
    #     self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch('requests.get', mock_image_response)
    def test_post_api_201(self):
        """
        Tests POST (create) API for status code 201.
        """
        url = reverse('mobile:prescription-list')

        # JSON (payload)
        data = {
            "patient": {
                "user_id": self.patient.user.id,
                "preferred_laboratories_id": [self.laboratory.id],
                "picture_id_front": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
                "picture_id_back": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
                "selfie": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
                "picture_id_front_uploadcare": "https://ucarecdn.com/e20532cd-bff1-43b4-8783-e55ee65b6312/8.png",
                "picture_id_back_uploadcare": "https://ucarecdn.com/e20532cd-bff1-43b4-8783-e55ee65b6312/8.png",
                "selfie_uploadcare": "https://ucarecdn.com/e20532cd-bff1-43b4-8783-e55ee65b6312/8.png"
            },
            "picture_insurance_card_front": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "picture_prescription": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "picture_insurance_card_front_uploadcare": "https://ucarecdn.com/e20532cd-bff1-43b4-8783-e55ee65b6312/8.png",
            "picture_prescription_uploadcare": "https://ucarecdn.com/e20532cd-bff1-43b4-8783-e55ee65b6312/8.png",
        }

        response = self.client.post(url, data=data, format="json")
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertIn('id', data)
        # self.assertIsNone(data['insurance_plan_code'])
        self.assertEqual(data['status'], MedicalPrescription.PATIENT_REQUESTED)
        self.assertIsNone(data['doctor_crm'])
        # self.assertIsNone(data['lab_expected_time'])
        # self.assertIsNone(data['lab_file_code'])
        self.assertEqual(data['patient_id'], self.patient.user.id)
        # self.assertEqual(data['laboratory_id'], self.laboratory.id)
        self.assertIsNone(data['insurance_company_id'])
        # self.assertEqual(data['exams_id'], [])
        self.assertIn('jpg', data['picture_insurance_card_front_url'])
        self.assertEqual('', data['picture_insurance_card_back_url'])
        self.assertIn('jpg', data['picture_prescription_url'])
        self.assertIn('jpg', data['picture_id_front_url'])
        self.assertIn('jpg', data['picture_id_back_url'])
        self.assertIn('jpg', data['selfie_url'])

    @patch('requests.get', mock_image_response)
    def test_post_api_no_preferred_laboratories_201(self):
        """
        Tests POST (create) API for status code 201.
        """
        url = reverse('mobile:prescription-list')

        # Creates a prescription for this user
        data = {
            "patient": {
                "user_id": self.patient.user.id,
                "preferred_laboratories_id": [self.laboratory.id],
                "picture_id_front": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
                "picture_id_back": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
                "selfie": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
                "picture_id_front_uploadcare": "https://ucarecdn.com/e20532cd-bff1-43b4-8783-e55ee65b6312/8.png",
                "picture_id_back_uploadcare": "https://ucarecdn.com/e20532cd-bff1-43b4-8783-e55ee65b6312/8.png",
                "selfie_uploadcare": "https://ucarecdn.com/e20532cd-bff1-43b4-8783-e55ee65b6312/8.png"
            },
            "picture_prescription": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "picture_prescription_uploadcare": "https://ucarecdn.com/e20532cd-bff1-43b4-8783-e55ee65b6312/8.png",
            "picture_insurance_card_front": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "picture_insurance_card_front_uploadcare": "https://ucarecdn.com/e20532cd-bff1-43b4-8783-e55ee65b6312/8.png"

        }
        self.client.post(url, data=data, format="json")

        # JSON (payload)
        # From now on preferred_laboratories_id is not required anymore.
        # It will be taken from the latest prescription.
        data = {
            "patient": {
                "user_id": self.patient.user.id,
                # "preferred_laboratories_id": [self.laboratory.id],
                "picture_id_front": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
                "picture_id_back": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
                "selfie": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
                "picture_id_front_uploadcare": "https://ucarecdn.com/e20532cd-bff1-43b4-8783-e55ee65b6312/8.png",
                "picture_id_back_uploadcare": "https://ucarecdn.com/e20532cd-bff1-43b4-8783-e55ee65b6312/8.png",
                "selfie_uploadcare": "https://ucarecdn.com/e20532cd-bff1-43b4-8783-e55ee65b6312/8.png"
            },
            "picture_prescription": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "picture_prescription_uploadcare": "https://ucarecdn.com/e20532cd-bff1-43b4-8783-e55ee65b6312/8.png"
        }

        response = self.client.post(url, data=data, format="json")
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertIn('id', data)
        # self.assertIsNone(data['insurance_plan_code'])
        self.assertEqual(data['status'], MedicalPrescription.PATIENT_REQUESTED)
        self.assertIsNone(data['doctor_crm'])
        # self.assertIsNone(data['lab_expected_time'])
        # self.assertIsNone(data['lab_file_code'])
        self.assertEqual(data['patient_id'], self.patient.user.id)
        # self.assertEqual(data['laboratory_id'], self.laboratory.id)
        self.assertIsNone(data['insurance_company_id'])
        # self.assertEqual(data['exams_id'], [])
        self.assertIn('jpg', data['picture_insurance_card_front_url'])
        self.assertEqual('', data['picture_insurance_card_back_url'])
        self.assertIn('jpg', data['picture_prescription_url'])
        self.assertIn('jpg', data['picture_id_front_url'])
        self.assertIn('jpg', data['picture_id_back_url'])
        self.assertIn('jpg', data['selfie_url'])

    def test_get_prescriptions_by_patient_200(self):
        """
        Tests GET (retrieve) prescriptions by patient for status code 200.
        Patient exists and has prescriptions.
        :return:
        """
        # Creates a prescription for this user
        prescription = MedicalPrescriptionFactory()
        prescription.patient = self.patient
        prescription.save()

        # Creates a scheduled exam within the prescription
        schedule_exam = ScheduledExamFactory()
        schedule_exam.exam = self.exam_one
        schedule_exam.prescription = prescription
        schedule_exam.save()

        url = reverse('mobile:patient-prescriptions', kwargs={'pk': self.patient.user.id})
        response = self.client.get(url)
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data_patient = data['patient']
        data_prescription = data['prescriptions'][0]
        data_scheduled_exams = data_prescription['scheduled_exams'][0]

        self.assertEqual(data_prescription['id'], prescription.id)
        self.assertIn('created_timestamp', data_prescription)
        # self.assertEqual(data_prescription['insurance_plan_code'], prescription.insurance_plan_code)
        self.assertEqual(data_prescription['status'], prescription.status)
        self.assertEqual(data_prescription['doctor_crm'], prescription.doctor_crm)
        # self.assertEqual(data_prescription['lab_file_code'], prescription.lab_file_code)
        self.assertEqual(data_prescription['insurance_company_id'], prescription.insurance_company.id)
        # self.assertEqual(data_prescription['plan_product_code'], prescription.plan_product_code)
        self.assertIn('status_versions', data_prescription)

        self.assertEqual(data_scheduled_exams['laboratory']['brand_name'], self.laboratory.brand.name)
        self.assertEqual(data_scheduled_exams['laboratory']['description'], self.laboratory.description)
        self.assertEqual(data_scheduled_exams['laboratory']['address']['street'], self.laboratory.street)
        # self.assertEqual(data_scheduled_exams['laboratory']['coordinates']['lat'], self.laboratory.point[1])
        # self.assertEqual(data_scheduled_exams['laboratory']['coordinates']['lng'], self.laboratory.point[0])

        self.assertEqual(data_patient['user']['email'], self.patient.user.email)

        self.assertEqual(data_scheduled_exams['exam']['id'], self.exam_one.id)

        self.assertEqual(data_scheduled_exams['suggested_labs_id'], [])
        self.assertIsNone(data_scheduled_exams['procedure_average_duration'])

    def test_get_preparation_steps_200(self):
        """
        Tests GET (list) preparation steps  for status code 200.
        :return:
        """
        self.prescription.patient = self.patient
        self.prescription.laboratory = self.laboratory
        self.prescription.save()

        url = reverse('mobile:prescription-preparation-steps', kwargs={'pk': self.prescription.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()[0][0]
        self.assertEquals(data["title"], "Fasting")
        self.assertEquals(data["description"], "Patient can't eat for the next 24 hours")
        self.assertFalse(data["is_mandatory"])
        self.assertEquals(data["exam_id"], self.exam_one.id)

    def test_get_preparation_steps_404(self):
        """
        Tests GET (list) preparation steps  for status code 404.
        :return:
        """
        self.prescription.patient = self.patient
        self.prescription.save()
        self.scheduled_exam.exam = self.exam_two
        self.scheduled_exam.save()

        url = reverse('mobile:prescription-preparation-steps', kwargs={'pk': self.prescription.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_preparation_steps_200_no_laboratory(self):
        """
        Tests GET (list) preparation steps  for status code 200.
        :return:
        """
        self.prescription.patient = self.patient
        self.scheduled_exam.laboratory = None
        self.prescription.save()

        url = reverse('mobile:prescription-preparation-steps', kwargs={'pk': self.prescription.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_preparation_steps_403(self):
        """
        Tests GET (retrieve) API for status code 403.
        Logged auth user is different from the one who owns the prescription
        """
        # Logged user owns only prescription_one
        url = reverse('mobile:prescription-preparation-steps', kwargs={'pk': self.prescription_two.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # def test_get_exams_result_200(self):
    #     """
    #     Tests GET (list) exams result for status code 200.
    #     :return:
    #     """
    #     self.prescription.patient = self.patient
    #     self.prescription.save()
    #
    #     url = reverse('mobile:prescription-exams-result', kwargs={'pk': self.prescription.id})
    #     response = self.client.get(url)
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    #
    #     data = response.json()[0]
    #     self.assertEquals(data["exam_id"], self.exam_one.id)
    #     self.assertIn("jpg", data["file_url"])
    #
    #     self.assertIn("exam_result_details", data)
    #     exam_result_details = data["exam_result_details"][0]
    #     self.assertEquals(exam_result_details["title"], "")
    #     self.assertEquals(exam_result_details["description"], "Glicose")
    #     self.assertEquals(exam_result_details["result"], "10mg")
    #     self.assertEquals(exam_result_details["reference_values"], "5mg - 10mg")
    #
    # def test_get_exams_result_404(self):
    #     """
    #     Tests GET (list) exams result for status code 404.
    #     :return:
    #     """
    #     self.prescription_two.patient = self.patient_two
    #     self.prescription_two.save()
    #     self.client.login(username='stewart2', password='secret2')
    #
    #     url = reverse('mobile:prescription-exams-result', kwargs={'pk': self.prescription_two.id})
    #     response = self.client.get(url)
    #     self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    #
    # def test_get_exams_result_403(self):
    #     """
    #     Tests GET (retrieve) API for status code 403.
    #     Logged auth user is different from the one who owns the prescription
    #     """
    #     # Logged user owns only prescription_one
    #     url = reverse('mobile:prescription-exams-result', kwargs={'pk': self.prescription_two.id})
    #     response = self.client.get(url)
    #
    #     self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_scheduled_exams_200(self):
        """
        Tests GET (list) scheduled exams for status code 200.
        :return:
        """
        self.prescription.patient = self.patient
        self.prescription.save()

        url = reverse('mobile:prescription-scheduled-exams', kwargs={'pk': self.prescription.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()[0]
        self.assertEquals(data["exam"]["id"], self.exam_one.id)
        self.assertEquals(data["exam"]["name"], self.exam_one.name)
        self.assertEquals(data["exam"]["description"], self.exam_one.description)

        self.assertEquals(data["laboratory"]["id"], self.laboratory.id)
        self.assertEquals(data["laboratory"]["brand_name"], self.laboratory.brand.name)
        self.assertIn("address", data["laboratory"])
        self.assertIn("coordinates", data["laboratory"])

        self.assertEquals(data["status"], self.scheduled_exam.status)
        self.assertEquals(data["procedure_average_duration"], self.scheduled_exam.procedure_average_duration)
        self.assertEquals(data["confirmation"], self.scheduled_exam.confirmation)
        self.assertEquals(data["suggested_labs_id"], [lab.id for lab in self.scheduled_exam.suggested_labs.all()])
        scheduled_time_timestamp = int(parser.parse(self.scheduled_exam.scheduled_time).timestamp())
        self.assertEquals(data["scheduled_time_timestamp"], scheduled_time_timestamp)

        phone_call = data["scheduled_exam_phone_call"]
        self.assertEquals(phone_call["id"], self.scheduled_exam_phone_call.id)
        self.assertEquals(phone_call["phone"], self.scheduled_exam_phone_call.phone)
        phone_call_timestamp = int(self.scheduled_exam_phone_call.call_time.timestamp())
        self.assertEquals(phone_call["call_time_timestamp"], phone_call_timestamp)

    def test_get_scheduled_exams_404(self):
        """
        Tests GET (list)scheduled exams for status code 404.
        :return:
        """
        self.prescription_two.patient = self.patient_two
        self.prescription_two.save()
        self.client.login(username='stewart2', password='secret2')

        url = reverse('mobile:prescription-scheduled-exams', kwargs={'pk': self.prescription_two.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_scheduled_exams_403(self):
        """
        Tests GET (retrieve) API for status code 403.
        Logged auth user is different from the one who owns the prescription
        """
        # Logged user owns only prescription_one
        url = reverse('mobile:prescription-scheduled-exams', kwargs={'pk': self.prescription_two.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
