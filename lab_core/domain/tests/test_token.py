# encode: utf-8

import os
import time

from django.conf import settings
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from domain.tests.factory_models import PatientFactory


class TestExpirableToken(APITestCase):

    USERNAME = 'john'
    EMAIL = 'doe@roundpe.gs'
    PASSWORD = 'secret'

    def setUp(self):
        self.user = User.objects.create_user(self.USERNAME, self.EMAIL, password=self.PASSWORD)
        self.patient = PatientFactory()
        self.patient.user = self.user
        self.patient.save()

        os.environ.setdefault('RUNNING_TESTS', "1")

    def test_api_200(self):
        """
        Tests token creation API.
        """
        response = self.client.post(path=reverse('token'),
                                    data={'username': self.USERNAME, 'password': self.PASSWORD})
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', data)

    def test_api_wrong_user_400(self):
        """
        Tests token creation API.
        """
        response = self.client.post(path=reverse('token'),
                                    data={'username': 'XXX', 'password': self.PASSWORD})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_api_wrong_password_400(self):
        """
        Tests token creation API.
        """
        response = self.client.post(path=reverse('token'),
                                    data={'username': self.USERNAME, 'password': 'XXX'})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_authentication_200(self):
        """
        Tests expirable token functionality.
        :return:
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

    def test_authentication_no_token_403(self):
        """
        Tests expirable token functionality.
        :return:
        """
        url = reverse('mobile:patient-detail', kwargs={'pk': self.patient.user.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authentication_wrong_token_403(self):
        """
        Tests expirable token functionality.
        :return:
        """
        url = reverse('mobile:patient-detail', kwargs={'pk': self.patient.user.id})
        response = self.client.get(url, HTTP_AUTHORIZATION='Token XXX')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authentication_expired_token_403(self):
        """
        Tests expirable token functionality.
        :return:
        """
        # get token
        response = self.client.post(path=reverse('token'),
                                    data={'username': self.USERNAME, 'password': self.PASSWORD})
        data = response.json()
        token = data['token']

        # expire token
        time.sleep(settings.TOKEN_EXPIRATION_IN_SECONDS + 1)

        # send request
        url = reverse('mobile:patient-detail', kwargs={'pk': self.patient.user.id})
        response = self.client.get(url, HTTP_AUTHORIZATION='Token {0}'.format(token))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authentication_expired_delta_token_403(self):
        """
        Tests expirable token functionality.
        :return:
        """
        delta = int(settings.TOKEN_EXPIRATION_DELTA_IN_SECONDS / settings.TOKEN_EXPIRATION_IN_SECONDS)

        # get token
        response = self.client.post(path=reverse('token'),
                                    data={'username': self.USERNAME, 'password': self.PASSWORD})
        data = response.json()
        token = data['token']

        # any ordinary API
        url = reverse('mobile:patient-detail', kwargs={'pk': self.patient.user.id})

        for i in range(delta):
            # token almost expires
            time.sleep(settings.TOKEN_EXPIRATION_IN_SECONDS - 1)

            # send request and refresh token
            response = self.client.get(url, HTTP_AUTHORIZATION='Token {0}'.format(token))

            self.assertEqual(response.status_code, status.HTTP_200_OK)

        # sleeps in order to reach delta time
        time.sleep(delta+1)

        # send request (token is valid, but delta time was reached)
        response = self.client.get(url, HTTP_AUTHORIZATION='Token {0}'.format(token))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
