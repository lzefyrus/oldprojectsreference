# encode: utf-8

import datetime
import os
import time

from django.conf import settings
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from domain.tests.factory_models import RecoverPasswordFactory


class TestRecoverPassword(APITestCase):

    USERNAME = 'john'
    EMAIL = 'doe@roundpe.gs'
    PASSWORD = 'secret'

    def setUp(self):
        os.environ.setdefault('RUNNING_TESTS', "1")

        self.user = User.objects.create_user(self.USERNAME, self.EMAIL, password=self.PASSWORD)
        self.recovering = RecoverPasswordFactory()
        self.recovering.user = self.user
        self.recovering.save()

    def test_api_recover_200(self):
        """
        Tests password recovering creation API.
        """
        response = self.client.post(path=reverse('recover_password'), data={'email': self.EMAIL})
        data = response.json()

        self.assertEqual(data, {})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_api_invalid_email_400(self):
        """
        Tests password recover API with an invalid email.
        :return:
        """
        response = self.client.post(path=reverse('recover_password'), data={'email': "invalid@email.com"})
        data = response.json()

        self.assertEqual(data["detail"], "User matching query does not exist.")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_api_without_email_400(self):
        """
        Tests password recover API with no email.
        :return:
        """
        response = self.client.post(path=reverse('recover_password'), data={'name': "invalid@email.com"})
        data = response.json()

        self.assertEqual(data["email"][0], "This field is required.")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_api_reset_200(self):
        """
        Tests password reset API.
        """
        response = self.client.post(path=reverse('reset_password'),
                                    data={"token": self.recovering.token,
                                          "new_password": "my_secret",
                                          "new_password_confirmation": "my_secret"})
        data = response.json()

        self.assertEqual(data, {})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_api_reset_without_token_400(self):
        """
        Tests password reset API with no token.
        :return:
        """
        response = self.client.post(path=reverse('reset_password'),
                                    data={
                                        # "token": "2131231as2wsas",
                                        "new_password": "mypass",
                                        "new_password_confirmation": "mypass",
                                    })
        data = response.json()

        self.assertEqual(data["token"][0], "This field is required.")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_api_reset_without_password_400(self):
        """
        Tests password reset API with no password.
        :return:
        """
        response = self.client.post(path=reverse('reset_password'),
                                    data={
                                        "token": "2131231as2wsas",
                                        # "new_password": "mypass",
                                        "new_password_confirmation": "mypass",
                                    })
        data = response.json()

        self.assertEqual(data["new_password"][0], "This field is required.")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_api_reset_without_password_confirmation_400(self):
        """
        Tests password reset API with no password confirmation.
        :return:
        """
        response = self.client.post(path=reverse('reset_password'),
                                    data={
                                        "token": "2131231as2wsas",
                                        "new_password": "mypass",
                                        # "new_password_confirmation": "mypass",
                                    })
        data = response.json()

        self.assertEqual(data["new_password_confirmation"][0], "This field is required.")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_api_reset_different_passwords_400(self):
        """
        Tests password reset API with different password/confirmation.
        :return:
        """
        response = self.client.post(path=reverse('reset_password'),
                                    data={
                                        "token": self.recovering.token,
                                        "new_password": "mypass",
                                        "new_password_confirmation": "mywrongpassconfirmation",
                                    })
        data = response.json()

        self.assertEqual(data["password"], "Password/confirmation doesn't match.")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_api_reset_invalid_token_400(self):
        """
        Tests password reset API with no password confirmation.
        :return:
        """
        response = self.client.post(path=reverse('reset_password'),
                                    data={
                                        "token": "xxx",
                                        "new_password": "mypass",
                                        "new_password_confirmation": "mypass",
                                    })
        data = response.json()

        self.assertEqual(data["detail"], "Token does not exist or has already been used before.")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_api_reset_expired_token_400(self):
        """
        Tests expirable token functionality.
        :return:
        """
        recover = RecoverPasswordFactory()
        recover.expiration_date = datetime.datetime.now() + datetime.timedelta(seconds=settings.RESET_PASSWORD_EXPIRATION_IN_SECONDS)
        recover.save()

        time.sleep(settings.RESET_PASSWORD_EXPIRATION_IN_SECONDS+1)

        response = self.client.post(path=reverse('reset_password'),
                                    data={"token": recover.token,
                                          "new_password": "my_secret",
                                          "new_password_confirmation": "my_secret"})
        data = response.json()

        self.assertIn("token", data, "Expiration date is not working")
        self.assertEqual(data["token"], "This token has expired. Ask for another one.")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_api_reset_used_token_400(self):
        """
        Tests if previous tokens are canceled as a new one is created.
        :return:
        """
        self.client.post(path=reverse('recover_password'), data={'email': self.EMAIL})

        response = self.client.post(path=reverse('reset_password'),
                                    data={"token": self.recovering.token,  # request reset using the old token
                                          "new_password": "my_secret",
                                          "new_password_confirmation": "my_secret"})
        data = response.json()

        self.assertEqual(data["detail"], "Token does not exist or has already been used before.")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
