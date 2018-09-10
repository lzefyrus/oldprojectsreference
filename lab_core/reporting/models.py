# encode: utf-8

from django.contrib.contenttypes.models import ContentType
from django.db import models
from django_extensions.db.models import TimeStampedModel

from domain.models import MedicalPrescription, ScheduledExam


# Create your models here.


class GeneralStatus(TimeStampedModel):
    content_type = models.ForeignKey(ContentType)
    date_set = models.DateTimeField(null=False, unique=True)
    status = models.CharField(null=False, blank=False, max_length=150, db_index=True)
    prescription = models.ForeignKey(MedicalPrescription)
    exam = models.ForeignKey(ScheduledExam, null=True, blank=True)
    parent = models.ForeignKey("GeneralStatus", null=True, blank=True)
    ttl = models.FloatField(default=0.0, db_index=True)

    def __str__(self):
        return "%s:%s:%s" % (self.content_type.model, self.status, self.date_set.isoformat())
        # class Meta:
        #     unique_together = (("parent", "content_type"),)
