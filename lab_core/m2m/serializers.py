# encode: utf-8

import datetime

from django.db import transaction
from rest_framework import serializers

import domain.models as domain_models
from concierge.serializers import (PrescriptionSerializer)