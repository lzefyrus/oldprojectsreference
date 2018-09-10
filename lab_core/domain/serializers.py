import datetime
import os
import uuid

from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction

from rest_framework import status
from rest_framework.authtoken.models import Token

from rest_framework import serializers

from domain.authentication import TokenCreation
from domain.mailer import Mail
from domain.models import *


class UserSerializer(serializers.ModelSerializer):

    id = serializers.PrimaryKeyRelatedField(read_only=True)
    email = serializers.EmailField(required=False)
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)

    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name')


class RecoverPasswordSerializer(serializers.ModelSerializer):
    token = serializers.CharField(read_only=True)
    email = serializers.EmailField(required=True, write_only=True)
    user = UserSerializer(read_only=True)
    expiration_date_timestamp = serializers.SerializerMethodField(read_only=True)
    is_used = serializers.BooleanField(read_only=True)

    class Meta:
        model = RecoverPassword
        fields = ('token', 'email', 'user', 'expiration_date_timestamp', 'is_used')

    @transaction.atomic
    def create(self, validated_data):
        """
        Manages recover password first step on `lost my password` feature.
        """
        with transaction.atomic():
            prepared_data = self._prepare_data(validated_data.copy())
            instance = super(RecoverPasswordSerializer, self).create(prepared_data)
            self._post_save(instance)

        return instance

    def _prepare_data(self, validated_data):
        """
        Prepares validated data.
        :param validated_data:
        :return:
        """
        validated_data['token'] = self.generate_random_string()
        validated_data['user'] = self.get_user_by_email(validated_data)
        validated_data['expiration_date'] = self.get_user_password_expiration_date()

        self._invalidate_existing_requests(validated_data['user'])
        return validated_data

    def _post_save(self, instance):
        """
        Performs actions after saving the instance
        :param instance:
        :return:
        """
        request = self.context.get('request')
        device_type = request.META.get(settings.DEVICE_TYPE_HEADERS, None)

        self._send_email(instance, device_type)

    @staticmethod
    def _send_email(instance, device_type=settings.ANDROID):
        """
        Sends the email with current token
        :param instance:
        :return:
        """
        link = "{0}/password/reset?token={1}".format(settings.DOMAIN_NAME, instance.token)

        if device_type == settings.IOS:
            link += "&{0}={1}".format(settings.DEVICE_TYPE_HEADERS, device_type)

        text = """
        <html>
            Olá, você acabou de requisitar a mudança da sua senha no aplicativo Sara, para alterar sua senha clique no link abaixo através do seu celular:
            <br><br>
            <a href={0}>{0}</a>
            <br><br>
            Lembramos que a duração desse código é de {1} horas. Caso este tempo expire, você precisará requisitar uma nova troca de senha.
            <br><br>
            Até mais!
            <br><br>
            Sara
        </html>
            """.format(link, settings.RESET_PASSWORD_EXPIRATION_IN_HOURS)

        Mail.send(to=instance.user.email, subject='Sara - Recuperação de senha', text=text, html=True)

    @staticmethod
    def _invalidate_existing_requests(user):
        """
        Invalidates all existing unused recover password requests
        :param user:
        :return:
        """
        existing_recover_requests = RecoverPassword.objects.filter(user=user.id,
                                                                   is_used=False)

        for request in existing_recover_requests:
            request.is_used = True
            request.save()

    @staticmethod
    def get_user_by_email(validated_data):
        """
        Returns user instance.
        :param validated_data:
        :return:
        """
        return User.objects.get(email=validated_data.pop('email', None))

    @staticmethod
    def get_expiration_date_timestamp(instance):
        """
        Retrieves timestamp dynamically.
        :param instance:
        :return:
        """
        try:
            return int(instance.expiration_date.timestamp())
        except:
            return None

    @staticmethod
    def get_user_password_expiration_date():
        """
        Returns expiration date for a "lost my password" request
        :return:
        """
        return datetime.datetime.now() + datetime.timedelta(hours=settings.RESET_PASSWORD_EXPIRATION_IN_HOURS)

    @staticmethod
    def generate_random_string():
        """
        Returns a random uuid string of 32 chars
        :return:
        """
        return uuid.uuid4().hex


class ResetPasswordSerializer(serializers.ModelSerializer):
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, write_only=True)
    new_password_confirmation = serializers.CharField(required=True, write_only=True)

    class Meta:
        model = RecoverPassword
        fields = ('token', 'new_password', 'new_password_confirmation')

    @transaction.atomic
    def create(self, validated_data):
        """
        Manages password reset on "lost my password".
        """
        with transaction.atomic():
            instance = self._get_recover(validated_data["token"])
            prepared_data = self._prepare_data(validated_data.copy())
            instance.__dict__.update(prepared_data)
            instance.save()
            self._post_save(instance, validated_data)

        return instance

    def _prepare_data(self, validated_data):
        """
        Prepares validated data.
        :param validated_data:
        :return:
        """
        validated_data['is_used'] = True
        self.match_passwords(validated_data.pop('new_password'), validated_data.pop('new_password_confirmation'))

        return validated_data

    def _post_save(self, instance, data):
        """
        Performs actions after saving the instance
        :param instance:
        :return:
        """
        self._save_user(instance.user, data["new_password"])

    @staticmethod
    def _get_recover(value):
        """
        Gets/Validates if current token is valid.
        :param value:
        :return:
        """
        recover = RecoverPassword.objects.get(token=value, is_used=False)

        if datetime.datetime.now() > recover.expiration_date:
            raise serializers.ValidationError({"token": "This token has expired. Ask for another one.",
                                               "status_code": status.HTTP_400_BAD_REQUEST})

        return recover

    @staticmethod
    def match_passwords(password, confirmation):
        """
        Validates password and confirmation.
        :param password:
        :param confirmation:
        :return:
        """
        if confirmation != password:
            raise serializers.ValidationError({"password": "Password/confirmation doesn't match.",
                                               "status_code": status.HTTP_400_BAD_REQUEST})

    @staticmethod
    def _save_user(user, new_password):
        if user.check_password(new_password):
            # Removed due to Liza's request:
            # raise serializers.ValidationError({"password": "Please, try another password. This one is being used.",
            #                                    "status_code": status.HTTP_400_BAD_REQUEST})
            return

        user.password = make_password(new_password)
        user.save()


class ObtainExpirableTokenSerializer(serializers.ModelSerializer):

    @classmethod
    @transaction.atomic
    def get_new_token(cls, user, key=None):
        """
        Creates a new Token or rewrite the previous one (always one active token per user)
        :param user:
        :param key:
        :return:
        """
        with transaction.atomic():
            try:
                token = Token.objects.get(user=user)

                # Delete current token in order to create a new one
                token.delete()
                token = cls._create_token(user, key)

            except ObjectDoesNotExist:
                token = cls._create_token(user, key)

                # Stores original creation date in order to have 2 expiration rules (usual and delta)
                token_creation = TokenCreation(user=user, created=token.created)
                token_creation.save()

            return token

    @staticmethod
    def _create_token(user, key):
        """
        Instantiate the new token
        :param user:
        :param key:
        :return:
        """
        if key:
            token = Token(user=user, created=datetime.datetime.now(), key=key)
        else:
            token = Token(user=user, created=datetime.datetime.now())
        token.save()

        return token


