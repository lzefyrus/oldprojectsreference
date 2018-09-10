# encode: utf-8

import datetime

from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.core.validators import URLValidator
from django.db import IntegrityError, transaction
from rest_framework import serializers
from domain.mailer import Mail
from domain.models import *
from domain.tasks import create_images
from patient_api.utils import (
    get_prescription_version,
    get_scheduled_exam_version
)
from patient_api.validators import Base64Validator


class UserCreateSerializer(serializers.ModelSerializer):

    id = serializers.PrimaryKeyRelatedField(read_only=True)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)
    username = serializers.CharField(required=False)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'first_name', 'last_name')


class UserUpdateSerializer(serializers.ModelSerializer):

    id = serializers.PrimaryKeyRelatedField(read_only=True)
    email = serializers.EmailField(read_only=True)
    password = serializers.CharField(required=False, write_only=True)
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)

    class Meta:
        model = User
        fields = ('id', 'email', 'password', 'first_name', 'last_name')


class ExamSerializer(serializers.ModelSerializer):

    id = serializers.PrimaryKeyRelatedField(read_only=True)
    prescription_id = serializers.SerializerMethodField()
    piece_id = serializers.SerializerMethodField()
    preparation_steps = serializers.SerializerMethodField()

    class Meta:
        model = Exam
        fields = (
            'id',
            'external_id',
            'name',
            'description',
            'synonymy',
            'exam_type',
            'is_scheduled_by_phone',
            'prescription_id',
            'piece_id',
            'preparation_steps'
        )

    def get_prescription_id(self, exam):
        exam_data = self.context.get('exam_data')
        if exam_data:
            return exam_data.get(str(exam.pk)).get('prescription_id')

    def get_piece_id(self, exam):
        exam_data = self.context.get('exam_data')
        if exam_data:
            return exam_data.get(str(exam.pk)).get('piece_id')

    def get_preparation_steps(self, exam):
        exam_data = self.context.get('exam_data')
        if exam_data and exam_data.get(str(exam.pk)).get('laboratory_id'):
            preparation_steps = exam.preparationstep_set.filter(
                laboratory__pk=exam_data.get(str(exam.pk)).get('laboratory_id')
            )
            if preparation_steps.exists():
                return preparation_steps.first().description

            #laboratory by brand
            lab = Laboratory.objects.filter(id=exam_data.get(str(exam.pk)).get('laboratory_id')).first()
            preparation_steps = exam.preparationstep_set.filter(
                laboratory_id__in=[i.get('id', '---') for i in lab.brand.laboratory_set.all().values('id')]
            )
            if preparation_steps.exists():
                return preparation_steps.first().description


class TimestampedExamSerializer(ExamSerializer):
    scheduled_exam_id = serializers.SerializerMethodField()
    scheduled_time_timestamp = serializers.SerializerMethodField()


    class Meta(ExamSerializer.Meta):
        fields = ExamSerializer.Meta.fields + (
            'scheduled_exam_id',
            'scheduled_time_timestamp',
        )

    def get_scheduled_exam_id(self, exam):
        exam_data = self.context.get('exam_data')
        if exam_data:
            return exam_data.get(str(exam.pk)).get('scheduled_exam_id')

    def get_scheduled_time_timestamp(self, exam):
        exam_data = self.context.get('exam_data')
        if exam_data:
            timestamp = exam_data.get(str(exam.pk)).get('timestamp')
            return timestamp


class LaboratoryBrandSerializer(serializers.ModelSerializer):

    id = serializers.PrimaryKeyRelatedField(read_only=True)
    similar_brand_id = serializers.SerializerMethodField()

    class Meta:
        model = LaboratoryBrand
        fields = ('id', 'name', 'is_active', 'similar_brand_id', 'premium')

    @staticmethod
    def get_similar_brand_id(laboratory_brand):
        try:
            return laboratory_brand.similar_brand.id
        except AttributeError:
            return None


class LaboratoryFacilitiesSerializer(serializers.ModelSerializer):

    class Meta:
        model = LaboratoryFacilities
        fields = ('id', 'description', )


class LaboratoryOpeningHoursSerializer(serializers.ModelSerializer):
    opens_at = serializers.SerializerMethodField()
    closes_at = serializers.SerializerMethodField()

    class Meta:
        model = LaboratoryOpeningHours
        fields = ('week_day', 'is_open', 'opens_at', 'closes_at')

    @staticmethod
    def get_opens_at(obj):
        """
        Dynamically gets formatted opens_at field
        :param obj:
        :return:
        """
        if obj.opens_at:
            return obj.opens_at.strftime("%H:%M")
        return False

    @staticmethod
    def get_closes_at(obj):
        """
        Dynamically gets formatted closes_at field
        :param obj:
        :return:
        """
        if obj.closes_at:
            return obj.closes_at.strftime("%H:%M")
        return False


class LaboratoryCollectionTimeSerializer(LaboratoryOpeningHoursSerializer):

    class Meta:
        model = LaboratoryCollectionTime
        fields = ('week_day', 'is_open', 'opens_at', 'closes_at')


class LaboratorySerializer(serializers.ModelSerializer):

    id = serializers.PrimaryKeyRelatedField(read_only=True)
    brand_name = serializers.SerializerMethodField()
    address = serializers.SerializerMethodField()
    coordinates = serializers.SerializerMethodField()
    exams_id = serializers.SerializerMethodField()
    facilities = serializers.SerializerMethodField()
    opening_hours = serializers.SerializerMethodField()
    collection_time = serializers.SerializerMethodField()
    premium = serializers.SerializerMethodField()

    class Meta:
        model = Laboratory
        fields = (
            'id',
            'brand_name',
            'address',
            'coordinates',
            'description',
            'exams_id',
            'facilities',
            'opening_hours',
            'collection_time',
            'premium'
        )

    @staticmethod
    def get_brand_name(laboratory):
        """
        Dynamically gets brand_name field
        :param laboratory:
        :return:
        """
        try:
            return laboratory.brand.name
        except AttributeError:
            return ""

    @staticmethod
    def get_address(laboratory):
        """
        Dynamically gets address field
        :param laboratory:
        :return:
        """
        return {
            "street": laboratory.street,
            "street_number": laboratory.street_number,
            "zip_code": laboratory.zip_code,
            "district": laboratory.district,
            "city": laboratory.city,
            "state": laboratory.state,
            "state_abbreviation": laboratory.state_abbreviation,
            "country": laboratory.country,
            "complement": laboratory.complement
        }

    @staticmethod
    def get_coordinates(laboratory):
        """
        Dynamically gets coordinates field
        :param laboratory:
        :return:
        """
        return {"lat": laboratory.lat, "lng": laboratory.lng}

    @staticmethod
    def get_exams_id(laboratory):
        return [exam.id for exam in laboratory.exams.all()]

    @staticmethod
    def get_facilities(laboratory):
        """
        Dynamically gets lab facilities
        :param laboratory:
        :return:
        """
        return LaboratoryFacilitiesSerializer(LaboratoryFacilities.objects.filter(laboratory=laboratory.id)
                                              .order_by("id"), read_only=True, many=True).data

    @staticmethod
    def get_opening_hours(laboratory):
        """
        Dynamically gets lab opening hours
        :param laboratory:
        :return:
        """
        return LaboratoryOpeningHoursSerializer(LaboratoryOpeningHours.objects.filter(laboratory=laboratory.id)
                                                .order_by("week_day"), read_only=True, many=True).data

    @staticmethod
    def get_collection_time(laboratory):
        """
        Dynamically gets lab collection times
        :param laboratory:
        :return:
        """
        return LaboratoryCollectionTimeSerializer(LaboratoryCollectionTime.objects.filter(laboratory=laboratory.id)
                                                  .order_by("week_day"), read_only=True, many=True).data

    @staticmethod
    def get_premium(laboratory):
        return laboratory.brand.premium


