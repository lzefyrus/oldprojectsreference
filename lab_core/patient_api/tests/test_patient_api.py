# encode: utf-8

import logging
import uuid

from django.contrib.auth.models import User
from django.urls import reverse
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from domain.utils import disable_signals
from domain.tests.factory_models import LaboratoryFactory, MedicalPrescriptionFactory, PatientFactory
from domain.models import Patient

log = logging.getLogger(__name__)


@override_settings(
    task_always_eager=True,
)
class PatientAPITests(APITestCase):

    patient = None
    laboratory = None

    def setUp(self):
        """
        Setting up things before tests.
        :return:
        """
        # Disabling push notification/firebase signals.
        disable_signals()

        # Getting authenticated for the next requests.
        user = User.objects.create_user('john', 'doe@roundpe.gs', password='secret')
        self.client.login(username='john', password='secret')

        # Creating a Laboratory (dependency for POST tests).
        self.laboratory = LaboratoryFactory()
        self.laboratory.save()

        self.current_patient = PatientFactory()
        self.current_patient.user = user
        self.current_patient.preferred_laboratories = [self.laboratory]
        self.current_patient.save()
        self.current_patient.token = uuid.uuid4().hex

    def test_get_current_api_200(self):
        """
        Tests GET (retrieve) current patient for status code 200.
        """
        url = reverse('mobile:patient-current')
        response = self.client.get(url)
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data['id_device'], self.current_patient.id_device)
        self.assertEqual(data['created_timestamp'], int(self.current_patient.created.timestamp()))
        self.assertEqual(data['gender'], self.current_patient.gender)
        self.assertEqual(data['birth_date'], str(self.current_patient.birth_date))
        self.assertIn(self.current_patient.picture_id_front.name, data['picture_id_front_url'])
        self.assertIn(self.current_patient.picture_id_back.name, data['picture_id_back_url'])
        self.assertIn(self.current_patient.selfie.name, data['selfie_url'])
        self.assertEqual(data['user']['id'], self.current_patient.user.id)
        self.assertEqual(data['user']['username'], self.current_patient.user.username)
        self.assertEqual(data['user']['email'], self.current_patient.user.email)
        self.assertEqual(data['user']['first_name'], self.current_patient.user.first_name)
        self.assertEqual(data['user']['last_name'], self.current_patient.user.last_name)
        self.assertEqual(data['preferred_laboratories'][0]['id'], self.current_patient.preferred_laboratories.all()[0].id)
        self.assertEqual(data['full_name'], self.current_patient.full_name)
        self.assertEqual(data['phone'], self.current_patient.phone)

    def test_get_current_api_404(self):
        """
        Tests GET (retrieve) current patient for status code 404.
        There is a User but it is not associated with a Patient
        """
        User.objects.create_user('john_2', 'doe2@roundpe.gs', password='secret')
        self.client.login(username='john_2', password='secret')

        url = reverse('mobile:patient-current')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_api_200(self):
        """
        Tests GET (retrieve) API for status code 200.
        """
        url = reverse('mobile:patient-detail', kwargs={'pk': self.current_patient.user.id})
        response = self.client.get(url)
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data['id_device'], self.current_patient.id_device)
        self.assertEqual(data['created_timestamp'], int(self.current_patient.created.timestamp()))
        self.assertEqual(data['gender'], self.current_patient.gender)
        self.assertEqual(data['birth_date'], str(self.current_patient.birth_date))
        self.assertIn(self.current_patient.picture_id_front.name, data['picture_id_front_url'])
        self.assertIn(self.current_patient.picture_id_back.name, data['picture_id_back_url'])
        self.assertIn(self.current_patient.selfie.name, data['selfie_url'])
        self.assertEqual(data['user']['username'], self.current_patient.user.username)
        self.assertEqual(data['user']['email'], self.current_patient.user.email)
        self.assertEqual(data['preferred_laboratories'][0]['id'], self.current_patient.preferred_laboratories.all()[0].id)
        self.assertEqual(data['full_name'], self.current_patient.full_name)
        self.assertEqual(data['phone'], self.current_patient.phone)

    def test_get_api_403(self):
        """
        Tests GET (retrieve) API for status code 403.
        """
        url = reverse('mobile:patient-detail', kwargs={'pk': 9999999999})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_api_list_200(self):
        """
        Tests GET (retrieve) list API for status code 200.
        """
        url = reverse('mobile:patient-list')
        response = self.client.get(url)
        data = response.json()
        response_data = data['results'][0]

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response_data['id_device'], self.current_patient.id_device)
        self.assertEqual(response_data['created_timestamp'], int(self.current_patient.created.timestamp()))
        self.assertEqual(response_data['gender'], self.current_patient.gender)
        self.assertEqual(response_data['birth_date'], str(self.current_patient.birth_date))
        self.assertIn(self.current_patient.picture_id_front.name, response_data['picture_id_front_url'])
        self.assertIn(self.current_patient.picture_id_back.name, response_data['picture_id_back_url'])
        self.assertIn(self.current_patient.selfie.name, response_data['selfie_url'])
        self.assertEqual(response_data['user']['username'], self.current_patient.user.username)
        self.assertEqual(response_data['user']['email'], self.current_patient.user.email)
        self.assertEqual(response_data['preferred_laboratories'][0]['id'],
                         self.current_patient.preferred_laboratories.all()[0].id)
        self.assertEqual(response_data['full_name'], self.current_patient.full_name)
        self.assertEqual(response_data['phone'], self.current_patient.phone)

    def test_get_api_list_200_with_email(self):
        """
        Tests GET (retrieve) list API for status code 200.
        """
        url = reverse('mobile:patient-list')
        response = self.client.get(url + "?email={0}".format(self.current_patient.user.email))
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(data['id_device'], self.current_patient.id_device)
        self.assertEqual(data['created_timestamp'], int(self.current_patient.created.timestamp()))
        self.assertEqual(data['gender'], self.current_patient.gender)
        self.assertEqual(data['birth_date'], str(self.current_patient.birth_date))
        self.assertIn(self.current_patient.picture_id_front.name, data['picture_id_front_url'])
        self.assertIn(self.current_patient.picture_id_back.name, data['picture_id_back_url'])
        self.assertIn(self.current_patient.selfie.name, data['selfie_url'])
        self.assertEqual(data['user']['username'], self.current_patient.user.username)
        self.assertEqual(data['user']['email'], self.current_patient.user.email)
        self.assertEqual(data['preferred_laboratories'][0]['id'],
                         self.current_patient.preferred_laboratories.all()[0].id)
        self.assertEqual(data['full_name'], self.current_patient.full_name)
        self.assertEqual(data['phone'], self.current_patient.phone)

    def test_get_api_list_404_with_invalid_email(self):
        """
        Tests GET (retrieve) list API for status code 404.
        """
        url = reverse('mobile:patient-list')
        response = self.client.get(url + "?email=invalid@email.com")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_api_list_empty_200(self):
        """
        Tests GET (retrieve) list API for status code 200.
        """
        # Removing patients from the database.
        Patient.objects.all().delete()

        url = reverse('mobile:patient-list')
        response = self.client.get(url)
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data['count'], 0)
        self.assertEqual(data['results'], [])

    def test_post_api_201(self):
        """
        Tests POST (create) API for status code 201.
        """
        url = reverse('mobile:patient-list')

        # JSON (payload)
        data = {
            "id_device": "12345676",
            "gender": "M",
            "birth_date": "2016-11-15",
            "full_name": "user lastname",
            "phone": 5511975259176,
            "user": {
              "password": "123456",
              "email": "juca_silva@yahoo.com.br"
            },
            "preferred_laboratories_id": [self.laboratory.id],
            "picture_id_front": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "picture_id_back": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "selfie": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "token": uuid.uuid4().hex
        }

        response = self.client.post(url, data=data, format="json")
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(data['id_device'], '12345676')
        self.assertIn('created_timestamp', data)
        self.assertEqual(data['gender'], 'M')
        self.assertEqual(data['birth_date'], '2016-11-15')
        self.assertIn('id', data['user'])
        self.assertEqual(data['user']['username'], 'juca_silva@yahoo.com.br')
        self.assertEqual(data['user']['email'], 'juca_silva@yahoo.com.br')
        self.assertEqual(data['user']['first_name'], '')
        self.assertEqual(data['user']['last_name'], '')
        self.assertEqual(data['preferred_laboratories'][0]['id'], self.laboratory.id)
        self.assertEqual(data['full_name'], 'user lastname')
        self.assertEqual(data['phone'], 5511975259176)
        self.assertIn('jpg', data['picture_id_front_url'])
        self.assertIn('jpg', data['picture_id_back_url'])
        self.assertIn('jpg', data['selfie_url'])

    def test_post_api_duplicated_username_400(self):
        """
        Tests POST (create) API for status code 400 with duplicated username (unique).
        PS: The email is used as username
        """
        url = reverse('mobile:patient-list')

        # JSON (payload)
        data = {
            "id_device": "12345676",
            "gender": "M",
            "birth_date": "2016-11-15",
            "full_name": "user lastname",
            "phone": 5511975259176,
            "user": {
                "password": "123456",
                "email": "juca_silva@yahoo.com.br"
            },
            "preferred_laboratories_id": [self.laboratory.id],
            "picture_id_front": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "picture_id_back": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "selfie": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "token": uuid.uuid4().hex
        }

        # First request
        response = self.client.post(url, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Second request
        response = self.client.post(url, data=data, format="json")
        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response_data)
        self.assertEqual(response_data['detail'], 'This username already exists.')

    def test_post_api_no_device_id_201(self):
        """
        Tests POST (create) API for status code 201.
        """
        url = reverse('mobile:patient-list')

        # JSON (payload)
        data = {
            # "id_device": "12345676", --> no device_id
            "gender": "M",
            "birth_date": "2016-11-15",
            "full_name": "user lastname",
            "phone": 5511975259176,
            "user": {
                "password": "123456",
                "email": "juca_silva@yahoo.com.br"
            },
            "preferred_laboratories_id": [self.laboratory.id],
            "picture_id_front": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "picture_id_back": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "selfie": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "token": uuid.uuid4().hex
        }

        response = self.client.post(url, data=data, format="json")
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNone(data['id_device'])
        self.assertIn("created_timestamp", data)
        self.assertEqual(data['gender'], 'M')
        self.assertEqual(data['birth_date'], '2016-11-15')
        self.assertEqual(data['user']['username'], 'juca_silva@yahoo.com.br')
        self.assertEqual(data['user']['email'], 'juca_silva@yahoo.com.br')
        self.assertEqual(data['preferred_laboratories'][0]['id'], self.laboratory.id)
        self.assertEqual(data['full_name'], "user lastname")
        self.assertEqual(data['phone'], 5511975259176)
        self.assertIn('jpg', data['picture_id_front_url'])
        self.assertIn('jpg', data['picture_id_back_url'])
        self.assertIn('jpg', data['selfie_url'])

    def test_post_api_no_gender_400(self):
        """
        Tests POST (create) API for status code 400.
        """
        url = reverse('mobile:patient-list')

        # JSON (payload)
        data = {
            "id_device": "12345676",
            # "gender": "M", --> no gender
            "birth_date": "2016-11-15",
            "full_name": "user lastname",
            "phone": 5511975259176,
            "user": {
                "password": "123456",
                "email": "juca_silva@yahoo.com.br"
            },
            "preferred_laboratories_id": [self.laboratory.id],
            "picture_id_front": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "picture_id_back": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "selfie": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "token": uuid.uuid4().hex
        }

        response = self.client.post(url, data=data, format="json")
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(data['gender'][0], 'This field is required.')

    def test_post_api_no_birth_date_201(self):
        """
        Tests POST (create) API for status code 201.
        """
        url = reverse('mobile:patient-list')

        # JSON (payload)
        data = {
            "id_device": "12345676",
            "gender": "M",
            # "birth_date": "2016-11-15", --> no birth_date
            "full_name": "user lastname",
            "phone": 5511975259176,
            "user": {
                "password": "123456",
                "email": "juca_silva@yahoo.com.br"
            },
            "preferred_laboratories_id": [self.laboratory.id],
            "picture_id_front": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "picture_id_back": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "selfie": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "token": uuid.uuid4().hex
        }

        response = self.client.post(url, data=data, format="json")
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_post_api_no_user_400(self):
        """
        Tests POST (create) API for status code 400.
        """
        url = reverse('mobile:patient-list')

        # JSON (payload)
        data = {
            "id_device": "12345676",
            "gender": "M",
            "birth_date": "2016-11-15",
            "phone": 5511975259176,
            # "user": {                 --> no user
            #     "username": "juca123",
            #     "first_name": "Juca",
            #     "last_name": "Silva",
            #     "email": "juca_silva@yahoo.com.br"
            # },
            "preferred_laboratories_id": [self.laboratory.id],
            "picture_id_front": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "picture_id_back": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "selfie": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "token": uuid.uuid4().hex
        }

        response = self.client.post(url, data=data, format="json")
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(data['user'][0], 'This field is required.')

    def test_post_api_invalid_preferred_laboratories_400(self):
        """
        Tests POST (create) API for status code 400.
        """
        url = reverse('mobile:patient-list')

        # JSON (payload)
        data = {
            "id_device": "12345676",
            "gender": "M",
            "birth_date": "2016-11-15",
            "full_name": "user lastname",
            "phone": 5511975259176,
            "user": {
                "password": "123456",
                "email": "juca_silva@yahoo.com.br"
            },
            "preferred_laboratories_id": [99999999],
            "picture_id_front": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "picture_id_back": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "selfie": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "token": uuid.uuid4().hex
        }

        response = self.client.post(url, data=data, format="json")
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Laboratory matching query does not exist.', data['detail'])

    def test_post_api_no_picture_id_front_201(self):
        """
        Tests POST (create) API for status code 201.
        """
        url = reverse('mobile:patient-list')

        # JSON (payload)
        data = {
            "id_device": "12345676",
            "gender": "M",
            "birth_date": "2016-11-15",
            "full_name": "user lastname",
            "phone": 5511975259176,
            "user": {
                "password": "123456",
                "email": "juca_silva@yahoo.com.br"
            },
            "preferred_laboratories_id": [self.laboratory.id],
            # "picture_id_front": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=", --> no picture_id_front
            "picture_id_back": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "selfie": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "token": uuid.uuid4().hex
        }

        response = self.client.post(url, data=data, format="json")
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(data['id_device'], '12345676')
        self.assertIn('created_timestamp', data)
        self.assertEqual(data['gender'], 'M')
        self.assertEqual(data['birth_date'], '2016-11-15')
        self.assertEqual(data['user']['username'], 'juca_silva@yahoo.com.br')
        self.assertEqual(data['user']['email'], 'juca_silva@yahoo.com.br')
        self.assertEqual(data['preferred_laboratories'][0]['id'], self.laboratory.id)
        self.assertEqual(data['full_name'], 'user lastname')
        self.assertEqual(data['phone'], 5511975259176)
        self.assertEquals(data['picture_id_front_url'], '')
        self.assertIn('jpg', data['picture_id_back_url'])
        self.assertIn('jpg', data['selfie_url'])

    def test_post_api_no_picture_id_back_201(self):
        """
        Tests POST (create) API for status code 201.
        """
        url = reverse('mobile:patient-list')

        # JSON (payload)
        data = {
            "id_device": "12345676",
            "gender": "M",
            "birth_date": "2016-11-15",
            "full_name": "user lastname",
            "phone": 5511975259176,
            "user": {
                "password": "123456",
                "email": "juca_silva@yahoo.com.br"
            },
            "preferred_laboratories_id": [self.laboratory.id],
            "picture_id_front": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            # "picture_id_back": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=", --> no picture_id_back
            "selfie": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "token": uuid.uuid4().hex
        }

        response = self.client.post(url, data=data, format="json")
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(data['id_device'], '12345676')
        self.assertIn('created_timestamp', data)
        self.assertEqual(data['gender'], 'M')
        self.assertEqual(data['birth_date'], '2016-11-15')
        self.assertEqual(data['user']['username'], 'juca_silva@yahoo.com.br')
        self.assertEqual(data['user']['email'], 'juca_silva@yahoo.com.br')
        self.assertEqual(data['preferred_laboratories'][0]['id'], self.laboratory.id)
        self.assertEqual(data['full_name'], 'user lastname')
        self.assertEqual(data['phone'], 5511975259176)
        self.assertIn('jpg', data['picture_id_front_url'])
        self.assertEquals(data['picture_id_back_url'], '')
        self.assertIn('jpg', data['selfie_url'])

    def test_post_api_no_selfie_201(self):
        """
        Tests POST (create) API for status code 201.
        """
        url = reverse('mobile:patient-list')

        # JSON (payload)
        data = {
            "id_device": "12345676",
            "gender": "M",
            "birth_date": "2016-11-15",
            "full_name": "user lastname",
            "phone": 5511975259176,
            "user": {
                "password": "123456",
                "email": "juca_silva@yahoo.com.br"
            },
            "preferred_laboratories_id": [self.laboratory.id],
            "picture_id_front": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "picture_id_back": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            # "selfie": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=" --> no selfie,
            "token": uuid.uuid4().hex
        }

        response = self.client.post(url, data=data, format="json")
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(data['id_device'], '12345676')
        self.assertIn('created_timestamp', data)
        self.assertEqual(data['gender'], 'M')
        self.assertEqual(data['birth_date'], '2016-11-15')
        self.assertEqual(data['user']['username'], 'juca_silva@yahoo.com.br')
        self.assertEqual(data['user']['email'], 'juca_silva@yahoo.com.br')
        self.assertEqual(data['preferred_laboratories'][0]['id'], self.laboratory.id)
        self.assertEqual(data['full_name'], 'user lastname')
        self.assertEqual(data['phone'], 5511975259176)
        self.assertIn('jpg', data['picture_id_front_url'])
        self.assertIn('jpg', data['picture_id_back_url'])
        self.assertEqual(data['selfie_url'], '')

    def test_post_api_no_phone_201(self):
        """
        Tests POST (create) API for status code 201.
        """
        url = reverse('mobile:patient-list')

        # JSON (payload)
        data = {
            "id_device": "12345676",
            "gender": "M",
            "birth_date": "2016-11-15",
            "full_name": "user lastname",
            # "phone": 551175259176, --> no phone
            "user": {
                "password": "123456",
                "email": "juca_silva@yahoo.com.br"
            },
            "preferred_laboratories_id": [self.laboratory.id],
            "picture_id_front": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "picture_id_back": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "selfie": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "token": uuid.uuid4().hex
        }

        response = self.client.post(url, data=data, format="json")
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(data['id_device'], '12345676')
        self.assertIn('created_timestamp', data)
        self.assertEqual(data['gender'], 'M')
        self.assertEqual(data['birth_date'], '2016-11-15')
        self.assertEqual(data['user']['username'], 'juca_silva@yahoo.com.br')
        self.assertEqual(data['user']['email'], 'juca_silva@yahoo.com.br')
        self.assertEqual(data['preferred_laboratories'][0]['id'], self.laboratory.id)
        self.assertEqual(data['full_name'], 'user lastname')
        self.assertIsNone(data['phone'])
        self.assertIn('jpg', data['picture_id_front_url'])
        self.assertIn('jpg', data['picture_id_back_url'])
        self.assertIn('jpg',  data['selfie_url'])

    def test_post_api_no_token_201(self):
        """
        Tests POST (create) API for status code 201.
        """
        url = reverse('mobile:patient-list')

        # JSON (payload)
        data = {
            "id_device": "12345676",
            "gender": "M",
            "birth_date": "2016-11-15",
            "full_name": "user lastname",
            # "phone": 551175259176, --> no phone
            "user": {
                "password": "123456",
                "email": "juca_silva@yahoo.com.br"
            },
            "preferred_laboratories_id": [self.laboratory.id],
            "picture_id_front": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "picture_id_back": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "selfie": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            # "token": uuid.uuid4().hex
        }

        response = self.client.post(url, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_put_api_200(self):
        """
        Tests PUT (create) API for status code 200.
        """
        url = reverse('mobile:patient-detail', kwargs={'pk': self.current_patient.user.id})

        # JSON (payload)
        data = {
            "phone": 5513975269813,
            "preferred_laboratories_id": [self.laboratory.id],
            "picture_id_front": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "picture_id_back": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "selfie": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "gender": "F",
            "user": {
                "first_name": "John",
                "last_name": "The tester"
            }
        }

        response = self.client.put(url, data=data, format="json")
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data['phone'], 5513975269813)
        self.assertEqual(data['preferred_laboratories'][0]['id'], self.laboratory.id)
        self.assertIn('jpg', data['picture_id_front_url'])
        self.assertIn('jpg', data['picture_id_back_url'])
        self.assertIn('jpg', data['selfie_url'])
        self.assertEqual(data['gender'], 'F')
        self.assertEqual(data['user']['first_name'], 'John')
        self.assertEqual(data['user']['last_name'], 'The tester')

    def test_put_api_200_no_phone(self):
        """
        Tests PUT (create) API for status code 200.
        """
        url = reverse('mobile:patient-detail', kwargs={'pk': self.current_patient.user.id})

        # JSON (payload)
        data = {
            # "phone": 5513975269813,
            "preferred_laboratories_id": [self.laboratory.id],
            "picture_id_front": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "picture_id_back": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "selfie": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "gender": "F",
            "user": {
                "first_name": "John",
                "last_name": "The tester"
            }
        }

        response = self.client.put(url, data=data, format="json")
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data['preferred_laboratories'][0]['id'], self.laboratory.id)
        self.assertIn('jpg', data['picture_id_front_url'])
        self.assertIn('jpg', data['picture_id_back_url'])
        self.assertIn('jpg', data['selfie_url'])
        self.assertEqual(data['gender'], 'F')
        self.assertEqual(data['user']['first_name'], 'John')
        self.assertEqual(data['user']['last_name'], 'The tester')

    def test_put_api_200_no_laboratory(self):
        """
        Tests PUT (create) API for status code 200.
        """
        url = reverse('mobile:patient-detail', kwargs={'pk': self.current_patient.user.id})

        # JSON (payload)
        data = {
            "phone": 5513975269813,
            # "preferred_laboratories_id": [self.laboratory.id],
            "picture_id_front": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "picture_id_back": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "selfie": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "gender": "F",
            "user": {
                "first_name": "John",
                "last_name": "The tester"
            }
        }

        response = self.client.put(url, data=data, format="json")
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data['phone'], 5513975269813)
        self.assertIn('jpg', data['picture_id_front_url'])
        self.assertIn('jpg', data['picture_id_back_url'])
        self.assertIn('jpg', data['selfie_url'])
        self.assertEqual(data['gender'], 'F')
        self.assertEqual(data['user']['first_name'], 'John')
        self.assertEqual(data['user']['last_name'], 'The tester')

    def test_put_api_invalid_picture_id_front_400(self):
        """
        Tests PUT (create) API for status code 200.
        """
        url = reverse('mobile:patient-detail', kwargs={'pk': self.current_patient.user.id})

        # JSON (payload)
        data = {
            "phone": 5513975269813,
            "preferred_laboratories_id": [self.laboratory.id],
            "picture_id_front": "123",
            "picture_id_back": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "selfie": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "gender": "F",
            "user": {
                "first_name": "John",
                "last_name": "The tester"
            }
        }

        response = self.client.put(url, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_put_api_invalid_picture_id_back_400(self):
        """
        Tests PUT (create) API for status code 200.
        """
        url = reverse('mobile:patient-detail', kwargs={'pk': self.current_patient.user.id})

        # JSON (payload)
        data = {
            "phone": 5513975269813,
            "preferred_laboratories_id": [self.laboratory.id],
            "picture_id_front": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "picture_id_back": "123",
            "selfie": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "gender": "F",
            "user": {
                "first_name": "John",
                "last_name": "The tester"
            }
        }

        response = self.client.put(url, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_put_api_invalid_selfie_400(self):
        """
        Tests PUT (create) API for status code 200.
        """
        url = reverse('mobile:patient-detail', kwargs={'pk': self.current_patient.user.id})

        # JSON (payload)
        data = {
            "phone": 5513975269813,
            "preferred_laboratories_id": [self.laboratory.id],
            "picture_id_front": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "picture_id_back": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "selfie": "123",
            "gender": "F",
            "user": {
                "first_name": "John",
                "last_name": "The tester"
            }
        }

        response = self.client.put(url, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_put_api_invalid_laboratory_400(self):
        """
        Tests PUT (create) API for status code 200.
        """
        url = reverse('mobile:patient-detail', kwargs={'pk': self.current_patient.user.id})

        # JSON (payload)
        data = {
            "phone": 5513975269813,
            "preferred_laboratories_id": [99999],
            "picture_id_front": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "picture_id_back": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "selfie": "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "gender": "F",
            "user": {
                "first_name": "John",
                "last_name": "The tester"
            }
        }

        response = self.client.put(url, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_prescriptions_by_patient_403(self):
        """
        Tests GET (retrieve) API for status code 403.
        Patient does not exist.
        """
        url = reverse('mobile:patient-prescriptions', kwargs={'pk': 99999999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_prescriptions_by_patient_404_again(self):
        """
        Tests GET (retrieve) API for status code 404.
        Patient exists, but does not have any prescription.
        """
        url = reverse('mobile:patient-prescriptions', kwargs={'pk': self.current_patient.user.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_preferred_labs_by_patient_403(self):
        """
        Tests GET (retrieve) API for status code 403.
        Trying to access data from another user.
        """
        user = User.objects.create_user('john2', 'doe2@roundpe.gs', password='secret2')
        self.client.login(username='john2', password='secret2')
        patient = PatientFactory()
        patient.user = user
        patient.save()

        url = reverse('mobile:patient-preferred-labs', kwargs={'pk': self.current_patient.user.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_preferred_labs_by_patient_404(self):
        """
        Tests GET (retrieve) API for status code 404.
        Patient exists, but does not have any preferred lab.
        """
        user = User.objects.create_user('john2', 'doe2@roundpe.gs', password='secret2')
        self.client.login(username='john2', password='secret2')
        patient = PatientFactory()
        patient.user = user
        patient.save()

        url = reverse('mobile:patient-preferred-labs', kwargs={'pk': patient.user.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_preferred_labs_by_patient_200(self):
        """
        Tests GET API for status code 200.
        Brings all preferred labs belonging to a patient
        :return:
        """

        url = reverse('mobile:patient-preferred-labs', kwargs={'pk': self.current_patient.user.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_prescriptions_by_current_patient_404(self):
        """
        Tests GET (retrieve) API for status code 404.
        Patient exists, but doesn't have any prescription
        """
        user = User.objects.create_user('john2', 'doe2@roundpe.gs', password='secret2')
        self.client.login(username='john2', password='secret2')
        patient = PatientFactory()
        patient.user = user
        patient.save()

        url = reverse('mobile:patient-current/prescriptions')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_prescriptions_by_current_patient_200(self):
        """
        Tests GET API for status code 200.
        Brings all prescriptions from current patient
        :return:
        """
        self.prescription = MedicalPrescriptionFactory()
        self.prescription.patient = self.current_patient
        self.prescription.save()

        url = reverse('mobile:patient-current/prescriptions')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn("patient", data)
        self.assertIn("prescriptions", data)
        self.assertIn("expiration_date_timestamp", data['prescriptions'][0])
        self.assertIn("prescription_issued_at_timestamp", data['prescriptions'][0])

    def test_get_patient_email_confirmation_200(self):
        """
        Tests GET API for status code 200.
        Set is_confirmed field to true
        :return:
        """
        patient = PatientFactory()
        patient.is_confirmed = False
        patient.hash = uuid.uuid4().hex
        patient.save()

        url = reverse('mobile:patient-confirmation')
        url += "?token={0}".format(patient.hash)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.content.decode(), "Email confirmado! Clique, pelo seu celular, neste link e marque seus exames agora mesmo. Nos vemos em breve. Sara")

        confirmed_patient = Patient.objects.get(pk=patient.user.id)
        self.assertTrue(confirmed_patient.is_confirmed)

        # Try to confirm again
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.content.decode(), "Este email já foi confirmado! Clique, pelo seu celular, neste link e marque seus exames agora mesmo. Nos vemos em breve. Sara")

    def test_get_patient_email_confirmation_404(self):
        """
        Tests GET API for status code 404.
        Try to confirm an invalid patient
        :return:
        """
        url = reverse('mobile:patient-confirmation')
        response = self.client.get(url+"?token={0}".format("999999999"))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_patient_send_email_confirmation_200(self):
        """
        Tests GET API for status code 200.
        :return:
        """
        url = reverse('mobile:patient-send-confirmation')
        response = self.client.get(url+"?email={0}".format(self.current_patient.user.email))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {})

    def test_get_patient_send_email_confirmation_400_no_email(self):
        """
        Tests GET API for status code 400.
        No email parameter is passed in query string
        :return:
        """
        url = reverse('mobile:patient-send-confirmation')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()['detail'], 'You must send email parameter in querystring')

    def test_get_patient_send_email_confirmation_404_invalid_email(self):
        """
        Tests GET API for status code 200.
        An invalid email is given (can't find a patient with this email)
        :return:
        """
        url = reverse('mobile:patient-send-confirmation')
        response = self.client.get(url+"?email={0}".format("invalid_email@email.com"))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_put_patient_is_confirmed(self):
        """
        'is_confirmed' field must be updated only throught 'mobile/patient/<user_id>/confirmation'
        :return:
        """
        self.current_patient.is_confirmed = False
        self.current_patient.save()

        url = reverse('mobile:patient-detail', kwargs={'pk': self.current_patient.user.id})

        # JSON (payload)
        data = {
            "is_confirmed": True,
        }

        response = self.client.put(url, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.json()['is_confirmed'])

    def test_delete_patient(self):
        """
        Tests DELETE method for Patient
        :return:
        """
        self.current_patient.is_confirmed = False
        self.current_patient.save()

        url = reverse('mobile:patient-detail', kwargs={'pk': self.current_patient.user.id})

        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_invalid_patient(self):
        """
        Tests DELETE method for an invalid Patient
        :return:
        """
        self.current_patient.is_confirmed = False
        self.current_patient.save()

        url = reverse('mobile:patient-detail', kwargs={'pk': 999999})

        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_invalid_token_patient(self):
        """
        Tests DELETE method for an invalid Patient
        :return:
        """
        user = User.objects.create_user('john2', 'doe2@roundpe.gs', password='secret2')
        self.client.login(username='john2', password='secret2')

        patient = PatientFactory()
        patient.user = user
        patient.is_confirmed = False
        patient.save()

        url = reverse('mobile:patient-detail', kwargs={'pk': self.current_patient.user.id})

        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
