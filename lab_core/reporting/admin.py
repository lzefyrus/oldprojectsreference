# encode: utf-8

from django.contrib import admin

from .models import *
from domain.models import ScheduledExam, MedicalPrescription

choices = ScheduledExam.STATUS_CHOICES + MedicalPrescription.STATUS_CHOICES


class GeneralStatusOptions(admin.ModelAdmin):
    raw_id_fields = ('prescription','exam','parent')
    # define the related_lookup_fields
    related_lookup_fields = {
        # 'content_type': ['content_type'],
        'prescription': ['prescription'],
        'medical exam': ['exam'],
        'parent status': ['parent'],
    }

admin.site.register(GeneralStatus, GeneralStatusOptions)