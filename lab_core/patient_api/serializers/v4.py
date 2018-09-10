
import datetime

from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.core.validators import URLValidator
from django.db import IntegrityError, transaction
from rest_framework import serializers
from domain.mailer import Mail
from domain.models import *
from domain.tasks import create_images
from domain.utils import get_date_from_timestamp
from patient_api.serializers.v3 import HealthInsurancePlanSerializer, ScheduledExamSerializer
from patient_api.utils import (
    get_prescription_version,
    get_scheduled_exam_version
)
from patient_api.validators import Base64Validator


class PictureRetrieveMixin(object):

    def _get_picture_uri(self, picture_name, instance):
        """
        Retrieves absolute URI of a picture.
        :param picture_name:
        :param instance:
        :return:
        """
        try:
            request = self.context.get('request')
            picture_url = getattr(instance, picture_name).url
            return request.build_absolute_uri(picture_url)
        except:
            return ""


class PrescriptionPieceSerializer(serializers.ModelSerializer, PictureRetrieveMixin):
    expiration_date_timestamp = serializers.SerializerMethodField()
    prescription_issued_at_timestamp = serializers.SerializerMethodField()
    picture = serializers.SerializerMethodField()

    class Meta:
        model = PrescriptionPiece
        fields = (
            'id',
            'picture',
            'annotations',
            'doctor_crm',
            'exams_not_registered',
            'expiration_date_timestamp',
            'prescription_issued_at_timestamp',
            'status'
        )

    @staticmethod
    def get_expiration_date_timestamp(piece):
        """
        Retrieves expiration_date timestamp dynamically.
        :param piece:
        :return:
        """
        try:
            return int(piece.expiration_date.timestamp())
        except:
            return None

    @staticmethod
    def get_prescription_issued_at_timestamp(piece):
        """
        Retrieves prescription_issued_at timestamp dynamically.
        :param piece:
        :return:
        """
        try:
            return int(piece.prescription_issued_at.timestamp())
        except:
            return None

    def get_picture(self, piece):
        """
        Retrieves picture dynamically.
        :param piece:
        :return:
        """
        return self.context.get('request').data.get(
            'piece_{}_link'.format(piece.pk),
            self._get_picture_uri('picture', piece)
        )


