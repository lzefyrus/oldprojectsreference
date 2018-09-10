# encode: utf-8

import datetime
import os

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django_extensions.db.models import TimeStampedModel
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import AuthenticationFailed


class TokenCreation(TimeStampedModel):
    """
    Persists token creation date in order to implement TOKEN_EXPIRATION_DELTA rule.
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, primary_key=True, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)


class ExpirableTokenAuthentication(TokenAuthentication):
    """
    Expirable Token Authorization rules.
    """

    def authenticate_credentials(self, key):
        """
        1) Verifies if token with 'key' exists.
        2) Verifies if token's owner is active and has its email confirmed.
        3) A token can only keep being refreshed up to SETTINGS.TOKEN_EXPIRATION_DELTA_IN_DAYS.
        4) A token itself lasts up to SETTINGS.TOKEN_EXPIRATION_IN_MINUTES.
        :param key:
        :return:
        """
        try:
            token = Token.objects.get(key=key)
        except ObjectDoesNotExist:
            raise AuthenticationFailed('Invalid token')

        if not token.user.is_active:
            raise AuthenticationFailed('User inactive or deleted')

        # TODO: return this when email confirmation becomes mandatory again
        # try:
        #     from domain.models import Patient  # avoiding circular dependency
        #     patient = Patient.objects.get(pk=token.user.id)
        #     if not patient.is_confirmed:
        #         raise AuthenticationFailed('User email is not confirmed. Confirm it and then retry')
        # except ObjectDoesNotExist:
        #     pass

        utc_now = datetime.datetime.now()
        try:
            token_creation = TokenCreation.objects.get(pk=token.user.id)
        except ObjectDoesNotExist:
            raise AuthenticationFailed('Invalid token')

        if token_creation.created + datetime.timedelta(**self.token_expiration_delta) < utc_now:
            token_creation.delete()
            token.delete()
            raise AuthenticationFailed("Token has expired permanently and can't be refreshed")

        if token.created + datetime.timedelta(**self.token_expiration) < utc_now:
            raise AuthenticationFailed('Token has expired')

        # Refresh token's lifetime
        token.created += datetime.timedelta(**self.token_expiration)
        token.save()

        return token.user, token

    @property
    def token_expiration(self):
        """
        Returns token expiration kwargs.
        :return:
        """
        if os.environ.get('RUNNING_TESTS', False):
            return {'seconds': settings.TOKEN_EXPIRATION_IN_SECONDS}

        return {'minutes': settings.TOKEN_EXPIRATION_IN_MINUTES}

    @property
    def token_expiration_delta(self):
        """
        Returns token expiration delta kwargs.
        :return:
        """
        if os.environ.get('RUNNING_TESTS', False):
            return {'seconds': settings.TOKEN_EXPIRATION_DELTA_IN_SECONDS}

        return {'days': settings.TOKEN_EXPIRATION_DELTA_IN_DAYS}
