# encode: utf-8

from django.conf import settings
from django.conf.urls import include, url
from rest_framework import routers
from rest_framework.schemas import get_schema_view
from rest_framework.urlpatterns import format_suffix_patterns

from . import views

router = routers.DefaultRouter(schema_title='Concierge Frontend API')
router.register('operator', views.OperatorViewSet, base_name='operator')
router.register('patient', views.PatientRetrieveViewSet)
router.register('prescription', views.MedicalPrescriptionViewSet)
router.register('insuranceCompany', views.InsuranceCompanyViewSet)
router.register('exam', views.ExamViewSet)
router.register('laboratory', views.LaboratoryViewSet)
router.register('dashboard', views.DashboardViewSet, base_name='dashboard')
router.register('scheduled-exam', views.ScheduledExamViewSet)
router.register('phone-call', views.ExamPhoneCallViewSet)
router.register('health-insurance', views.HealthInsuranceViewSet)
router.register('health-insurance-plan', views.HealthInsurancePlanViewSet)
router.register('rejection-reason', views.RejectionReasonListViewSet)
router.register('preparation-step', views.PreparationStepViewSet)


schema_view = get_schema_view(title='Concierge API')

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
