# encode: utf-8

from django.conf import settings
from django.conf.urls import include, url
from rest_framework import routers
from rest_framework.schemas import get_schema_view
from rest_framework.urlpatterns import format_suffix_patterns

from . import views

router = routers.DefaultRouter(schema_title='General Utils')

schema_view = get_schema_view(title='General Utils')

urlpatterns = [
    url(r'^$', schema_view),
    url(r'^(?P<version>(v3|v3|v4|v4|v5|v5))/appconfig$', views.mobile_settings),
    url(r'^(?P<version>(v3|v3|v4|v4|v5|v5))/mobile/appconfig$', views.mobile_settings),
    url(r'^.well-known\/acme-challenge\/(?P<acme_challenge>.*)$', views.lets_encrypt_acme),
]

# urlpatterns = format_suffix_patterns(urlpatterns)
# urlpatterns += router.urls
