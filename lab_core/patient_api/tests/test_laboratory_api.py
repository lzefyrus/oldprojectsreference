# encode: utf-8

from django.contrib.auth.models import User
from django.contrib.gis.geos import Point
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from domain.tests.factory_models import LaboratoryFactory


class LaboratoryAPITests(APITestCase):

    laboratory = None

    def setUp(self):
        """
        Setting up things before tests.
        :return:
        """
        # Getting authenticated for the next requests.
        User.objects.create_user('lab', 'lab@roundpe.gs', password='secret')
        self.client.login(username='lab', password='secret')

        # Creating Laboratories.
        self.laboratory_one = LaboratoryFactory()  # located in Salto-SP-Brazil
        self.laboratory_one.point = Point(-47.291696, -23.204466)
        self.laboratory_one.save()

        self.laboratory_two = LaboratoryFactory()  # located in São Paulo-SP-Brazil
        self.laboratory_two.point = Point(-46.634079, -23.550059)
        self.laboratory_two.save()

        self.laboratory_three = LaboratoryFactory()  # No location
        self.laboratory_three.point = None
        self.laboratory_three.save()

    def test_retrieve_200(self):
        """
        Tests GET (retrieve) API for status code 200.
        """

        url = reverse('mobile:laboratory-detail', kwargs={'pk': self.laboratory_one.id})
        response = self.client.get(url)
        data = response.json()
        address = data["address"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(data['id'], self.laboratory_one.id)
        self.assertEqual(data['exams_id'], [exam.id for exam in self.laboratory_one.exams.all()])
        # self.assertEqual(data['external_id'], self.laboratory_one.external_id)
        self.assertEqual(data['description'], self.laboratory_one.description)
        self.assertEqual(data['brand_name'], self.laboratory_one.brand.name)
        # self.assertEqual(data['is_active'], self.laboratory_one.is_active)
        # self.assertEqual(data['cnpj'], self.laboratory_one.cnpj)
        self.assertEqual(address['street'], self.laboratory_one.street)
        self.assertEqual(address['street_number'], self.laboratory_one.street_number)
        self.assertEqual(address['zip_code'], self.laboratory_one.zip_code)
        self.assertEqual(address['city'], self.laboratory_one.city)
        self.assertEqual(address['district'], self.laboratory_one.district)
        self.assertEqual(address['state'], self.laboratory_one.state)
        self.assertEqual(address['state_abbreviation'], self.laboratory_one.state_abbreviation)
        self.assertEqual(address['country'], self.laboratory_one.country)

    def test_retrieve_200_no_coordinates(self):
        """
        Tests GET (retrieve) API for status code 200.
        """

        url = reverse('mobile:laboratory-detail', kwargs={'pk': self.laboratory_three.id})
        response = self.client.get(url)
        data = response.json()
        address = data["address"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(data['id'], self.laboratory_three.id)
        self.assertEqual(data['exams_id'], [exam.id for exam in self.laboratory_three.exams.all()])
        # self.assertEqual(data['external_id'], self.laboratory_three.external_id)
        self.assertEqual(data['description'], self.laboratory_three.description)
        self.assertEqual(data['brand_name'], self.laboratory_three.brand.name)
        # self.assertEqual(data['is_active'], self.laboratory_three.is_active)
        # self.assertEqual(data['cnpj'], self.laboratory_three.cnpj)
        self.assertEqual(address['street'], self.laboratory_three.street)
        self.assertEqual(address['street_number'], self.laboratory_three.street_number)
        self.assertEqual(address['zip_code'], self.laboratory_three.zip_code)
        self.assertEqual(address['city'], self.laboratory_three.city)
        self.assertEqual(address['district'], self.laboratory_three.district)
        self.assertEqual(address['state'], self.laboratory_three.state)
        self.assertEqual(address['state_abbreviation'], self.laboratory_three.state_abbreviation)
        self.assertEqual(address['country'], self.laboratory_three.country)

    def test_retrieve_404(self):
        """
        Tests GET (retrieve) API for status code 404.
        """

        url = reverse('mobile:laboratory-detail', kwargs={'pk': 999999})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_radius_get_list_api_200(self):
        """
        Tests GET (list) API for status code 200.
        In this test user is located in Tietê-SP-Brazil.
        Tietê is 43km away from Salto (1st Lab) and 119km away from São Paulo (2nd Lab).
        """
        # Located in Tietê-SP-Brazil
        lat = -23.119919
        lng = -47.707772

        # In a radius of 50km should retrieve one Lab (Salto)
        query_string = "lat={0}&lng={1}&radius=50000".format(lat, lng)
        url = "{0}?{1}".format(reverse('mobile:laboratory-list'), query_string)
        response = self.client.get(url)
        data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(data['results']), 1)

        # In a radius of 150km should retrieve two Labs (Salto and São Paulo)
        query_string = "lat={0}&lng={1}&radius=150000".format(lat, lng)
        url = "{0}?{1}".format(reverse('mobile:laboratory-list'), query_string)
        response = self.client.get(url)
        data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(data['results']), 2)

    def test_content_get_list_api_200(self):
        """
        Tests GET (list) API for status code 200.
        This test aims to verify response content.
        """
        query_string = "lat=-23.119919&lng=-47.707772&radius=50000"
        url = "{0}?{1}".format(reverse('mobile:laboratory-list'), query_string)
        response = self.client.get(url)
        data = response.json()

        # self.assertIn('count', data)
        # self.assertIn('next', data)
        # self.assertIn('previous', data)
        # self.assertIn('results', data)

        # laboratory_data = data['results'][0]
        # address_data = laboratory_data['address']
        # coordinates_data = laboratory_data['coordinates']

        # self.assertEqual(response.status_code, status.HTTP_200_OK)
        # self.assertEqual(laboratory_data['id'], self.laboratory_one.id)
        # self.assertEqual(laboratory_data['exams_id'], [])
        # # self.assertEqual(laboratory_data['external_id'], self.laboratory_one.external_id)
        # self.assertEqual(laboratory_data['description'], self.laboratory_one.description)
        # self.assertEqual(laboratory_data['brand_name'], self.laboratory_one.brand.name)
        # # self.assertEqual(laboratory_data['is_active'], self.laboratory_one.is_active)
        # # self.assertEqual(laboratory_data['cnpj'], self.laboratory_one.cnpj)
        # self.assertEqual(address_data['street'], self.laboratory_one.street)
        # self.assertEqual(address_data['street_number'], self.laboratory_one.street_number)
        # self.assertEqual(address_data['zip_code'], self.laboratory_one.zip_code)
        # self.assertEqual(address_data['city'], self.laboratory_one.city)
        # self.assertEqual(address_data['district'], self.laboratory_one.district)
        # self.assertEqual(address_data['country'], self.laboratory_one.country)
        # self.assertEqual(address_data['state'], self.laboratory_one.state)
        # self.assertEqual(address_data['state_abbreviation'], self.laboratory_one.state_abbreviation)
        # # self.assertEqual(coordinates_data['lat'], self.laboratory_one.point[1])
        # # self.assertEqual(coordinates_data['lng'], self.laboratory_one.point[0])

    def test_search_by_address_get_list_api_200(self):
        """
        Tests GET (list) API for status code 200.
        In this test an address is passed as parameter instead of lat/lng.
        User is located in Tietê-SP-Brazil.
        Tietê is 43km away from Salto (1st Lab) and 119km away from São Paulo (2nd Lab).
        """
        # Located in Tietê-SP-Brazil
        address = "Tietê-SP-Brazil"

        # In a radius of 50km should retrieve one Lab (Salto)
        query_string = "address={0}&radius=50000".format(address)
        url = "{0}?{1}".format(reverse('mobile:laboratory-list'), query_string)
        response = self.client.get(url)
        data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(data['results']), 1)

        # In a radius of 150km should retrieve two Labs (Salto and São Paulo)
        query_string = "address={0}&radius=150000".format(address)
        url = "{0}?{1}".format(reverse('mobile:laboratory-list'), query_string)
        response = self.client.get(url)
        data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(data['results']), 2)

    def test_brand_as_int_get_list_api_200(self):
        """
        Tests GET (list) API for status code 200.
        This test aims to verify 'brand' filter when passing int as value.
        """
        query_string = "lat=-23.119919&lng=-47.707772&radius=50000&brand={0}".format(self.laboratory_one.brand.id)
        url = "{0}?{1}".format(reverse('mobile:laboratory-list'), query_string)
        response = self.client.get(url)
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(data['results']), 1)

    def test_brand_as_list_get_list_api_200(self):
        """
        Tests GET (list) API for status code 200.
        This test aims to verify 'brand' filter when passing list as value.
        """
        query_string = "lat=-23.119919&lng=-47.707772&radius=50000&brand=[{0}]".format(self.laboratory_one.brand.id)
        url = "{0}?{1}".format(reverse('mobile:laboratory-list'), query_string)
        response = self.client.get(url)
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(data['results']), 1)

    def test_invalid_lat_get_list_api_400(self):
        """
        Tests GET (list) API for status code 400.
        """
        query_string = "lat=XXX&lng=-47.707772&radius=50000"
        url = "{0}?{1}".format(reverse('mobile:laboratory-list'), query_string)
        response = self.client.get(url)
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(data['status_code'], status.HTTP_400_BAD_REQUEST)
        self.assertEqual(data['detail'], "Request has been sent with errors: ['invalid lat it must be a float']")

    def test_invalid_lng_get_list_api_400(self):
        """
        Tests GET (list) API for status code 400.
        """
        query_string = "lat=-23.119919&lng=XXX&radius=50000"
        url = "{0}?{1}".format(reverse('mobile:laboratory-list'), query_string)
        response = self.client.get(url)
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(data['status_code'], status.HTTP_400_BAD_REQUEST)
        self.assertEqual(data['detail'], "Request has been sent with errors: ['invalid lng it must be a float']")

    def test_invalid_radius_get_list_api_400(self):
        """
        Tests GET (list) API for status code 400.
        """
        query_string = "lat=-23.119919&lng=-47.707772&radius=XXX"
        url = "{0}?{1}".format(reverse('mobile:laboratory-list'), query_string)
        response = self.client.get(url)
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(data['status_code'], status.HTTP_400_BAD_REQUEST)
        self.assertEqual(data['detail'], "Request has been sent with errors: ['invalid radius it must be an integer']")

    def test_invalid_brand_get_list_api_400(self):
        """
        Tests GET (list) API for status code 400.
        """
        query_string = "lat=-23.119919&lng=-47.707772&radius=50000&brand=XXX"
        url = "{0}?{1}".format(reverse('mobile:laboratory-list'), query_string)
        response = self.client.get(url)
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(data['status_code'], status.HTTP_400_BAD_REQUEST)
        self.assertEqual(data['detail'],
                         "Request has been sent with errors: ['invalid brand it must be an integer or list']")

    def test_no_lat_get_list_api_400(self):
        """
        Tests GET (list) API for status code 400.
        """
        query_string = "lng=-47.707772&radius=50000"
        url = "{0}?{1}".format(reverse('mobile:laboratory-list'), query_string)
        response = self.client.get(url)
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(data['status_code'], status.HTTP_400_BAD_REQUEST)
        self.assertEqual(data['detail'], "Request has been sent with errors: ['lat parameter is required']")

    def test_no_lng_get_list_api_400(self):
        """
        Tests GET (list) API for status code 400.
        """
        query_string = "lat=-23.119919&radius=50000"
        url = "{0}?{1}".format(reverse('mobile:laboratory-list'), query_string)
        response = self.client.get(url)
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(data['status_code'], status.HTTP_400_BAD_REQUEST)
        self.assertEqual(data['detail'], "Request has been sent with errors: ['lng parameter is required']")

    def test_no_radius_get_list_api_400(self):
        """
        Tests GET (list) API for status code 400.
        """
        query_string = "lat=-23.119919&lng=-47.707772"
        url = "{0}?{1}".format(reverse('mobile:laboratory-list'), query_string)
        response = self.client.get(url)
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(data['status_code'], status.HTTP_400_BAD_REQUEST)
        self.assertEqual(data['detail'], "Request has been sent with errors: ['radius parameter is required']")