class PatientSerializer(serializers.ModelSerializer):
    user = UserCreateSerializer(required=True)

    selfie = serializers.CharField(required=False, validators=[Base64Validator()], write_only=True)
    picture_id_front = serializers.CharField(required=False, validators=[Base64Validator()], write_only=True)
    picture_id_back = serializers.CharField(required=False, validators=[Base64Validator()], write_only=True)

    selfie_uploadcare = serializers.CharField(required=False, validators=[URLValidator()], write_only=True)
    picture_id_front_uploadcare = serializers.CharField(required=False, validators=[URLValidator()], write_only=True)
    picture_id_back_uploadcare = serializers.CharField(required=False, validators=[URLValidator()], write_only=True)

    selfie_url = serializers.SerializerMethodField()
    picture_id_front_url = serializers.SerializerMethodField()
    picture_id_back_url = serializers.SerializerMethodField()

    selfie_uploadcare_url = serializers.SerializerMethodField()
    picture_id_front_uploadcare_url = serializers.SerializerMethodField()
    picture_id_back_uploadcare_url = serializers.SerializerMethodField()

    created_timestamp = serializers.SerializerMethodField()
    preferred_laboratories_id = serializers.ListField(required=False)
    preferred_laboratories = LaboratorySerializer(many=True, read_only=True)
    is_confirmed = serializers.BooleanField(read_only=True)

    class Meta:
        model = Patient
        fields = (
            'id_device',
            'created_timestamp',
            'gender',
            'birth_date',

            'picture_id_front',
            'picture_id_back',
            'selfie',

            'picture_id_front_uploadcare',
            'picture_id_back_uploadcare',
            'selfie_uploadcare',

            'picture_id_front_url',
            'picture_id_back_url',
            'selfie_url',

            'picture_id_front_uploadcare_url',
            'picture_id_back_uploadcare_url',
            'selfie_uploadcare_url',

            'preferred_laboratories_id',
            'preferred_laboratories',
            'full_name',
            'user',
            'phone',
            'is_confirmed'
        )

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

    def get_selfie_url(self, patient):
        """
        Retrieves picture URL.
        :param patient:
        :return:
        """
        return self._get_picture_uri("selfie", patient)

    def get_picture_id_front_url(self, patient):
        """
        Retrieves picture URL.
        :param patient:
        :return:
        """
        return self._get_picture_uri("picture_id_front", patient)

    def get_picture_id_back_url(self, patient):
        """
        Retrieves picture URL.
        :param patient:
        :return:
        """
        return self._get_picture_uri("picture_id_back", patient)

    def get_selfie_uploadcare_url(self, patient):
        """
        Retrieves picture URL.
        :param patient:
        :return:
        """
        return self.context.get('request').data.get(
            'selfie_uploadcare',
            self._get_picture_uri('selfie_uploadcare', patient)
        )

    def get_picture_id_front_uploadcare_url(self, patient):
        """
        Retrieves picture URL.
        :param patient:
        :return:
        """
        return self.context.get('request').data.get(
            'picture_id_front_uploadcare',
            self._get_picture_uri('picture_id_front_uploadcare', patient)
        )

    def get_picture_id_back_uploadcare_url(self, patient):
        """
        Retrieves picture URL.
        :param patient:
        :return:
        """
        return self.context.get('request').data.get(
            'picture_id_back_uploadcare',
            self._get_picture_uri('picture_id_back_uploadcare', patient)
        )

    @staticmethod
    def _get_picture(picture, picture_name, patient):
        """
        Retrieves picture as file.
        :param picture:
        :param picture_name:
        :param patient:
        :return:
        """
        picture_file = {
            "picture_id_front": "id_front.jpg",
            "picture_id_back": "id_back.jpg",
            "selfie": "selfie.jpg",
        }
        return utils.base_64_to_image_file(picture, picture_file[picture_name]) or getattr(patient, picture_name)

    @staticmethod
    def get_created_timestamp(patient):
        """
        Retrieves timestamp dynamically.
        :param patient:
        :return:
        """
        try:
            return int(patient.created.timestamp())
        except:
            return None

    @staticmethod
    def _get_preferred_labs(validated_data):
        request_lab_ids = validated_data.pop('preferred_laboratories_id', None)
        if not request_lab_ids:
            return []

        preferred_labs = Laboratory.objects.filter(pk__in=request_lab_ids).all()
        if len(preferred_labs) < len(request_lab_ids):
            raise ObjectDoesNotExist("Laboratory matching query does not exist. "
                                     "There's some invalid id inside preferred_laboratories_id list.")

        return preferred_labs