class MedicalPrescriptionV4Serializer(serializers.ModelSerializer, PictureRetrieveMixin):
    id = serializers.PrimaryKeyRelatedField(read_only=True)
    picture_insurance_card_front = serializers.CharField(required=True, write_only=True, validators=[Base64Validator()])
    picture_insurance_card_back = serializers.CharField(required=False, write_only=True, validators=[Base64Validator()])

    picture_insurance_card_front_uploadcare = serializers.CharField(required=True, write_only=True, validators=[URLValidator()])
    picture_insurance_card_back_uploadcare = serializers.CharField(required=False, write_only=True, validators=[URLValidator()])

    picture_insurance_card_front_url = serializers.SerializerMethodField()
    picture_insurance_card_back_url = serializers.SerializerMethodField()
    picture_id_front_url = serializers.SerializerMethodField()
    picture_id_back_url = serializers.SerializerMethodField()
    selfie_url = serializers.SerializerMethodField()

    picture_insurance_card_front_uploadcare_url = serializers.SerializerMethodField()
    picture_insurance_card_back_uploadcare_url = serializers.SerializerMethodField()
    picture_id_front_uploadcare_url = serializers.SerializerMethodField()
    picture_id_back_uploadcare_url = serializers.SerializerMethodField()
    selfie_uploadcare_url = serializers.SerializerMethodField()

    health_insurance_plan = HealthInsurancePlanSerializer(read_only=True)
    latest_prescription = None
    modified_at_timestamp = serializers.SerializerMethodField(read_only=True)
    preferred_date_to_schedule_timestamp = serializers.SerializerMethodField(read_only=True)
    pieces = PrescriptionPieceSerializer(many=True)

    ungrouped_scheduled_exams = serializers.SerializerMethodField()
    grouped_scheduled_exams = serializers.SerializerMethodField()

    class Meta:
        model = MedicalPrescription
        fields = (
            'id', 'health_insurance_plan', 'status', 'patient',
            'insurance_company', 'picture_insurance_card_front', 'picture_insurance_card_back',
            'picture_insurance_card_front_url',
            'picture_insurance_card_back_url', 'picture_id_front_url',
            'picture_id_back_url', 'selfie_url', 'modified_at_timestamp',
            'additional_info', 'period_info', 'pieces',

            'picture_insurance_card_front_uploadcare',
            'picture_insurance_card_back_uploadcare',
            'picture_id_back_uploadcare',
            'picture_id_front_uploadcare',
            'selfie_uploadcare',


            'ungrouped_scheduled_exams',
            'grouped_scheduled_exams'

        )

    def get_picture_insurance_card_front_url(self, prescription):
        """
        Retrieves picture URL.
        :param prescription:
        :return:
        """
        return self._get_picture_uri("picture_insurance_card_front", prescription)

    @staticmethod
    def get_modified_at_timestamp(prescription):
        """
        Retrieves modified_at as timestamp dynamically.
        :param prescription:
        :return:
        """
        try:
            return int(prescription.modified.timestamp())
        except:
            return None

    @staticmethod
    def get_preferred_date_to_schedule_timestamp(prescription):
        """
        Retrieves preferred_date_to_schedule as timestamp dynamically.
        :param prescription:
        :return:
        """
        try:
            return int(prescription.preferred_date_to_schedule.timestamp())
        except:
            return None

    def get_picture_insurance_card_back_url(self, prescription):
        """
        Retrieves picture URL.
        :param prescription:
        :return:
        """
        return self._get_picture_uri("picture_insurance_card_back", prescription)

    def get_picture_id_front_url(self, prescription):
        """
        Retrieves picture URL.
        :param prescription:
        :return:
        """
        return self._get_picture_uri("picture_id_front", prescription.patient)

    def get_picture_id_back_url(self, prescription):
        """
        Retrieves picture URL.
        :param prescription:
        :return:
        """
        return self._get_picture_uri("picture_id_back", prescription.patient)

    def get_selfie_url(self, prescription):
        """
        Retrieves picture URL.
        :param prescription:
        :return:
        """
        return self._get_picture_uri("selfie", prescription.patient)

    def get_picture_insurance_card_front_uploadcare_url(self, prescription):
        """
        Retrieves picture URL.
        :param prescription:
        :return:
        """
        return self.context.get('request').data.get(
            'picture_insurance_card_front_uploadcare',
            self._get_picture_uri('picture_insurance_card_front_uploadcare', prescription)
        )

    def get_picture_insurance_card_back_uploadcare_url(self, prescription):
        """
        Retrieves picture URL.
        :param prescription:
        :return:
        """
        return self.context.get('request').data.get(
            'picture_insurance_card_back_uploadcare',
            self._get_picture_uri('picture_insurance_card_back_uploadcare', prescription)
        )

    def get_picture_id_front_uploadcare_url(self, prescription):
        """
        Retrieves picture URL.
        :param prescription:
        :return:
        """
        patient_data = self.context.get('request').data.get('patient', None)
        if patient_data:
            return patient_data.get(
                'picture_id_front_uploadcare',
                self._get_picture_uri('picture_id_front_uploadcare', prescription)
            )
        return self._get_picture_uri('picture_id_front_uploadcare', prescription)

    def get_picture_id_back_uploadcare_url(self, prescription):
        """
        Retrieves picture URL.
        :param prescription:
        :return:
        """
        patient_data = self.context.get('request').data.get('patient', None)
        if patient_data:
            return patient_data.get(
                'picture_id_back_uploadcare',
                self._get_picture_uri('picture_id_back_uploadcare', prescription)
            )
        return self._get_picture_uri('picture_id_back_uploadcare', prescription)

    def get_selfie_uploadcare_url(self, prescription):
        """
        Retrieves picture URL.
        :param prescription:
        :return:
        """
        patient_data = self.context.get('request').data.get('patient', None)
        if patient_data:
            return patient_data.get(
                'selfie_uploadcare',
                self._get_picture_uri('selfie_uploadcare', prescription)
            )
        return self._get_picture_uri('selfie_uploadcare', prescription)

    @staticmethod
    def get_ungrouped_scheduled_exams(instance):
        """
        Gets all nested ScheduledExam instances which are not grouped
        :param instance:
        :return:
        """
        exams = []
        for piece in instance.pieces.all():
            for exam in piece.scheduled_exams.filter(is_grouped=False):
                exams.append(exam)
        return ScheduledExamSerializer(exams, many=True).data

    @staticmethod
    def get_grouped_scheduled_exams(instance):
        """
        Gets all nested ScheduledExam instances which are grouped
        :param instance:
        :return:
        """
        exams = []
        for piece in instance.pieces.all():
            for exam in piece.scheduled_exams.filter(is_grouped=True):
                exams.append(exam)

        return ScheduledExamSerializer(exams, many=True).data


