# encode: utf-8

import dotmap
import factory
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from domain.tests.factory_models import (ExamFactory,
                                         MedicalPrescriptionFactory,
                                         PatientFactory,
                                         ScheduledExamFactory)
from domain.utils import disable_signals

# TODO: create all the tests

# class UserFactory(factory.DjangoModelFactory):
#     class Meta:
#         model = User
#
#     username = "john"
#     password = "xapianoi1@#_Z"
#     email = 'john@example.com'
#
#
# class OperatorTest(TestCase):
#     def test_operator_has_user(self):
#         op = OperatorFactory()
#         self.assertIsNotNone(op.user)
#         self.assertEqual("john", op.user.username)
#
#
# class BackOfficeTest(TestCase):
#     def setUp(self):
#         # Disabling push notifications signal and firebase sync tasks.
#         disable_signals()
#
#         # Getting authenticated for the next requests.
#         user = User.objects.create_user('john', 'doe@roundpe.gs', password='secret')
#         self.client.login(username='john', password='secret')
#         self.operator = OperatorFactory(user=user)
#
#     def test_operator(self):
#         url = reverse('concierge:operator-detail', kwargs={'pk': self.operator.pk})
#         response = self.client.get(url)
#
#         self.assertEqual(response.status_code, 200)
#
#         body = dotmap.DotMap(response.json())
#         self.assertEqual(self.operator.user.username, body.user.username)
#         self.assertEqual('J', body.abbreviation)
#
#     def test_load_patient(self):
#         patient = PatientFactory()
#         url = reverse('concierge:patient-detail', kwargs={'pk': patient.pk})
#
#         response = self.client.get(url)
#         self.assertEqual(200, response.status_code)
#
#         body = dotmap.DotMap(response.json())
#
#         self.assertEqual('user lastname', body.full_name)
#
#     def test_load_prescription(self):
#         prescription = MedicalPrescriptionFactory()
#         scheduled_exam = ScheduledExamFactory()
#         scheduled_exam.prescription = prescription
#         scheduled_exam.save()
#
#         url = reverse('concierge:medicalprescription-detail', kwargs={'pk': prescription.pk})
#
#         response = self.client.get(url)
#         self.assertEqual(200, response.status_code)
#
#         body = dotmap.DotMap(response.json())
#
#         self.assertEqual(body.doctor_crm, prescription.doctor_crm)
#         self.assertEqual(body.patient, prescription.patient.pk)
#         self.assertEqual(body.scheduled_exams[0].exam.name, scheduled_exam.exam.name)
#
#     def test_filter_exam(self):
#         exam = ExamFactory()
#         url = reverse("concierge:exam-list")
#         response = self.client.get(url + '?name=111')
#
#         self.assertEqual(200, response.status_code)
#         body = dotmap.DotMap(response.json())
#
#         self.assertEqual(body.results[0].name, exam.name)