class PatientCreateSerializer(PatientSerializer):
    token = serializers.CharField(required=False)

    class Meta:
        model = Patient
        fields = (
            'id_device',
            'created_timestamp',
            'gender',
            'birth_date',
            'picture_id_front',
            'picture_id_back',
            'selfie',
            'picture_id_front_url',
            'picture_id_back_url',
            'selfie_url',
            'user',
            'preferred_laboratories_id',
            'full_name',
            'phone',
            'preferred_laboratories',
            'is_confirmed',
            'token',
            'picture_id_front_uploadcare',
            'picture_id_back_uploadcare',
            'selfie_uploadcare',
            'picture_id_front_uploadcare_url',
            'picture_id_back_uploadcare_url',
            'selfie_uploadcare_url',
        )

    @transaction.atomic
    def create(self, validated_data):
        """
        Create and return a new `Patient` instance.
        """
        with transaction.atomic():
            # creates user instance
            validated_data['user'] = self._create_user(validated_data.pop('user', None))

            # Set Preferred Laboratory
            preferred_labs = self._get_preferred_labs(validated_data)
            if preferred_labs:
                validated_data['preferred_laboratories'] = preferred_labs

            # creates patient instance
            validated_data["hash"] = uuid.uuid4().hex
            instance = super(PatientSerializer, self).create(validated_data)

            self._post_save(instance, validated_data)

            return instance

    def _post_save(self, instance, validated_data):
        """
        Performs actions after saving a Patient
        :param instance:
        :param validated_data:
        :return:
        """
        self._create_pictures(
            instance,
            validated_data.pop("picture_id_front", None),
            validated_data.pop("picture_id_back", None),
            validated_data.pop("selfie", None),

            validated_data.pop("picture_id_front_uploadcare", None),
            validated_data.pop("picture_id_back_uploadcare", None),
            validated_data.pop("selfie_uploadcare", None),
        )

        request = self.context.get('request')
        device_type = request.META.get(settings.DEVICE_TYPE_HEADERS, None)
        self.send_confirmation_email(instance, device_type)

    @staticmethod
    def _create_user(user_data):
        """
        Creates user instance.
        :param user_data:
        :return:
        """

        try:
            User.objects.get(email=user_data["email"])
            raise IntegrityError
        except ObjectDoesNotExist:
            pass

        return User.objects.create_user(username=user_data["email"],
                                        email=user_data["email"],
                                        password=user_data["password"])

    def _create_pictures(
            self, patient, picture_id_front, picture_id_back, selfie,
            picture_id_front_uploadcare, picture_id_back_uploadcare , selfie_uploadcare):
        """
        Creates patient pictures.
        :param patient:
        :param picture_id_front:
        :param picture_id_back:
        :param selfie:
        :return:
        """
        patient.picture_id_front = self._get_picture(picture_id_front, "picture_id_front", patient)
        patient.picture_id_back = self._get_picture(picture_id_back, "picture_id_back", patient)
        patient.selfie = self._get_picture(selfie, "selfie", patient)

        patient.save()
        # Upload pictures from uploadcare asynchronously
        data = {
            'get_pictures_method': 'get_patient_picture_uploadcare',
            'patient_id': patient.pk,
            'picture_id_front_uploadcare': picture_id_front_uploadcare,
            'picture_id_back_uploadcare': picture_id_back_uploadcare,
            'selfie_uploadcare': selfie_uploadcare
        }

        create_images.apply_async(
            kwargs=data,
            countdown=3,
        )

    @staticmethod
    def send_confirmation_email(patient, device_type=settings.ANDROID):
        link = "{0}/mobile/patient/confirmation?token={1}".format(settings.DOMAIN_NAME, patient.hash)

        if device_type == settings.IOS:
            link += "&{0}={1}".format(settings.DEVICE_TYPE_HEADERS, device_type)

        subject = "{}, confirme seu email".format(patient.full_name)
        text = """
        <html>
            Olá, {0}!
            <br><br>
            Só falta confirmar sua conta de e-mail para começar a usar o aplicativo Sara.
            <br><br>
            <b>É só acessar esse e-mail no celular em que o aplicativo está instalado e clicar no link abaixo.</b>
            <br><br>
            <a href={1}>{1}</a>
            <br><br>
            Assim que seu e-mail estiver confirmado, nós já poderemos te ajudar com seus exames.
            <br><br>
            Nos vemos em breve.
            <br><br>
            SARA app
            <br><br>
            --
            <br><br>
            Ignore esta mensagem caso você não tenha utilizado esta conta de e-mail para o cadastro em nosso app.
        </html>
        """.format(patient.full_name, link)

        Mail.send(
            to=patient.user.email,
            subject=subject,
            text=text,
            html=True
        )


class PatientUpdateSerializer(PatientSerializer):

    user = UserUpdateSerializer(required=False)
    full_name = serializers.CharField(required=False)
    birth_date = serializers.CharField(required=False)
    gender = serializers.CharField(required=False)

    class Meta:
        model = Patient
        fields = (
            'id_device',
            'created_timestamp',
            'gender',
            'birth_date',
            'picture_id_front',
            'picture_id_back',
            'selfie',
            'picture_id_front_url',
            'picture_id_back_url',
            'selfie_url',
            'user',
            'preferred_laboratories_id',
            'full_name',
            'phone',
            'preferred_laboratories',
            'is_confirmed',
            'token',
            'picture_id_front_uploadcare',
            'picture_id_back_uploadcare',
            'selfie_uploadcare',
            'picture_id_front_uploadcare_url',
            'picture_id_back_uploadcare_url',
            'selfie_uploadcare_url',
        )

    @transaction.atomic
    def update(self, instance, validated_data):
        """
        Update and return an existing `Patient` instance, given the validated data.
        """
        # Pictures update
        instance.picture_id_front = self._get_picture(
            validated_data.pop("picture_id_front", None),
            "picture_id_front",
            instance
        )
        instance.picture_id_back = self._get_picture(
            validated_data.pop("picture_id_back", None),
            "picture_id_back",
            instance
        )
        instance.selfie = self._get_picture(
            validated_data.pop("selfie", None),
            "selfie",
            instance
        )

        picture_id_front_uploadcare = validated_data.pop("picture_id_front_uploadcare", None)
        picture_id_back_uploadcare = validated_data.pop("picture_id_back_uploadcare", None)
        selfie_uploadcare = validated_data.pop("selfie_uploadcare", None)

        validated_data["picture_id_front"] = instance.picture_id_front
        validated_data["picture_id_back"] = instance.picture_id_back
        validated_data["selfie"] = instance.selfie

        validated_data["picture_id_front_uploadcare"] = instance.picture_id_front_uploadcare
        validated_data["picture_id_back_uploadcare"] = instance.picture_id_back_uploadcare
        validated_data["selfie_uploadcare"] = instance.selfie_uploadcare

        # Updates user instance
        validated_data['user'] = self._update_user(instance, validated_data.pop('user', None))

        # Set Preferred Laboratory
        self._set_laboratory(validated_data, instance)

        # Save it
        instance.__dict__.update(validated_data)
        instance.save()
        # Upload pictures from uploadcare asynchronously
        data = {
            'get_pictures_method': 'get_patient_picture_uploadcare',
            'patient_id': instance.pk,
            'picture_id_front_uploadcare': picture_id_front_uploadcare,
            'picture_id_back_uploadcare': picture_id_back_uploadcare,
            'selfie_uploadcare': selfie_uploadcare
        }

        create_images.apply_async(
            kwargs=data,
            countdown=3,)

        return instance

    def _set_laboratory(self, validated_data, instance):
        """
        Sets laboratory value.
        :param validated_data:
        :param instance:
        :return:
        """
        if validated_data.get('preferred_laboratories_id', None):
            preferred_labs = self._get_preferred_labs(validated_data)
            if preferred_labs:
                instance.preferred_laboratories = preferred_labs
        elif instance.preferred_laboratories:
            validated_data['preferred_laboratories_id'] = [lab.id for lab in instance.preferred_laboratories.all()]
        else:
            validated_data['preferred_laboratories_id'] = []

    @staticmethod
    def _update_user(instance, user_data):
        """
        Updates user instance.
        :param instance:
        :param user_data:
        :return:
        """
        if user_data:
            instance.user.__dict__.update(user_data)
            instance.user.save()

        return user_data


class InsuranceCompanySerializer(serializers.ModelSerializer):

    class Meta:
        model = InsuranceCompany
        fields = ('name', 'description', 'cnpj')


class HealthInsuranceSerializer(serializers.ModelSerializer):
    insurance_company = InsuranceCompanySerializer()
    laboratories = LaboratorySerializer(many=True)

    class Meta:
        model = HealthInsurance
        fields = ('id', 'external_id', 'description', 'cnpj', 'insurance_company', 'laboratories')


