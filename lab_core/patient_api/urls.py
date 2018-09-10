# encode: utf-8

from django.conf import settings
from django.conf.urls import include, url
from rest_framework import routers
from rest_framework.schemas import get_schema_view
from rest_framework.urlpatterns import format_suffix_patterns

from patient_api.views import *

router = routers.DefaultRouter(schema_title='Patient Mobile API')
router.register(r'exam', ExamViewSet)
router.register(r'laboratory', LaboratoryViewSet, base_name='laboratory')
router.register(r'laboratory-brand', LaboratoryBrandViewSet, base_name='brand')
router.register(r'patient', PatientViewSet)
router.register(r'prescription', MedicalPrescriptionViewSet, base_name='prescription')
router.register(r'phone-call', ScheduledExamPhoneCallViewSet, base_name='phone-call')
router.register(r'scheduled-exam', ScheduledExamViewSet, base_name='scheduled-exam')
router.register(r'holidays', HolidayViewSet, base_name='holidays')

schema_view = get_schema_view(title='Patient API')

urlpatterns = [
    url('^$', schema_view),
]

urlpatterns = format_suffix_patterns(urlpatterns)
urlpatterns += router.urls

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]
