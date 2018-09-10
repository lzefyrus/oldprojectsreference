# encode: utf-8

import datetime

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError, transaction
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework import parsers, renderers
from django.shortcuts import render

from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import mixins, status, viewsets
from rest_framework.versioning import URLPathVersioning

from domain.models import RecoverPassword
from domain.serializers import RecoverPasswordSerializer, ResetPasswordSerializer, ObtainExpirableTokenSerializer
from domain.utils import RequestLogViewMixin

from django.template.exceptions import TemplateDoesNotExist

class ObtainSSLConfirmation(APIView):
    """
    Returns hash code for SSL confirmation (Let's Crypt mandatory step).
    """
    throttle_classes = ()
    permission_classes = ()
    parser_classes = (parsers.FormParser, parsers.MultiPartParser, parsers.JSONParser,)
    renderer_classes = (renderers.JSONRenderer,)

    def get(self, request, *args, **kwargs):
        return HttpResponse(settings.LETSCRYPT_ACME_CONFIRMATION)

obtain_ssl_confirmation = ObtainSSLConfirmation.as_view()


class ObtainSSLConfirmationAgain(APIView):
    """
    Returns hash code for SSL confirmation (2nd confirmation) (Let's Crypt mandatory step).
    """
    throttle_classes = ()
    permission_classes = ()
    parser_classes = (parsers.FormParser, parsers.MultiPartParser, parsers.JSONParser,)
    renderer_classes = (renderers.JSONRenderer,)

    def get(self, request, *args, **kwargs):
        return HttpResponse(settings.LETSCRYPT_ACME_CONFIRMATION_2)

obtain_ssl_confirmation_again = ObtainSSLConfirmationAgain.as_view()


class ObtainExpirableToken(RequestLogViewMixin,
                           APIView):
    """
    Expirable Token API.
    """
    throttle_classes = ()
    permission_classes = ()
    parser_classes = (parsers.FormParser, parsers.MultiPartParser, parsers.JSONParser,)
    renderer_classes = (renderers.JSONRenderer,)
    serializer_class = AuthTokenSerializer

    def post(self, request, *args, **kwargs):
        """
        Creates an expirable token. It has basically two expiration rules:
        1st: a token itself lasts up to SETTINGS.TOKEN_EXPIRATION_IN_MINUTES if not refreshed.
        2nd: a token can only keep being refreshed up to SETTINGS.TOKEN_EXPIRATION_DELTA_IN_DAYS.
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token = ObtainExpirableTokenSerializer.get_new_token(user)

        return Response({'token': token.key})

obtain_auth_token = ObtainExpirableToken.as_view()


class RecoverPasswordView(RequestLogViewMixin,
                          mixins.CreateModelMixin,
                          viewsets.GenericViewSet):

    renderer_classes = (renderers.JSONRenderer,)
    queryset = RecoverPassword.objects.all()
    authentication_classes = ()
    permission_classes = []

    def get_serializer_class(self):
        if self.request.version == 'v3':
            return RecoverPasswordSerializer

    def create(self, request, *args, **kwargs):
        """
        Overwrites post method in order to handle IntegrityError and ObjectDoesNotExist.
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        serializer = RecoverPasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        try:
            serializer.save()
            return Response({})

        except (ObjectDoesNotExist, RuntimeError) as exc:
            return Response({"detail": str(exc),
                             "status_code": status.HTTP_400_BAD_REQUEST},
                            status=status.HTTP_400_BAD_REQUEST)
        except IntegrityError as ie:
            # Just in case unique field is repeated, generate another token
            response = serializer.create(request.data)
            return Response(RecoverPasswordSerializer(response).data)


class ResetPasswordView(RequestLogViewMixin,
                        mixins.ListModelMixin,
                        mixins.CreateModelMixin,
                        viewsets.GenericViewSet):

    queryset = RecoverPassword.objects.all()
    authentication_classes = ()
    permission_classes = []

    def get_serializer_class(self):
        if self.request.version == 'v3':
            return ResetPasswordSerializer

    def list(self, request, *args, **kwargs):
        """
        Overwrites get method in order to redirect to a custom schema in case of iOS devices
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        device_type = request.query_params.get(settings.DEVICE_TYPE_HEADERS, None)
        token = request.query_params.get("token", None)

        if device_type == settings.IOS:
            return self.__get_custom_redirect("resetPassword", token)

        return Response({})

    def create(self, request, *args, **kwargs):
        """
        Overwrites post method in order to handle IntegrityError and ObjectDoesNotExist.
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        serializer = ResetPasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        try:
            serializer.save()
            return Response({})

        except ObjectDoesNotExist as exc:
            return Response({"detail": "Token does not exist or has already been used before.",
                             "status_code": status.HTTP_400_BAD_REQUEST},
                            status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def __get_custom_redirect(path, token):
        custom_schema_url = "{0}{1}/{2}".format(settings.CUSTOM_SCHEMA, path, token)
        response = HttpResponse("", status=302)
        response['Location'] = custom_schema_url

        return response


class CurrentVersionView(mixins.ListModelMixin,
                        viewsets.GenericViewSet):
    authentication_classes = ()
    permission_classes = []

    def list(self, request, *args, **kwargs):
        """
        Returns current API version
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        return Response({"version": self.request.version})


api_version = CurrentVersionView.as_view({'get': 'list'})


@csrf_exempt
def health_monitor(request):
    """
    Health monitor URL in order to measure availability and downtime in /healthz endpoint
    :param request:
    :return:
    """
    return HttpResponse()


@csrf_exempt
def index(request):
    """
    Displays home page
    :param request:
    :return:
    """
    host = request.get_host()
    try:
        return render(request, 'domain/index_{}.html'.format(host.split('.')[0]))
    except TemplateDoesNotExist as e:
        return render(request, 'domain/index.html')