class HealthInsurancePlanSerializer(serializers.ModelSerializer):
    health_insurance_id = serializers.SerializerMethodField()

    class Meta:
        model = HealthInsurancePlan
        fields = ('id', 'health_insurance_id', 'plan_code')

    @staticmethod
    def get_health_insurance_id(instance):
        try:
            return instance.health_insurance.id
        except AttributeError:
            return None


class MedicalPrescriptionSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(read_only=True)
    picture_insurance_card_front = serializers.CharField(required=True, write_only=True, validators=[Base64Validator()])
    picture_insurance_card_back = serializers.CharField(required=False, write_only=True, validators=[Base64Validator()])
    picture_prescription = serializers.CharField(required=True, write_only=True, validators=[Base64Validator()])

    picture_insurance_card_front_uploadcare = serializers.CharField(required=True, write_only=True, validators=[URLValidator()])
    picture_insurance_card_back_uploadcare = serializers.CharField(required=False, write_only=True, validators=[URLValidator()])
    picture_prescription_uploadcare = serializers.CharField(required=True, write_only=True, validators=[URLValidator()])

    picture_insurance_card_front_url = serializers.SerializerMethodField()
    picture_insurance_card_back_url = serializers.SerializerMethodField()
    picture_prescription_url = serializers.SerializerMethodField()
    picture_id_front_url = serializers.SerializerMethodField()
    picture_id_back_url = serializers.SerializerMethodField()
    selfie_url = serializers.SerializerMethodField()

    picture_insurance_card_front_uploadcare_url = serializers.SerializerMethodField()
    picture_insurance_card_back_uploadcare_url = serializers.SerializerMethodField()
    picture_prescription_uploadcare_url = serializers.SerializerMethodField()
    picture_id_front_uploadcare_url = serializers.SerializerMethodField()
    picture_id_back_uploadcare_url = serializers.SerializerMethodField()
    selfie_uploadcare_url = serializers.SerializerMethodField()

    scheduled_exams = serializers.SerializerMethodField()
    health_insurance_plan = HealthInsurancePlanSerializer(read_only=True)
    latest_prescription = None
    modified_at_timestamp = serializers.SerializerMethodField(read_only=True)
    exams_not_registered = serializers.CharField(read_only=True)

    class Meta:
        model = MedicalPrescription
        fields = (
            'id', 'health_insurance_plan', 'status', 'doctor_crm', 'doctor_name', 'patient',
            'insurance_company', 'picture_insurance_card_front', 'picture_insurance_card_back',
            'picture_prescription', 'picture_insurance_card_front_url',
            'picture_insurance_card_back_url', 'picture_prescription_url', 'picture_id_front_url',
            'picture_id_back_url', 'selfie_url', 'scheduled_exams', 'modified_at_timestamp',
            'additional_info', 'exams_not_registered',

            'picture_insurance_card_front_uploadcare',
            'picture_insurance_card_back_uploadcare',
            'picture_prescription_uploadcare',
            'picture_id_back_uploadcare',
            'picture_id_front_uploadcare',
            'selfie_uploadcare',
            'period_info',
        )

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

    def get_picture_insurance_card_back_url(self, prescription):
        """
        Retrieves picture URL.
        :param prescription:
        :return:
        """
        return self._get_picture_uri("picture_insurance_card_back", prescription)

    def get_picture_prescription_url(self, prescription):
        """
        Retrieves picture URL.
        :param prescription:
        :return:
        """
        return self._get_picture_uri("picture_prescription", prescription)

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

    def get_picture_prescription_uploadcare_url(self, prescription):
        """
        Retrieves picture URL.
        :param prescription:
        :return:
        """
        return self.context.get('request').data.get(
            'picture_prescription_uploadcare',
            self._get_picture_uri('picture_prescription_uploadcare', prescription)
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
    def get_scheduled_exams(prescription):
        return ScheduledExamSerializer(ScheduledExam.objects.filter(
            prescription=prescription.id), many=True).data


class PreparationStepSerializer(serializers.ModelSerializer):

    exam_id = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = PreparationStep
        fields = ('title', 'description', 'recent_description', 'is_mandatory', 'exam_id')

    @staticmethod
    def get_exam_id(preparation_step):
        """
        Retrieves exam id.
        :param preparation_step:
        :return:
        """
        try:
            return preparation_step.exam.id
        except AttributeError:
            return None


class ExamResultDetailSerializer(serializers.ModelSerializer):

    class Meta:
        model = ExamResultDetail
        fields = ('title', 'description', 'result', 'reference_values')


class ExamResultSerializer(serializers.Serializer):

    exam_id = serializers.SerializerMethodField(read_only=True)
    file_url = serializers.SerializerMethodField()
    exam_result_details = serializers.SerializerMethodField()

    @staticmethod
    def get_exam_id(scheduled_exam):
        """
        Retrieves exam id.
        :param scheduled_exam:
        :return:
        """
        try:
            return scheduled_exam.exam.id
        except AttributeError:
            return None

    def get_file_url(self, scheduled_exam):
        """
        Retrieves file URL.
        :param scheduled_exam:
        :return:
        """
        import requests
        headers = {}

        if settings.SARA_CLINIC.get('token', None):
            headers = {'Authorization': settings.SARA_CLINIC.get('token')}

        clinic_data = requests.get(settings.SARA_CLINIC.get('endpoint').format(scheduled_exam.lab_file_code),
                                   headers=headers)

        if clinic_data.status_code == 200:
            data = clinic_data.json()
            if len(data) > 0:
                path = []
                for item in data:
                    path.append(item.get('path', ''))
                return path

        request = self.context.get('request')
        exams_result = ExamResult.objects.filter(scheduled_exam=scheduled_exam)
        for exam_result in exams_result:
            if exam_result.file:
                return [request.build_absolute_uri(exam_result.file.url)]

        return None

    @staticmethod
    def get_exam_result_details(scheduled_exam):
        """
        Retrieves all exam result details
        :param exam_result:
        :return:
        """
        return {}


class ScheduledExamSerializer(serializers.ModelSerializer):
    exam = serializers.SerializerMethodField()
    laboratory = LaboratorySerializer()
    suggested_labs_id = serializers.SerializerMethodField()
    status_versions = serializers.SerializerMethodField()
    scheduled_time_timestamp = serializers.SerializerMethodField()
    scheduled_exam_phone_call = serializers.SerializerMethodField()
    expiration_date_timestamp = serializers.SerializerMethodField()
    modified_at_timestamp = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ScheduledExam
        fields = ('id', 'exam', 'laboratory', 'status', 'scheduled_time_timestamp', 'procedure_average_duration',
                  'confirmation', 'suggested_labs_id', 'status_versions', 'scheduled_exam_phone_call',
                  'expiration_date_timestamp', 'plan_product_code', 'modified_at_timestamp',
                  'results_expected_at', 'annotations')
        read_only = True

    def get_exam(self, scheduled_exam):
        exam = scheduled_exam.exam
        exam_data_dict = {}
        exam_data_dict[str(exam.pk)] = {
            "prescription_id": scheduled_exam.prescription.pk,
            "piece_id": scheduled_exam.prescription_piece.pk,
            "laboratory_id": scheduled_exam.laboratory.pk if scheduled_exam.laboratory else None
        }
        return ExamSerializer(exam, context={"exam_data": exam_data_dict}).data

    @staticmethod
    def get_suggested_labs_id(scheduled_exam):
        """
        Retrieves suggested_labs ids dynamically.
        :param scheduled_exam:
        :return:
        """
        try:
            return [lab.id for lab in scheduled_exam.suggested_labs.all()]
        except AttributeError:
            return []

    @staticmethod
    def get_status_versions(scheduled_exam):
        """
        Retrieves status versions dynamically.
        :param scheduled_exam:
        :return:
        """
        try:
            return get_scheduled_exam_version(scheduled_exam, "status")
        except:
            return []

    @staticmethod
    def get_scheduled_time_timestamp(scheduled_exam):
        """
        Retrieves scheduled_time as timestamp dynamically.
        :param scheduled_exam:
        :return:
        """
        try:
            return int(scheduled_exam.scheduled_time.timestamp())
        except:
            return None

    @staticmethod
    def get_scheduled_exam_phone_call(scheduled_exam):
        """
        Dynamically gets an exam phone call
        :param scheduled_exam:
        :return:
        """
        try:
            phone_call = ScheduledExamPhoneCall.objects.get(scheduled_exam=scheduled_exam.id, is_canceled=False)
            return ScheduledExamPhoneCallSerializer(phone_call).data
        except:
            return None

    @staticmethod
    def get_expiration_date_timestamp(scheduled_exam):
        """
        Dynamically gets expiration date
        :param scheduled_exam:
        :return:
        """
        try:
            exam_expiration = ExamExpiration.objects.filter(exam=scheduled_exam.exam.id,
                                                            insurance_company=scheduled_exam.prescription.insurance_company.id
                                                            ).first()
            pre_defined_expiration = scheduled_exam.created + datetime.timedelta(days=exam_expiration.expiration_in_days)
        except AttributeError:
            pre_defined_expiration = None

        registered_expiration = int(scheduled_exam.expiration_date.timestamp()) if scheduled_exam.expiration_date else None
        pre_defined_expiration = int(pre_defined_expiration.timestamp()) if pre_defined_expiration else None

        return registered_expiration or pre_defined_expiration

    @staticmethod
    def get_modified_at_timestamp(scheduled_exam):
        """
        Retrieves modified_at as timestamp dynamically.
        :param scheduled_exam:
        :return:
        """
        try:
            return int(scheduled_exam.modified.timestamp())
        except:
            return None


class ScheduledExamRetrieveSerializer(ScheduledExamSerializer):
    exam_id = serializers.SerializerMethodField(read_only=True)
    laboratory_id = serializers.IntegerField()
    suggested_labs_id = serializers.SerializerMethodField(read_only=True)
    status_versions = serializers.SerializerMethodField(read_only=True)
    scheduled_time = serializers.IntegerField(write_only=True)

    class Meta:
        model = ScheduledExam
        fields = ('exam_id', 'laboratory_id', 'status', 'scheduled_time', 'scheduled_time_timestamp',
                  'procedure_average_duration', 'confirmation', 'suggested_labs_id', 'status_versions',
                  'scheduled_exam_phone_call', 'expiration_date_timestamp', 'plan_product_code',
                  'modified_at_timestamp')
        read_only = True

    def update(self, instance, validated_data):
        """
        Create and return a new `ScheduledExam` instance.
        """
        prepared_data = self._prepare_data(validated_data.copy())
        instance = super(ScheduledExamRetrieveSerializer, self).update(instance, prepared_data)
        return instance

    def _prepare_data(self, validated_data):
        """
        Prepares validated data.
        :param validated_data:
        :return:
        """
        # Parses timestamp into datetime
        scheduled_time_timestamp = validated_data.get("scheduled_time", None)
        if scheduled_time_timestamp:
            try:
                scheduled_time_timestamp = int(scheduled_time_timestamp)
            except ValueError:
                raise ValueError("Field 'scheduled_time_timestamp' should be an int timestamp")

            scheduled_time_timestamp = utils.remove_milliseconds_from_timestamp(scheduled_time_timestamp)
            validated_data["scheduled_time"] = datetime.datetime.fromtimestamp(scheduled_time_timestamp)

        # Parses laboratory id into Laboratory instance
        lab_id = validated_data.pop("laboratory_id", None)
        if lab_id:
            validated_data["laboratory"] = Laboratory.objects.get(pk=lab_id)

        request = self.context.get("request", None)
        if request and request.user:
            validated_data["modified_by"] = request.user

        return validated_data

    @staticmethod
    def get_exam_id(instance):
        """
        Gets exam id dynamically
        :param instance:
        :return:
        """
        return instance.exam.id

    @transaction.atomic
    def batch_update(self, data, request_user):
        """
        Updates ScheduledExam(s) in batch all at once in order to save HTTP requests when scheduling Exams packages
        :param data:
        :param request_user:
        :return:
        """
        if "scheduled_exams_id" not in data:
            raise ValueError("The following field(s) is mandatory: [scheduled_exams_id]")

        exams = []
        scheduled_exams = ScheduledExam.objects.filter(pk__in=data.pop("scheduled_exams_id"))

        for exam in scheduled_exams:
            prepared_data = self._prepare_data(data.copy())
            prepared_data["modified_by"] = request_user
            if scheduled_exams.count() > 1:
                prepared_data["is_grouped"] = True
            instance = super(ScheduledExamRetrieveSerializer, self).update(exam, prepared_data)
            exams.append(instance)

        return exams


class GroupedScheduledExamSerializer(ScheduledExamSerializer):

    scheduled_time_timestamp = serializers.SerializerMethodField()
    exams = serializers.SerializerMethodField()

    class Meta(ScheduledExamSerializer.Meta):

        fields = (
            'status',
            'scheduled_time_timestamp',
            'laboratory',
            'exams',
        )

    def get_scheduled_time_timestamp(self, scheduled_exam):
        """
        Retrieves scheduled_time as timestamp dynamically for earliest exam in a group.
        :param scheduled_exam:
        :return:
        """
        if scheduled_exam.laboratory:
            exams = ScheduledExam.objects.filter(
                prescription=scheduled_exam.prescription,
                laboratory__pk=scheduled_exam.laboratory.pk,
                scheduled_time__day=scheduled_exam.scheduled_time.day,
                status=self.context.get('statuses').get(str(scheduled_exam.pk))
            ).order_by('scheduled_time')

            return int(exams.first().scheduled_time.timestamp()) if exams.exists() else None

    def get_exams(self, scheduled_exam):
        if scheduled_exam.laboratory:
            scheduled_exams = ScheduledExam.objects.filter(
                prescription=scheduled_exam.prescription,
                laboratory__pk=scheduled_exam.laboratory.pk,
                scheduled_time__day=scheduled_exam.scheduled_time.day,
                status=self.context.get('statuses').get(str(scheduled_exam.pk))
                ).order_by('scheduled_time')
            exam_data_dict = {}
            exams_ids = []
            for scheduled_exam in scheduled_exams:
                exams_ids.append(scheduled_exam.exam.pk)
                exam_data_dict[str(scheduled_exam.exam.pk)] = {
                    "scheduled_exam_id": scheduled_exam.pk,
                    "timestamp": int(scheduled_exam.scheduled_time.timestamp()),
                    "prescription_id": scheduled_exam.prescription.pk,
                    "piece_id": scheduled_exam.prescription_piece.pk,
                    "laboratory_id": scheduled_exam.laboratory.pk
                }
            exams = Exam.objects.filter(pk__in=exams_ids)
            exams_with_order = list(exams)
            exams_with_order.sort(key=lambda exam: exam_data_dict.get(str(exam.pk)).get('timestamp'))
            return TimestampedExamSerializer(exams_with_order, many=True,
                                             context={
                                                 "exam_data": exam_data_dict,
                                             }).data


class MedicalPrescriptionByPatientSerializer(MedicalPrescriptionSerializer):

    scheduled_exams = serializers.SerializerMethodField()
    insurance_company_id = serializers.SerializerMethodField()
    created_timestamp = serializers.SerializerMethodField()
    status_versions = serializers.SerializerMethodField()
    health_insurance_plan = HealthInsurancePlanSerializer(read_only=True)
    expiration_date_timestamp = serializers.SerializerMethodField()
    prescription_issued_at_timestamp = serializers.SerializerMethodField()

    class Meta:
        model = MedicalPrescription
        fields = (
            'id', 'scheduled_exams', 'insurance_company_id', 'created_timestamp', 'status_versions',
            'status', 'selfie_id_matches', 'health_insurance_plan',
            'doctor_crm', 'doctor_name', 'picture_insurance_card_front_url',
            'picture_insurance_card_back_url', 'picture_prescription_url', 'picture_id_back_url',
            'picture_id_front_url', 'selfie_url', 'modified_at_timestamp', 'additional_info',
            'exams_not_registered', 'expiration_date_timestamp', 'prescription_issued_at_timestamp',
            'picture_insurance_card_front_uploadcare_url',
            'picture_insurance_card_back_uploadcare_url',
            'picture_prescription_uploadcare_url',
            'picture_id_back_uploadcare_url',
            'picture_id_front_uploadcare_url',
            'selfie_uploadcare_url',
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


    @staticmethod
    def get_prescription_issued_at_timestamp(prescription):
        """
        Retrieves prescription_issued_at timestamp dynamically.
        :param prescription:
        :return:
        """
        try:
            return int(prescription.prescription_issued_at.timestamp())
        except:
            return None


class MedicalPrescriptionRetrieveSerializer(MedicalPrescriptionSerializer):
    patient_id = serializers.SerializerMethodField()
    insurance_company_id = serializers.SerializerMethodField()
    health_insurance_plan = HealthInsurancePlanSerializer()

    class Meta:
        model = MedicalPrescription
        fields = (
            'id', 'health_insurance_plan', 'status', 'doctor_crm', 'doctor_name',
            'picture_insurance_card_front', 'picture_insurance_card_back', 'picture_prescription',
            'picture_insurance_card_front_url', 'picture_insurance_card_back_url', 'picture_prescription_url',
            'picture_id_front_url', 'picture_id_back_url', 'selfie_url',
            'patient_id', 'insurance_company_id', 'scheduled_exams', 'modified_at_timestamp', 'additional_info',
            'exams_not_registered',
            'picture_insurance_card_front_uploadcare_url',
            'picture_insurance_card_back_uploadcare_url',
            'picture_prescription_uploadcare_url',
            'picture_id_back_uploadcare_url',
            'picture_id_front_uploadcare_url',
            'selfie_uploadcare_url',
            'period_info',
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


class MedicalPrescriptionUpdateSerializer(MedicalPrescriptionSerializer):

    patient = serializers.DictField(required=False, write_only=True)
    picture_insurance_card_front = serializers.CharField(required=False, write_only=True, validators=[Base64Validator()])
    picture_insurance_card_back = serializers.CharField(required=False, write_only=True, validators=[Base64Validator()])
    picture_prescription = serializers.CharField(required=False, write_only=True, validators=[Base64Validator()])
    picture_insurance_card_front_uploadcare = serializers.CharField(required=False, write_only=True, validators=[URLValidator()])
    picture_insurance_card_back_uploadcare = serializers.CharField(required=False, write_only=True, validators=[URLValidator()])
    picture_prescription_uploadcare = serializers.CharField(required=False, write_only=True, validators=[URLValidator()])
    health_insurance_plan = HealthInsurancePlanSerializer(read_only=True)

    class Meta:
        model = MedicalPrescription
        fields = (
            'id',
            'health_insurance_plan',
            'status',
            'doctor_crm',
            'doctor_name',
            'picture_insurance_card_front',
            'picture_insurance_card_back',
            'picture_prescription',
            'picture_insurance_card_front_url',
            'picture_insurance_card_back_url',
            'picture_prescription_url',
            'picture_id_front_url',
            'picture_id_back_url',
            'selfie_url',
            'insurance_company_id',
            'patient',
            'modified_at_timestamp',
            'additional_info',
            'exams_not_registered',

            'picture_insurance_card_front_uploadcare',
            'picture_prescription_uploadcare',
            'picture_insurance_card_back_uploadcare',
            'picture_insurance_card_front_uploadcare_url',
            'picture_prescription_uploadcare_url',
            'picture_insurance_card_back_uploadcare_url',

            'picture_id_front_uploadcare_url',
            'picture_id_back_uploadcare_url',
            'selfie_uploadcare_url',
            'period_info'

        )

    def update(self, instance, validated_data):
        """
        Update and return an existing `MedicalPrescription` instance, given the validated data.
        """
        # Latest prescription update
        async_data = {}
        self.latest_prescription = instance
        patient = self._save_patient(instance, validated_data.pop('patient', None), async_data)

        # Pictures update
        self._update_images(instance, validated_data, patient)
        picture_insurance_card_front_uploadcare = validated_data.pop("picture_insurance_card_front_uploadcare", None)
        picture_insurance_card_back_uploadcare = validated_data.pop("picture_insurance_card_back_uploadcare", None)
        picture_prescription_uploadcare = validated_data.pop("picture_prescription_uploadcare", None)

        # Set dependencies from ids
        self._set_insurance_company(validated_data, instance)

        # Save it
        instance.__dict__.update(validated_data)

        request = self.context.get("request", None)
        if request and request.user:
            instance.modified_by = request.user

        instance.save()

        # Upload pictures from uploadcare asynchronously
        async_data.update(
            {
                'get_pictures_method': 'get_picture_as_content_file_uploadcare',
                'prescription_id': instance.pk,
                'picture_insurance_card_front_uploadcare': picture_insurance_card_front_uploadcare,
                'picture_insurance_card_back_uploadcare': picture_insurance_card_back_uploadcare,
                'picture_prescription_uploadcare': picture_prescription_uploadcare,
            }
        )
        if self.latest_prescription:
            async_data['latest_prescription_pk'] = self.latest_prescription.pk

        create_images.apply_async(
            kwargs=async_data,
            countdown=5,
        )
        return instance

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

    def _update_images(self, instance, validated_data, patient):
        """
        Updates images according to ones provided in the request
        :param instance:
        :param validated_data:
        :param patient:
        :return
        """

        if validated_data.get("picture_insurance_card_front", None):
            instance.picture_insurance_card_front = self._get_picture_as_content_file(
                validated_data,
                "picture_insurance_card_front"
            )
            validated_data["picture_insurance_card_front"] = instance.picture_insurance_card_front
            validated_data["picture_insurance_card_front_uploadcare"] = instance.picture_insurance_card_front_uploadcare

        if validated_data.get("picture_insurance_card_back", None):
            instance.picture_insurance_card_back = self._get_picture_as_content_file(
                validated_data,
                "picture_insurance_card_back"
            )
            validated_data["picture_insurance_card_back"] = instance.picture_insurance_card_back
            validated_data["picture_insurance_card_back_uploadcare"] = instance.picture_insurance_card_back_uploadcare

        if validated_data.get("picture_prescription", None):
            instance.picture_prescription = self._get_picture_as_content_file(
                validated_data,
                "picture_prescription"
            )
            validated_data["picture_prescription"] = instance.picture_prescription
            validated_data["picture_prescription_uploadcare"] = instance.picture_prescription_uploadcare

        if patient:
            instance.patient = patient

            validated_data["picture_id_front"] = patient.picture_id_front
            validated_data["picture_id_back"] = patient.picture_id_back
            validated_data["selfie"] = patient.selfie

            validated_data["picture_id_front_uploadcare"] = patient.picture_id_front_uploadcare
            validated_data["picture_id_back_uploadcare"] = patient.picture_id_back_uploadcare
            validated_data["selfie_uploadcare"] = patient.selfie_uploadcare

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


class MedicalPrescriptionCreateSerializer(MedicalPrescriptionSerializer):

    patient = serializers.DictField(required=True)

    picture_insurance_card_front = serializers.CharField(required=False, allow_blank=True, validators=[Base64Validator()])
    picture_insurance_card_back = serializers.CharField(required=False, allow_blank=True, validators=[Base64Validator()])
    picture_prescription = serializers.CharField(required=False, validators=[Base64Validator()])

    picture_insurance_card_front_uploadcare = serializers.CharField(required=False, allow_blank=True, validators=[URLValidator()])
    picture_insurance_card_back_uploadcare = serializers.CharField(required=False, allow_blank=True, validators=[URLValidator()])
    picture_prescription_uploadcare = serializers.CharField(required=False, validators=[URLValidator()])

    insurance_company_id = serializers.IntegerField(required=False)
    health_insurance_plan = HealthInsurancePlanSerializer(read_only=True)

    class Meta:
        model = MedicalPrescription
        fields = (
            'health_insurance_plan',
            'status',
            'doctor_crm',
            'doctor_name',

            # TODO: remove these fields when base64 apps version is no longer supported
            'picture_insurance_card_front',
            'picture_insurance_card_back',
            'picture_prescription',

            'patient',
            'insurance_company_id',
            'modified_at_timestamp',
            'additional_info',
            'exams_not_registered',

            'picture_insurance_card_front_uploadcare',
            'picture_insurance_card_back_uploadcare',
            'picture_prescription_uploadcare',

            'period_info'
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
            instance = super(MedicalPrescriptionCreateSerializer, self).create(prepared_data)
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

    def _prepare_data(self, validated_data, patient):
        """
        Prepares validated data.
        :param validated_data:
        :param patient:
        :return:
        """
        if not validated_data.get('picture_prescription', None) and \
                not validated_data.get('picture_prescription_uploadcare', None):
            raise serializers.ValidationError({"picture_prescription": "This field is required"})

        # Setting patient
        validated_data['patient'] = patient

        # Copying ID and Selfie images to current Prescription (historical purposes):
        # TODO: remove these fields when base64 apps version is no longer supported
        validated_data["picture_id_front"] = patient.picture_id_front
        validated_data["picture_id_back"] = patient.picture_id_back
        validated_data["selfie"] = patient.selfie

        validated_data["picture_id_front_uploadcare"] = patient.picture_id_front_uploadcare
        validated_data["picture_id_back_uploadcare"] = patient.picture_id_back_uploadcare
        validated_data["selfie_uploadcare"] = patient.selfie_uploadcare

        # Setting insurance company
        validated_data['insurance_company'] = self._get_insurance_company(validated_data)

        # This data is going to be updated later on
        # TODO: remove these fields when base64 apps version is no longer supported
        validated_data.pop("picture_insurance_card_front", None)
        validated_data.pop("picture_insurance_card_back", None)
        validated_data.pop("picture_prescription", None)

        validated_data.pop("picture_insurance_card_front_uploadcare", None)
        validated_data.pop("picture_insurance_card_back_uploadcare", None)
        validated_data.pop("picture_prescription_uploadcare", None)

        request = self.context.get("request", None)
        if request and request.user:
            validated_data["modified_by"] = request.user

        return validated_data

    def _post_save(self, instance, validated_data, async_data):
        """
        Saves pictures and exams for medical prescription.
        :param instance:
        :param validated_data:
        :param async_data:
        :return:
        """
        # Parsing base64 into images
        # TODO: remove these fields when base64 apps version is no longer supported
        picture_insurance_card_front = self._get_picture_as_content_file(validated_data, "picture_insurance_card_front")
        picture_insurance_card_back = self._get_picture_as_content_file(validated_data, "picture_insurance_card_back")
        picture_prescription = self._get_picture_as_content_file(validated_data, "picture_prescription")

        picture_insurance_card_front_uploadcare = validated_data.pop("picture_insurance_card_front_uploadcare", None)
        picture_insurance_card_back_uploadcare = validated_data.pop("picture_insurance_card_back_uploadcare", None)
        picture_prescription_uploadcare = validated_data.pop("picture_prescription_uploadcare", None)

        # Pictures update
        instance.picture_insurance_card_front = picture_insurance_card_front
        instance.picture_insurance_card_back = picture_insurance_card_back
        instance.picture_prescription = picture_prescription
        instance.save()

        # Upload pictures from uploadcare asynchronously
        async_data.update(
            {
                'get_pictures_method': 'get_picture_as_content_file_uploadcare',
                'prescription_id': instance.pk,
                'picture_insurance_card_front_uploadcare': picture_insurance_card_front_uploadcare,
                'picture_insurance_card_back_uploadcare': picture_insurance_card_back_uploadcare,
                'picture_prescription_uploadcare': picture_prescription_uploadcare,
            }
        )
        if self.latest_prescription:
            async_data['latest_prescription_pk'] = self.latest_prescription.pk

        create_images.apply_async(
            kwargs=async_data,
            countdown=5,
        )

        return instance

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


class ScheduledExamPhoneCallSerializer(serializers.ModelSerializer):
    call_time_timestamp = serializers.SerializerMethodField()

    class Meta:
        model = ScheduledExamPhoneCall
        fields = ('id', 'phone', 'call_time_timestamp')

    @staticmethod
    def get_call_time_timestamp(instance):
        """
        Gets call_time as timestamp dynamically
        :param instance:
        :return:
        """
        return int(instance.call_time.timestamp())


class ScheduledExamPhoneCallCreateSerializer(serializers.ModelSerializer):
    scheduled_exam_id = serializers.IntegerField(allow_null=False)
    call_time = serializers.IntegerField(write_only=True, allow_null=False)
    call_time_timestamp = serializers.SerializerMethodField()

    class Meta:
        model = ScheduledExamPhoneCall
        fields = ('id', 'scheduled_exam_id', 'call_time', 'call_time_timestamp', 'phone', 'is_canceled')

    def create(self, validated_data):
        """
        Create and return a new `ScheduledExamPhoneCall` instance.
        """
        prepared_data = self._prepare_data(validated_data.copy())
        with reversion.create_revision():
            instance = super(ScheduledExamPhoneCallCreateSerializer, self).create(prepared_data)
            reversion.set_user(self.context.get("request").user)
            reversion.set_comment("Sara Concierge Backoffice Call Attempt: #{}".format(0))
        return instance

    def _prepare_data(self, validated_data):
        """
        Prepares validated data.
        :param validated_data:
        :return:
        """
        # Parses timestamp into datetime
        call_time_timestamp = validated_data.get("call_time", None)
        if call_time_timestamp:
            call_time_timestamp = utils.remove_milliseconds_from_timestamp(call_time_timestamp)
            validated_data["call_time"] = datetime.datetime.fromtimestamp(call_time_timestamp)

        # Parses scheduled_exam_id into object
        scheduled_exam_id = validated_data.pop("scheduled_exam_id", None)
        validated_data["scheduled_exam"] = ScheduledExam.objects.get(pk=scheduled_exam_id)

        self._validate_data(validated_data)

        return validated_data

    @staticmethod
    def get_call_time_timestamp(instance):
        """
        Gets call_time as timestamp dynamically
        :param instance:
        :return:
        """
        return int(instance.call_time.timestamp())

    @staticmethod
    def _validate_data(validated_data):
        """
        Validates data before saving
        :param validated_data:
        :return:
        """
        scheduled_exam = validated_data["scheduled_exam"]

        if not scheduled_exam.exam.is_scheduled_by_phone:
            raise serializers.ValidationError({"scheduled_exam": "The current exam can't be scheduled by phone"})


class ScheduledExamPhoneCallUpdateSerializer(serializers.ModelSerializer):
    scheduled_exam_id = serializers.SerializerMethodField()
    call_time = serializers.IntegerField(write_only=True, allow_null=False)
    call_time_timestamp = serializers.SerializerMethodField()

    class Meta:
        model = ScheduledExamPhoneCall
        fields = ('scheduled_exam_id', 'call_time', 'call_time_timestamp', 'phone', 'is_canceled')

    def update(self, instance, validated_data):
        """
        Create and return a new `ScheduledExamPhoneCall` instance.
        """
        prepared_data = self._prepare_data(validated_data.copy())
        instance = super(ScheduledExamPhoneCallUpdateSerializer, self).update(instance, prepared_data)
        return instance

    @staticmethod
    def _prepare_data(validated_data):
        """
        Prepares validated data.
        :param validated_data:
        :return:
        """
        # Parses timestamp into datetime
        call_time_timestamp = validated_data.get("call_time", None)
        validated_data["attempt"] = 0
        if call_time_timestamp:
            call_time_timestamp = utils.remove_milliseconds_from_timestamp(call_time_timestamp)
            validated_data["call_time"] = datetime.datetime.fromtimestamp(call_time_timestamp)

        return validated_data

    @staticmethod
    def get_call_time_timestamp(instance):
        """
        Gets call_time as timestamp dynamically
        :param instance:
        :return:
        """
        return int(instance.call_time.timestamp())

    @staticmethod
    def get_scheduled_exam_id(instance):
        """
        Dynamically gets scheduled exam id
        :param instance:
        :return:
        """
        return instance.scheduled_exam.id


class ScheduledExamPhoneCallBatchSerializer(serializers.ModelSerializer):
    scheduled_exams_id = serializers.IntegerField(allow_null=False, required=True, write_only=True)
    call_time = serializers.IntegerField(write_only=True, allow_null=False)
    call_time_timestamp = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ScheduledExamPhoneCall
        fields = ('id', 'scheduled_exam_id', 'call_time', 'call_time_timestamp', 'phone', 'is_canceled',
                  'scheduled_exams_id')

    @staticmethod
    def get_call_time_timestamp(instance):
        """
        Gets call_time as timestamp dynamically
        :param instance:
        :return:
        """
        return int(instance.call_time.timestamp())

    @staticmethod
    def _prepare_data(validated_data):
        """
        Prepares validated data.
        :param validated_data:
        :return:
        """
        # Parses timestamp into datetime
        scheduled_time_timestamp = validated_data.get("call_time", None)
        validated_data["attempt"] = 0
        if scheduled_time_timestamp:
            try:
                scheduled_time_timestamp = int(scheduled_time_timestamp)
            except ValueError:
                raise ValueError("Field 'call_time' should be an int timestamp")

            scheduled_time_timestamp = utils.remove_milliseconds_from_timestamp(scheduled_time_timestamp)
            validated_data["call_time"] = datetime.datetime.fromtimestamp(scheduled_time_timestamp)

            day = validated_data["call_time"].day
            month = validated_data["call_time"].month

            if (day == 25 and month == 12) or (day == 1 and month == 1):
                raise ValueError("Sem expediente em feriados nacionais.")

        return validated_data

    @transaction.atomic
    def batch_update(self, data):
        """
        Updates ScheduledExamPhoneCall(s) in batch all at once in order to save HTTP requests when
        scheduling Exams packages
        :param data:
        :return:
        """
        if "scheduled_exams_id" not in data:
            raise ValueError("The following field(s) is mandatory: [scheduled_exams_id]")

        calls = []
        scheduled_exams = ScheduledExam.objects.filter(pk__in=data.pop("scheduled_exams_id"))
        if scheduled_exams.count() > 1:
            scheduled_exams.update(is_grouped=True)
        prepared_data = self._prepare_data(data.copy())

        for exam in scheduled_exams:
            # This rule was removed due to grouping logic (V2) that allows AC/RDI exams to be in the same group:
            # https://realtimeboard.com/app/board/o9Jk0A-3ak=/?moveToWidget=3074457345887589206

            # if not exam.exam.is_scheduled_by_phone:
            #     raise ValueError("All exams inside this request must be scheduled by phone (is_scheduled_by_phone=True)")

            try:
                call = ScheduledExamPhoneCall.objects.get(scheduled_exam=exam)
                call = super(ScheduledExamPhoneCallBatchSerializer, self).update(call, prepared_data)
            except ObjectDoesNotExist:
                with reversion.create_revision():
                    call = ScheduledExamPhoneCall(scheduled_exam=exam, **prepared_data)
                    call.save()
                    reversion.set_user(self.context.get("request").user)
                    reversion.set_comment("Sara Concierge Backoffice Call Attempt: #{}".format(0))
            calls.append(call)

        return calls


class HolidaySerializer(serializers.Serializer):
    holidays = serializers.SerializerMethodField()

    def get_holidays(self, instance):
        """
        Dynamically gets holidays list for given params
        """
        holidays = self.context.get("queryset")
        if holidays:
            data = [holiday.date.strftime("%d/%m") for holiday in holidays]
            return data
