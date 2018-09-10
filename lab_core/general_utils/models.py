# encode: utf-8

from django.db import models
from django_extensions.db.models import TimeStampedModel


# Create your models here.

MOBILE_CHOICES = (
    (0, 'All'),
    (1, 'Android'),
    (2, 'IOS'),
    (3, 'Mac OS'),
    (4, 'Windows'),
    (5, 'Linux'),
    (6, 'Unix'),
    (7, 'TVOS'),
    (100, 'None'),
)

class LetsencryptModel(TimeStampedModel):
    id = models.CharField(primary_key=True, max_length=50)
    content = models.TextField(null=False, blank=False)

    def __str__(self):
        return "%s" % self.id


class MobileSettings(TimeStampedModel):

    key = models.CharField(max_length=100, null=False, blank=False)
    key_value = models.CharField(max_length=100, null=False, blank=False)
    # device = models.PositiveIntegerField(choices=MOBILE_CHOICES, default=0)

    def __str__(self):
        return "%s-%s" % (self.key, self.key_value)

    # class Meta:
    #     unique_together = (("device", "key"),)