# encode: utf-8

from django.conf import settings
from django.conf.urls import include, url
from rest_framework import routers
from rest_framework.schemas import get_schema_view
from rest_framework.urlpatterns import format_suffix_patterns

from . import views

router = routers.DefaultRouter(schema_title='M2M API')
# router.register('zendesk', views.MedicalPrescriptionViewSet, base_name="medicalprescription")

schema_view = get_schema_view(title='M2M API')

urlpatterns = [
    url('^clinic/results', views.results),
    url('^clinic/notify', views.crawler_push),
    url('^zendesk/update_prescription', views.update_prescription),
    url('^zendesk/update_adf_prescription', views.do_adf),
    url('^zendesk/check_adf', views.check_adf),
    url('^m2m/zendesk_prescription', views.ticket),
    url('^m2m/$', schema_view),
]

urlpatterns = format_suffix_patterns(urlpatterns)
urlpatterns += router.urls

if settings.DEBUG:
    import debug_toolbar

    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]
