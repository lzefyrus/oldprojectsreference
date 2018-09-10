# encode: utf-8

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from domain.tests.factory_models import PatientFactory


class TestAuthenticateUser(APITestCase):

    USERNAME = 'john'
    EMAIL = 'doe@roundpe.gs'
    PASSWORD = 'secret'

    def setUp(self):
        self.user = User.objects.create_user(self.USERNAME, self.EMAIL, password=self.PASSWORD)
        self.patient = PatientFactory()
        self.patient.user = self.user
        self.patient.save()

        self.user_2 = User.objects.create_user("test", "any@email.com", password="secretagain")
        self.patient_2 = PatientFactory()
        self.patient_2.user = self.user_2
        self.patient_2.save()

    def test_200(self):
        """
        Tests successful user authentication
        """
        # get token
        response = self.client.post(path=reverse('token'),
                                    data={'username': self.USERNAME, 'password': self.PASSWORD})
        data = response.json()
        token = data['token']

        # send request
        url = reverse('mobile:patient-detail', kwargs={'pk': self.patient.user.id})
        response = self.client.get(url, HTTP_AUTHORIZATION='Token {0}'.format(token))

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_403(self):
        """
        Tests forbidden user authentication
        """

        # get first user token
        response = self.client.post(path=reverse('token'),
                                    data={'username': self.USERNAME, 'password': self.PASSWORD})
        data = response.json()
        token = data['token']

        # send request to retrieve the second user using the wrong token
        url = reverse('mobile:patient-detail', kwargs={'pk': self.patient_2.user.id})
        response = self.client.get(url, HTTP_AUTHORIZATION='Token {0}'.format(token))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # TODO: return this when email confirmation becomes mandatory again
    # def test_403_user_not_confirmed(self):
    #     """
    #     Tests forbidden user authentication
    #     """
    #     self.patient.is_confirmed = False
    #     self.patient.save()
    #
    #     # get first user token
    #     response = self.client.post(path=reverse('token'),
    #                                 data={'username': self.USERNAME, 'password': self.PASSWORD})
    #     data = response.json()
    #     token = data['token']
    #
    #     # send request to retrieve the non-confirmed user
    #     url = reverse('mobile:patient-detail', kwargs={'pk': self.patient.user.id})
    #     response = self.client.get(url, HTTP_AUTHORIZATION='Token {0}'.format(token))
    #     data = response.json()
    #
    #     self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    #     self.assertEqual(data['detail'], 'User email is not confirmed. Confirm it and then retry')

