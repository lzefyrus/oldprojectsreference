# encode: utf-8

from django.test.testcases import TestCase
from rest_framework import serializers

from domain.utils import swagrize

from .factory_models import *


class SampleSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Laboratory
        fields = ('external_id', 'lat', 'lng',)


class TestSwagerize(TestCase):

    def test_swagerize(self):
        spec = swagrize(SampleSerializer)
        self.assertTrue(spec)
        self.assertEqual(spec['type'], 'object')
        self.assertTrue(spec['properties']['lat'])
        self.assertEqual(spec['properties']['lat']['type'], 'number')
        self.assertEqual(spec['properties']['lat']['format'], 'float')
        self.assertEqual(spec['properties']['external_id']['type'], 'string')