class MedicalPrescriptionByPatientV4Serializer(MedicalPrescriptionV4Serializer):

    insurance_company_id = serializers.SerializerMethodField()
    created_timestamp = serializers.SerializerMethodField()
    status_versions = serializers.SerializerMethodField()
    health_insurance_plan = HealthInsurancePlanSerializer(read_only=True)
    expiration_date_timestamp = serializers.SerializerMethodField()

    class Meta:
        model = MedicalPrescription
        fields = (
            'id', 'insurance_company_id', 'created_timestamp', 'status_versions',
            'status', 'selfie_id_matches', 'health_insurance_plan',
            'picture_insurance_card_front_url',
            'picture_insurance_card_back_url', 'picture_id_back_url',
            'picture_id_front_url', 'selfie_url', 'modified_at_timestamp', 'additional_info',
            'expiration_date_timestamp', 'period_info', 'pieces',

            'picture_insurance_card_front_uploadcare_url',
            'picture_insurance_card_back_uploadcare_url',
            'picture_id_back_uploadcare_url',
            'picture_id_front_uploadcare_url',
            'selfie_uploadcare_url',

            'ungrouped_scheduled_exams',
            'grouped_scheduled_exams',
            'pieces'
        )

    @staticmethod
    def get_scheduled_exams(prescription):
        return ScheduledExamSerializer(ScheduledExam.objects.filter(
            prescription=prescription.id), many=True).data

    @staticmethod
    def get_insurance_company_id(prescription):
        """
        Retrieves insurance_company_id dynamically.
        :param prescription:
        :return:
        """
        try:
            return prescription.insurance_company.id
        except AttributeError:
            return None

    @staticmethod
    def get_created_timestamp(prescription):
        """
        Retrieves timestamp dynamically.
        :param prescription:
        :return:
        """
        try:
            return int(prescription.created.timestamp())
        except:
            return None

    @staticmethod
    def get_status_versions(prescription):
        """
        Retrieves status versions dynamically.
        :param prescription:
        :return:
        """
        try:
            return get_prescription_version(prescription, "status")
        except:
            return []

    @staticmethod
    def get_expiration_date_timestamp(prescription):
        """
        Retrieves expiration_date timestamp dynamically.
        :param prescription:
        :return:
        """
        try:
            return int(prescription.expiration_date.timestamp())
        except:
            return None


class MedicalPrescriptionRetrieveV4Serializer(MedicalPrescriptionV4Serializer):
    patient_id = serializers.SerializerMethodField()
    insurance_company_id = serializers.SerializerMethodField()
    health_insurance_plan = HealthInsurancePlanSerializer()

    class Meta:
        model = MedicalPrescription
        fields = (
            'id', 'health_insurance_plan', 'status',
            'picture_insurance_card_front', 'picture_insurance_card_back',
            'picture_insurance_card_front_url', 'picture_insurance_card_back_url',
            'picture_id_front_url', 'picture_id_back_url', 'selfie_url',
            'patient_id', 'insurance_company_id', 'modified_at_timestamp', 'additional_info', 'period_info', 'pieces',

            'picture_insurance_card_front_uploadcare_url',
            'picture_insurance_card_back_uploadcare_url',
            'picture_id_back_uploadcare_url',
            'picture_id_front_uploadcare_url',
            'selfie_uploadcare_url',


            'ungrouped_scheduled_exams',
            'grouped_scheduled_exams'
        )

    @staticmethod
    def get_patient_id(prescription):
        """
        Retrieves patient id.
        :param prescription:
        :return:
        """
        try:
            return prescription.patient.user.id
        except AttributeError:
            return None

    @staticmethod
    def get_insurance_company_id(prescription):
        """
        Retrieves insurance_company id.
        :param prescription:
        :return:
        """
        try:
            return prescription.insurance_company.id
        except AttributeError:
            return None


