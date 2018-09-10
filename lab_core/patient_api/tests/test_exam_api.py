# encode: utf-8

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from domain.tests.factory_models import ExamFactory


class ExamMobileAPITests(APITestCase):

    def setUp(self):
        """
        Setting up things before tests.
        :return:
        """
        # Getting authenticated for the next requests.
        User.objects.create_user('lab', 'lab@roundpe.gs', password='secret')
        self.client.login(username='lab', password='secret')

        # Creating Laboratory.
        self.exam = ExamFactory()

    def test_get_api_200_list(self):
        """
        Tests GET (retrieve) API for status code 200.
        """
        url = reverse('mobile:exam-list')
        response = self.client.get(url)
        data = response.json()

        self.assertIn('results', data)

        exam_data = data['results'][0]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(exam_data['id'], self.exam.id)
        self.assertEqual(exam_data['external_id'], self.exam.external_id)
        self.assertEqual(exam_data['description'], self.exam.description)
        self.assertEqual(exam_data['name'], self.exam.name)
        self.assertEqual(exam_data['synonymy'], self.exam.synonymy)
        self.assertEqual(exam_data['exam_type'], self.exam.exam_type)

    def test_get_api_200_retrieve(self):
        """
        Tests GET (retrieve) API for status code 200.
        """
        url = reverse('mobile:exam-detail', kwargs={'pk': self.exam.id})
        response = self.client.get(url)
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data['id'], self.exam.id)
        self.assertEqual(data['external_id'], self.exam.external_id)
        self.assertEqual(data['description'], self.exam.description)
        self.assertEqual(data['name'], self.exam.name)
        self.assertEqual(data['synonymy'], self.exam.synonymy)
        self.assertEqual(data['exam_type'], self.exam.exam_type)

    def test_get_api_invalid_pk_404(self):
        """
        Tests GET (retrieve) API for status code 404.
        """
        url = reverse('mobile:exam-detail', kwargs={'pk': 9999999999})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
