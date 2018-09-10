# encode: utf-8

import reversion
import uuid

from django.conf import settings
from django.contrib.gis.db import models as geo_models
from django.db import models
# from domain import models as domain_models
from django_extensions.db.models import TimeStampedModel
from django.contrib.postgres.fields import JSONField
from domain import utils

@reversion.register()
class ZendeskTicket(TimeStampedModel):
    external_id = models.CharField(max_length=50, null=True, blank=True, db_index=True)
    prescription = models.OneToOneField('domain.MedicalPrescription')
    content = JSONField()
    # Set to false to hide this laboratory brand plus its unities (Laboratory) from the user

    class Meta:
        ordering = ['external_id']

    def __str__(self):
        return "%s: %s" % (self.external_id, self.prescription.id)

class ZendeskASFTicket(TimeStampedModel):
    external_id = models.CharField(max_length=50, null=True, blank=True, db_index=True)
    content = JSONField()

    class Meta:
        ordering = ['external_id']

    def __str__(self):
        return "ZD ADF Ticket: %s" % (self.external_id)