class MedicalPrescriptionUpdateV4Serializer(MedicalPrescriptionV4Serializer, PictureRetrieveMixin):

    patient = serializers.DictField(required=False, write_only=True)
    picture_insurance_card_front = serializers.CharField(required=False, write_only=True, validators=[Base64Validator()])
    picture_insurance_card_back = serializers.CharField(required=False, write_only=True, validators=[Base64Validator()])
    picture_insurance_card_front_uploadcare = serializers.CharField(required=False, write_only=True, validators=[URLValidator()])
    picture_insurance_card_back_uploadcare = serializers.CharField(required=False, write_only=True, validators=[URLValidator()])
    health_insurance_plan = HealthInsurancePlanSerializer(read_only=True)
    pieces = serializers.ListField(required=False)

    class Meta:
        model = MedicalPrescription
        fields = (
            'id',
            'health_insurance_plan',
            'status',
            'picture_insurance_card_front',
            'picture_insurance_card_back',
            'picture_insurance_card_front_url',
            'picture_insurance_card_back_url',
            'picture_id_front_url',
            'picture_id_back_url',
            'selfie_url',
            'insurance_company_id',
            'patient',
            'modified_at_timestamp',
            'additional_info',
            'period_info',
            'pieces',

            'picture_insurance_card_front_uploadcare',
            'picture_insurance_card_back_uploadcare',
            'picture_insurance_card_front_uploadcare_url',
            'picture_insurance_card_back_uploadcare_url',
            'picture_id_front_uploadcare_url',
            'picture_id_back_uploadcare_url',
            'selfie_uploadcare_url',

            'ungrouped_scheduled_exams',
            'grouped_scheduled_exams'
        )

    @transaction.atomic
    def update(self, instance, validated_data):
        """
        Update and return an existing `MedicalPrescription` instance, given the validated data.
        """
        with transaction.atomic():

            # Latest prescription update
            self.latest_prescription = instance

            async_data = {}
            patient = self._save_patient(instance, validated_data.pop('patient', None), async_data)

            # Pictures update
            self._update_images(instance, validated_data, patient)
            picture_insurance_card_front_uploadcare = validated_data.pop("picture_insurance_card_front_uploadcare", None)
            picture_insurance_card_back_uploadcare = validated_data.pop("picture_insurance_card_back_uploadcare", None)

            # Set dependencies from ids
            self._set_insurance_company(validated_data, instance)

            # Save prescription
            instance.__dict__.update(validated_data)
            instance.save()

            # Set prescription pieces, if provided:
            pieces = validated_data.pop("pieces", None)
            pieces_images_data = self._save_pieces(pieces, instance) if pieces else None

            # Save pictures from Uploadcare, asynchronously
            self._upload_images_async(instance, async_data, picture_insurance_card_front_uploadcare,
                                      picture_insurance_card_back_uploadcare, pieces_images_data)

            return instance

    def _upload_images_async(self, instance, async_data, picture_insurance_card_front_uploadcare,
                             picture_insurance_card_back_uploadcare, pieces_images_data):
        """
        Asynchronously save images to default storage
        :param instance:
        :param async_data:
        :param picture_insurance_card_front_uploadcare:
        :param picture_insurance_card_back_uploadcare:
        :param pieces_images_data:
        :return:
        """
        async_data.update(
            {
                'get_pictures_method': 'get_picture_as_content_file_uploadcare',
                'prescription_id': instance.pk,
                'picture_insurance_card_front_uploadcare': picture_insurance_card_front_uploadcare,
                'picture_insurance_card_back_uploadcare': picture_insurance_card_back_uploadcare,
                'pieces': pieces_images_data
            }
        )
        if self.latest_prescription:
            async_data['latest_prescription_pk'] = self.latest_prescription.pk

        create_images.apply_async(
            kwargs=async_data,
            countdown=5,
        )

    def _update_images(self, instance, validated_data, patient):
        """
        Updates images according to ones provided in the request
        :param instance:
        :param validated_data:
        :param patient:
        :return:
        """
        if validated_data.get("picture_insurance_card_front", None):
            instance.picture_insurance_card_front = self._get_picture_as_content_file(
                validated_data,
                "picture_insurance_card_front"
            )
            # TODO: remove these fields when base64 apps version is no longer supported
            validated_data["picture_insurance_card_front"] = instance.picture_insurance_card_front
            validated_data["picture_insurance_card_front_uploadcare"] = instance.picture_insurance_card_front_uploadcare

        if validated_data.get("picture_insurance_card_back", None):
            instance.picture_insurance_card_back = self._get_picture_as_content_file(
                validated_data,
                "picture_insurance_card_back"
            )
            # TODO: remove these fields when base64 apps version is no longer supported
            validated_data["picture_insurance_card_back"] = instance.picture_insurance_card_back
            validated_data["picture_insurance_card_back_uploadcare"] = instance.picture_insurance_card_back_uploadcare

        if patient:
            instance.patient = patient

            # TODO: remove these fields when base64 apps version is no longer supported
            validated_data["picture_id_front"] = patient.picture_id_front
            validated_data["picture_id_back"] = patient.picture_id_back
            validated_data["selfie"] = patient.selfie

            validated_data["picture_id_front_uploadcare"] = patient.picture_id_front_uploadcare
            validated_data["picture_id_back_uploadcare"] = patient.picture_id_back_uploadcare
            validated_data["selfie_uploadcare"] = patient.selfie_uploadcare

    def _save_pieces(self, pieces, instance):
        """
        Saves nested pieces objects
        :param pieces:
        :param instance:
        :return:
        """
        pieces_images_data = []
        existing_pieces = PrescriptionPiece.objects.filter(prescription=instance)
        existing_pieces_pks = set(existing_pieces.values_list("pk", flat=True))
        piece_pks = []

        for piece_data in pieces:
            picture = piece_data.pop('picture', None)
            pk = piece_data.get("id", None)
            if not pk:
                prescription_piece = PrescriptionPiece.objects.create(prescription=instance)
                self.context.get('request').data['piece_{}_link'.format(prescription_piece.pk)] = picture
                pk = prescription_piece.pk
            else:
                piece_pks.append(pk)

            pieces_images_data.append({
                'pk': pk,
                'picture': picture
            })

        # Delete missing pieces which were not provided on request
        pks_to_delete = list(existing_pieces_pks - set(piece_pks))
        existing_pieces.filter(pk__in=pks_to_delete).delete()

        return pieces_images_data

    def _save_patient(self, instance, patient_data, async_data):
        """
        Saves patient using patient data.
        :param patient_data:
        :param async_data:
        :return:
        """
        if not patient_data:
            return None

        patient = Patient.objects.get(pk=instance.patient.user.id)

        # Parsing images to ContentFile
        patient.picture_id_front = self._get_picture_as_content_file(patient_data, "picture_id_front")
        patient.picture_id_back = self._get_picture_as_content_file(patient_data, "picture_id_back")
        patient.selfie = self._get_picture_as_content_file(patient_data, "selfie")

        picture_id_front_uploadcare = patient_data.pop("picture_id_front_uploadcare", None)
        picture_id_back_uploadcare = patient_data.pop("picture_id_back_uploadcare", None)
        selfie_uploadcare = patient_data.pop("selfie_uploadcare", None)

        # Save it
        patient.save()
        # Upload pictures from uploadcare asynchronously
        async_data.update(
            {
                'get_pictures_method': 'get_picture_as_content_file_uploadcare',
                'patient_id': patient.pk,
                'picture_id_front_uploadcare': picture_id_front_uploadcare,
                'picture_id_back_uploadcare': picture_id_back_uploadcare,
                'selfie_uploadcare': selfie_uploadcare
            }
        )
        if self.latest_prescription:
            async_data['latest_prescription_pk'] = self.latest_prescription.pk

        return patient

    @staticmethod
    def _set_insurance_company(validated_data, instance):
        """
        Sets insurance_company value.
        :param validated_data:
        :param instance:
        :return:
        """
        if validated_data.get('insurance_company_id', None):
            instance.insurance_company = InsuranceCompany.objects.get(pk=validated_data.get('insurance_company_id'))
        elif instance.insurance_company:
            validated_data['insurance_company_id'] = instance.insurance_company.id

    def _get_picture_as_content_file(self, validated_data, picture_name):
        """
        Returns picture as ContentFile.
        :param validated_data:
        :param picture_name:
        :return:
        """
        file_name = {
            "picture_id_front": "id_front.jpg",
            "picture_id_back": "id_back.jpg",
            "selfie": "selfie.jpg",
            "picture_prescription": "medical-prescription.jpg",
            "picture_insurance_card_front": "card-front.jpg",
            "picture_insurance_card_back": "card-back.jpg",
        }
        picture = validated_data.pop(picture_name, self._get_picture_from_latest_prescription(picture_name))
        return utils.base_64_to_image_file(picture, file_name[picture_name])

    def _get_picture_from_latest_prescription(self, picture_name):
        """
        Get picture according to name.
        :param picture_name:
        :return:
        """
        return getattr(self.latest_prescription, picture_name) if self.latest_prescription else None


