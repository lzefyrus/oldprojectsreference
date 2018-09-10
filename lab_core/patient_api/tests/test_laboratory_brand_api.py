# encode: utf-8

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from domain.models import Laboratory
from domain.tests.factory_models import LaboratoryFactory


class LaboratoryBrandAPITests(APITestCase):

    laboratory = None

    def setUp(self):
        """
        Setting up things before tests.
        :return:
        """
        # Getting authenticated for the next requests.
        User.objects.create_user('lab', 'lab@roundpe.gs', password='secret')
        self.client.login(username='lab', password='secret')

        # Creating Laboratory.
        self.laboratory = LaboratoryFactory()

    def test_get_api_200(self):
        """
        Tests GET (retrieve) API for status code 200.
        """
        url = reverse('mobile:brand-laboratories', kwargs={'pk': self.laboratory.brand.id})
        response = self.client.get(url)
        data = response.json()

        laboratory_data = data['laboratories'][0]
        brand_data = data['brand']
        address_data = laboratory_data["address"]
        coordinates_data = laboratory_data["coordinates"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(laboratory_data['id'], self.laboratory.id)
        # self.assertEqual(laboratory_data['exams_id'], [])
        # self.assertEqual(laboratory_data['external_id'], self.laboratory.external_id)
        self.assertEqual(laboratory_data['description'], self.laboratory.description)
        self.assertEqual(laboratory_data['brand_name'], self.laboratory.brand.name)
        # self.assertEqual(laboratory_data['is_active'], self.laboratory.is_active)
        # self.assertEqual(laboratory_data['cnpj'], self.laboratory.cnpj)
        self.assertEqual(address_data['street'], self.laboratory.street)
        self.assertEqual(address_data['street_number'], self.laboratory.street_number)
        self.assertEqual(address_data['zip_code'], self.laboratory.zip_code)
        self.assertEqual(address_data['city'], self.laboratory.city)
        self.assertEqual(address_data['district'], self.laboratory.district)
        self.assertEqual(address_data['country'], self.laboratory.country)
        self.assertEqual(address_data['state'], self.laboratory.state)
        self.assertEqual(address_data['state_abbreviation'], self.laboratory.state_abbreviation)
        # self.assertEqual(coordinates_data['lat'], self.laboratory.lat)
        # self.assertEqual(coordinates_data['lng'], self.laboratory.lng)

        self.assertEqual(brand_data['id'], self.laboratory.brand.id)
        self.assertEqual(brand_data['name'], self.laboratory.brand.name)
        self.assertEqual(brand_data['is_active'], self.laboratory.brand.is_active)
        self.assertEqual(brand_data['similar_brand_id'], None)

    def test_get_list_api_200(self):
        """
        Tests GET (list) API for status code 200.
        """
        url = reverse('mobile:brand-list')
        response = self.client.get(url)
        data = response.json()

        self.assertIn('count', data)
        self.assertIn('next', data)
        self.assertIn('previous', data)
        self.assertIn('results', data)

        brand_data = data['results'][0]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(brand_data['id'], self.laboratory.brand.id)
        self.assertEqual(brand_data['name'], self.laboratory.brand.name)
        self.assertEqual(brand_data['is_active'], self.laboratory.brand.is_active)
        self.assertEqual(brand_data['similar_brand_id'], None)

    def test_get_api_invalid_int_brand_400(self):
        """
        Tests GET (retrieve) API for status code 400.
        """
        url = reverse('mobile:brand-laboratories', kwargs={'pk': 99999})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_api_404(self):
        """
        Tests GET (retrieve) API for status code 404.
        """
        # Removing Laboratories from database
        Laboratory.objects.filter(brand=self.laboratory.brand.id).delete()

        url = reverse('mobile:brand-laboratories', kwargs={'pk': self.laboratory.brand.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
