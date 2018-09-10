"""lab_core URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin
from rest_framework_jwt.views import obtain_jwt_token, verify_jwt_token

from concierge import urls as concierge_urls
from domain import views
from patient_api.urls import urlpatterns as patient_api_urls
from general_utils import urls as general_utils_urls
from m2m import urls as m2m_urls
from m2m import views as m2m_views

urlpatterns_default = [
    url(r'^concierge/', include(concierge_urls, namespace='concierge')),
    url(r'^grappelli/', include('grappelli.urls')),
    url(r'^admin/', admin.site.urls),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^mobile/', include(patient_api_urls, namespace='mobile')),
    url(r'^api-token-auth/', views.obtain_auth_token, name='token'),
    url(r'^docs/', include('rest_framework_docs.urls')),
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^api-jwt-token-auth/', obtain_jwt_token),
    url(r'^api-jwt-token-verify/', verify_jwt_token),
    url(r'^password/recover/', views.RecoverPasswordView.as_view({'post': 'create'}), name="recover_password"),
    url(r'^password/reset/', views.ResetPasswordView.as_view({'post': 'create', 'get': 'list'}), name="reset_password"),
    # url(r'.well-known/acme-challenge/{0}'.format(settings.LETSCRYPT_ACME_CHALENGE), views.obtain_ssl_confirmation, name="ssl_confirmation"),
    # url(r'.well-known/acme-challenge/{0}'.format(settings.LETSCRYPT_ACME_CHALENGE_2), views.obtain_ssl_confirmation_again, name="ssl_confirmation_again"),
    url(r'^healthz/', views.health_monitor),
    url(r'^version/', views.api_version),
    url(r'^$', views.index, name='index'),
    url(r'^zendesk$', m2m_views.index),
    url(r'', include(general_utils_urls, namespace='general_utils')),
    url(r'', include(m2m_urls, namespace='clinic')),
]

urlpatterns_v3 = [
    url(r'^(?P<version>(v3|v3))/concierge/', include(concierge_urls, namespace='concierge')),
    url(r'^grappelli/', include('grappelli.urls')),
    url(r'^admin/', admin.site.urls),
    url(r'^(?P<version>(v3|v3))/api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^(?P<version>(v3|v3))/mobile/', include(patient_api_urls, namespace='mobile')),
    url(r'^(?P<version>(v3|v3))/api-token-auth/', views.obtain_auth_token, name='token'),
    url(r'^(?P<version>(v3|v3))/docs/', include('rest_framework_docs.urls')),
    url(r'^(?P<version>(v3|v3))/admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^(?P<version>(v3|v3))/api-jwt-token-auth/', obtain_jwt_token),
    url(r'^(?P<version>(v3|v3))/api-jwt-token-verify/', verify_jwt_token),
    url(r'^(?P<version>(v3|v3))/password/recover/', views.RecoverPasswordView.as_view({'post': 'create'}), name="recover_password"),
    url(r'^(?P<version>(v3|v3))/password/reset/', views.ResetPasswordView.as_view({'post': 'create', 'get': 'list'}), name="reset_password"),
    # url(r'.well-known/acme-challenge/{0}'.format(settings.LETSCRYPT_ACME_CHALENGE), views.obtain_ssl_confirmation, name="ssl_confirmation"),
    # url(r'.well-known/acme-challenge/{0}'.format(settings.LETSCRYPT_ACME_CHALENGE_2), views.obtain_ssl_confirmation_again, name="ssl_confirmation_again"),
    url(r'^healthz/', views.health_monitor),
    url(r'^(?P<version>(v3|v3))/version/', views.api_version),
    url(r'^$', views.index, name='index'),
]

urlpatterns_v4 = [
    url(r'^(?P<version>(v4|v4))/concierge/', include(concierge_urls, namespace='concierge')),
    url(r'^grappelli/', include('grappelli.urls')),
    url(r'^admin/', admin.site.urls),
    url(r'^(?P<version>(v4|v4))/api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^(?P<version>(v4|v4))/mobile/', include(patient_api_urls, namespace='mobile')),
    url(r'^(?P<version>(v4|v4))/api-token-auth/', views.obtain_auth_token, name='token'),
    url(r'^(?P<version>(v4|v4))/docs/', include('rest_framework_docs.urls')),
    url(r'^(?P<version>(v4|v4))/admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^(?P<version>(v4|v4))/api-jwt-token-auth/', obtain_jwt_token),
    url(r'^(?P<version>(v4|v4))/api-jwt-token-verify/', verify_jwt_token),
    url(r'^(?P<version>(v4|v4))/password/recover/', views.RecoverPasswordView.as_view({'post': 'create'}), name="recover_password"),
    url(r'^(?P<version>(v4|v4))/password/reset/', views.ResetPasswordView.as_view({'post': 'create', 'get': 'list'}), name="reset_password"),
    # url(r'.well-known/acme-challenge/{0}'.format(settings.LETSCRYPT_ACME_CHALENGE), views.obtain_ssl_confirmation, name="ssl_confirmation"),
    # url(r'.well-known/acme-challenge/{0}'.format(settings.LETSCRYPT_ACME_CHALENGE_2), views.obtain_ssl_confirmation_again, name="ssl_confirmation_again"),
    url(r'^healthz/', views.health_monitor),
    url(r'^(?P<version>(v4|v4))/version/', views.api_version),
    url(r'^$', views.index, name='index'),
]

urlpatterns_v5 = [
    url(r'^(?P<version>(v5|v5))/concierge/', include(concierge_urls, namespace='concierge')),
    url(r'^grappelli/', include('grappelli.urls')),
    url(r'^admin/', admin.site.urls),
    url(r'^(?P<version>(v5|v5))/api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^(?P<version>(v5|v5))/mobile/', include(patient_api_urls, namespace='mobile')),
    url(r'^(?P<version>(v5|v5))/api-token-auth/', views.obtain_auth_token, name='token'),
    url(r'^(?P<version>(v5|v5))/docs/', include('rest_framework_docs.urls')),
    url(r'^(?P<version>(v5|v5))/admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^(?P<version>(v5|v5))/api-jwt-token-auth/', obtain_jwt_token),
    url(r'^(?P<version>(v5|v5))/api-jwt-token-verify/', verify_jwt_token),
    url(r'^(?P<version>(v5|v5))/password/recover/', views.RecoverPasswordView.as_view({'post': 'create'}), name="recover_password"),
    url(r'^(?P<version>(v5|v5))/password/reset/', views.ResetPasswordView.as_view({'post': 'create', 'get': 'list'}), name="reset_password"),
    # url(r'.well-known/acme-challenge/{0}'.format(settings.LETSCRYPT_ACME_CHALENGE), views.obtain_ssl_confirmation, name="ssl_confirmation"),
    # url(r'.well-known/acme-challenge/{0}'.format(settings.LETSCRYPT_ACME_CHALENGE_2), views.obtain_ssl_confirmation_again, name="ssl_confirmation_again"),
    url(r'^healthz/', views.health_monitor),
    url(r'^(?P<version>(v5|v5))/version/', views.api_version),
    url(r'^$', views.index, name='index'),
]
# Add more versions here as they appear:
urlpatterns = urlpatterns_default + urlpatterns_v3 + urlpatterns_v4 + urlpatterns_v5

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