class MedicalPrescriptionCreateV4Serializer(MedicalPrescriptionV4Serializer):

    patient = serializers.DictField(required=True)

    picture_insurance_card_front = serializers.CharField(required=False, allow_blank=True, validators=[Base64Validator()])
    picture_insurance_card_back = serializers.CharField(required=False, allow_blank=True, validators=[Base64Validator()])

    picture_insurance_card_front_uploadcare = serializers.CharField(required=False, allow_blank=True, validators=[URLValidator()])
    picture_insurance_card_back_uploadcare = serializers.CharField(required=False, allow_blank=True, validators=[URLValidator()])

    insurance_company_id = serializers.IntegerField(required=False)
    preferred_laboratory_id = serializers.IntegerField(required=False)
    preferred_date_to_schedule = serializers.IntegerField(required=False, write_only=True, allow_null=True)
    health_insurance_plan = HealthInsurancePlanSerializer(read_only=True)
    pieces = serializers.ListField(required=True)

    class Meta:
        model = MedicalPrescription
        fields = (
            'health_insurance_plan',
            'status',

            # TODO: remove these fields when base64 apps version is no longer supported
            'picture_insurance_card_front',
            'picture_insurance_card_back',

            'patient',
            'insurance_company_id',
            'modified_at_timestamp',
            'additional_info',
            'period_info',
            'pieces',

            'picture_insurance_card_front_uploadcare',
            'picture_insurance_card_back_uploadcare',

            'ungrouped_scheduled_exams',
            'grouped_scheduled_exams',
            'preferred_laboratory_id',
            'preferred_date_to_schedule'
        )

    @transaction.atomic
    def create(self, validated_data):
        """
        Create and return a new `MedicalPrescription` instance.
        """
        with transaction.atomic():
            async_data = {}
            patient = self._save_patient(validated_data.pop('patient', None), async_data)
            prepared_data = self._prepare_data(validated_data.copy(), patient)
            instance = super(MedicalPrescriptionCreateV4Serializer, self).create(prepared_data)
            self._post_save(instance, validated_data, async_data)
            return instance

    def _save_patient(self, patient_data, async_data):
        """
        Saves patient using patient data.
        :param patient_data:
        :param async_data:
        :return:
        """
        patient = Patient.objects.get(pk=patient_data["user_id"])

        # Parsing images to ContentFile
        patient.picture_id_front = self._get_picture_as_content_file(patient_data, "picture_id_front")
        patient.picture_id_back = self._get_picture_as_content_file(patient_data, "picture_id_back")
        patient.selfie = self._get_picture_as_content_file(patient_data, "selfie")

        picture_id_front_uploadcare = patient_data.pop("picture_id_front_uploadcare", None)
        picture_id_back_uploadcare = patient_data.pop("picture_id_back_uploadcare", None)
        selfie_uploadcare = patient_data.pop("selfie_uploadcare", None)

        # Retrieving Laboratory
        patient.preferred_laboratories = self._get_preferred_laboratories(patient_data)

        phone = patient_data.get("phone", None)
        if phone and type(phone) != int:
            raise serializers.ValidationError({"phone": "must be integer"})
        patient.phone = phone

        # Save it
        patient.save()
        # Upload pictures from uploadcare asynchronously
        async_data.update(
            {
                'get_pictures_method': 'get_picture_as_content_file_uploadcare',
                'patient_id': patient.pk,
                'picture_id_front_uploadcare': picture_id_front_uploadcare,
                'picture_id_back_uploadcare': picture_id_back_uploadcare,
                'selfie_uploadcare': selfie_uploadcare
            }
        )
        if self.latest_prescription:
            async_data['latest_prescription_pk'] = self.latest_prescription.pk

        return patient

    def _post_save(self, instance, validated_data, async_data):
        """
        Saves pictures and exams for medical prescription.
        :param instance:
        :param validated_data:
        :param async_data:
        :return:
        """
        # Parsing base64 into images
        picture_insurance_card_front = self._get_picture_as_content_file(validated_data, "picture_insurance_card_front")
        picture_insurance_card_back = self._get_picture_as_content_file(validated_data, "picture_insurance_card_back")

        picture_insurance_card_front_uploadcare = validated_data.pop("picture_insurance_card_front_uploadcare", None)
        picture_insurance_card_back_uploadcare = validated_data.pop("picture_insurance_card_back_uploadcare", None)

        # Pictures update
        instance.picture_insurance_card_front = picture_insurance_card_front
        instance.picture_insurance_card_back = picture_insurance_card_back
        instance.save()

        pieces_data = validated_data.pop("pieces")
        pieces_images_data = []

        for piece_data in pieces_data:
            picture = piece_data.pop('picture', None)
            prescription_piece = PrescriptionPiece.objects.create(
                prescription=instance,
                **piece_data
            )
            self.context.get('request').data['piece_{}_link'.format(prescription_piece.pk)] = picture
            pieces_images_data.append({
                'pk': prescription_piece.pk,
                'picture': picture
            }
                                      )
        # Upload pictures from uploadcare asynchronously
        self._upload_images_async(instance, async_data, picture_insurance_card_front_uploadcare,
                                  picture_insurance_card_back_uploadcare, pieces_images_data)

        return instance

    def _prepare_data(self, validated_data, patient):
        """
        Prepares validated data.
        :param validated_data:
        :param patient:
        :return:
        """
        # Setting patient
        validated_data['patient'] = patient

        # TODO: remove these fields when base64 apps version is no longer supported
        validated_data["picture_id_front"] = patient.picture_id_front
        validated_data["picture_id_back"] = patient.picture_id_back
        validated_data["selfie"] = patient.selfie

        validated_data["picture_id_front_uploadcare"] = patient.picture_id_front_uploadcare
        validated_data["picture_id_back_uploadcare"] = patient.picture_id_back_uploadcare
        validated_data["selfie_uploadcare"] = patient.selfie_uploadcare

        # Setting insurance company
        validated_data['insurance_company'] = self._get_insurance_company(validated_data)
        validated_data['preferred_laboratory'] = self._get_preferred_laboratory(validated_data)
        try:
            validated_data["preferred_date_to_schedule"] = get_date_from_timestamp(validated_data, "preferred_date_to_schedule")
        except KeyError:
            pass
        # This data is going to be updated later on
        # TODO: remove these fields when base64 apps version is no longer supported
        validated_data.pop("picture_insurance_card_front", None)
        validated_data.pop("picture_insurance_card_back", None)

        validated_data.pop("picture_insurance_card_front_uploadcare", None)
        validated_data.pop("picture_insurance_card_back_uploadcare", None)

        validated_data.pop("pieces", None)
        return validated_data

    def _upload_images_async(self, instance, async_data, picture_insurance_card_front_uploadcare,
                             picture_insurance_card_back_uploadcare, pieces_images_data):
        """
        Asynchronously save images to default storage
        :param instance:
        :param async_data:
        :param picture_insurance_card_front_uploadcare:
        :param picture_insurance_card_back_uploadcare:
        :param pieces_images_data:
        :return:
        """
        async_data.update(
            {
                'get_pictures_method': 'get_picture_as_content_file_uploadcare',
                'prescription_id': instance.pk,
                'picture_insurance_card_front_uploadcare': picture_insurance_card_front_uploadcare,
                'picture_insurance_card_back_uploadcare': picture_insurance_card_back_uploadcare,
                'pieces': pieces_images_data
            }
        )
        if self.latest_prescription:
            async_data['latest_prescription_pk'] = self.latest_prescription.pk

        create_images.apply_async(
            kwargs=async_data,
            countdown=5,
        )

    def _get_picture_as_content_file(self, patient_data, picture_name):
        """
        Returns picture as ContentFile.
        :param patient_data:
        :param picture_name:
        :return:
        """
        file_name = {
            "picture_id_front": "id_front.jpg",
            "picture_id_back": "id_back.jpg",
            "selfie": "selfie.jpg",
            "picture_prescription": "medical-prescription.jpg",
            "picture_insurance_card_front": "card-front.jpg",
            "picture_insurance_card_back": "card-back.jpg",
        }

        # Try to get picture from patient data, otherwise get it from the latest prescription
        picture = patient_data.pop(picture_name, self._get_picture_from_latest_prescription(picture_name))

        return utils.base_64_to_image_file(picture, file_name[picture_name])

    def _get_picture_from_latest_prescription(self, picture_name):
        """
        Get picture according to name.
        :param picture_name:
        :return:
        """
        return getattr(self.latest_prescription, picture_name) if self.latest_prescription else None

    @staticmethod
    def _get_preferred_laboratories(patient_data):
        """
        Returns preferred laboratory instances.
        :param patient_data:
        :return:
        """
        laboratories_id = patient_data.pop('preferred_laboratories_id', None)

        if laboratories_id and type(laboratories_id) is list:
            return Laboratory.objects.filter(pk__in=laboratories_id).all()

        return []

    @staticmethod
    def _get_insurance_company(validated_data):
        """
        Returns insurance company instance.
        :param validated_data:
        :return:
        """
        insurance_company_id = validated_data.pop('insurance_company_id', None)

        if insurance_company_id:
            return InsuranceCompany.objects.get(pk=insurance_company_id)

        return None

    @staticmethod
    def _get_preferred_laboratory(validated_data):
        """
        Returns insurance company instance.
        :param validated_data:
        :return:
        """
        preferred_laboratory_id = validated_data.pop('preferred_laboratory_id', None)

        if preferred_laboratory_id:
            return Laboratory.objects.get(pk=preferred_laboratory_id)

        return None

    def set_latest_prescription(self):
        """
        Sets latest prescription for current user.
        :return:
        """
        try:
            self.latest_prescription = MedicalPrescription.objects \
                .filter(patient=self.initial_data['patient']["user_id"]) \
                .order_by("-created")[0]
        except:
            self.latest_prescription = None

    def validate_patient(self, value):
        """
        Custom validation for patient
        :param value:
        :return:
        """
        if self.latest_prescription:
            if "picture_id_front" not in value:
                value["picture_id_front"] = self.latest_prescription.picture_id_front
            if "picture_id_back" not in value:
                value["picture_id_back"] = self.latest_prescription.picture_id_back
            if "selfie" not in value:
                value["selfie"] = self.latest_prescription.selfie
            if "preferred_laboratories_id" not in value:
                value["preferred_laboratories_id"] = [lab.id for lab in
                                                      self.latest_prescription.patient.preferred_laboratories.all()]

        # TODO: remove these fields when base64 apps version is no longer supported
        to_be_validated = ("user_id", "picture_id_front", "picture_id_back", "selfie")
        errors = utils.validate_fields(value, to_be_validated)

        to_be_validated_uploadcare = ("user_id", "picture_id_front_uploadcare", "picture_id_back_uploadcare",
                                      "selfie_uploadcare")
        errors_uploadcare = utils.validate_fields(value, to_be_validated_uploadcare)

        if errors and errors_uploadcare:
            raise serializers.ValidationError(errors)

        if value.get("preferred_laboratories_id", None):
            labs = Laboratory.objects.filter(pk__in=value["preferred_laboratories_id"]).all()
            if len(labs) < len(value["preferred_laboratories_id"]):
                    raise serializers.ValidationError({
                        "preferred_laboratories_id": "Laboratory matching query does not exist. "
                        "There's some invalid id inside preferred_laboratories_id list."})

        if not errors:
            if not utils.is_base64(value["picture_id_front"]):
                raise serializers.ValidationError({"picture_id_front": "This is not a valid base64"})
            if not utils.is_base64(value["picture_id_back"]):
                raise serializers.ValidationError({"picture_id_back": "This is not a valid base64"})
            if not utils.is_base64(value["selfie"]):
                raise serializers.ValidationError({"selfie": "This is not a valid base64"})

        return value

    def validate_picture_insurance_card_front(self, value):
        """
        Custom validation for picture_insurance_card_front
        :param value:
        :return:
        """
        return self._validate_picture(value, "picture_insurance_card_front")

    def validate_picture_insurance_card_back(self, value):
        """
        Custom validation for picture_insurance_card_back
        :param value:
        :return:
        """
        return self._validate_picture(value, "picture_insurance_card_back")

    def _validate_picture(self, value, picture_name):
        """
        Validates pictures.
        :param value:
        :param picture_name:
        :return:
        """
        if not self.latest_prescription:
            if not value:
                raise serializers.ValidationError("This field is required.")
            if not utils.is_base64(value):
                raise serializers.ValidationError("This is not a valid base64")
            return value

        if not value:
            return getattr(self.latest_prescription, picture_name)
        if not utils.is_base64(value):
            raise serializers.ValidationError("This is not a valid base64")
        return value
