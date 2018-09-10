# encode: utf-8

import datetime
import random

import factory
from django.conf import settings
from django.contrib.gis.geos import Point

from domain.models import *
from domain.serializers import RecoverPasswordSerializer


class ExamFactory(factory.DjangoModelFactory):
    class Meta:
        model = Exam

    @factory.sequence
    def external_id(n):
        return "000{0}".format(n)

    @factory.sequence
    def name(n):
        return "111{0}".format(n)

    @factory.sequence
    def description(n):
        return "Description of 111{0}".format(n)

    @factory.sequence
    def synonymy(n):
        return "Synonymy of 111{0}".format(n)

    is_scheduled_by_phone = False


class LaboratoryBrandFactory(factory.DjangoModelFactory):
    class Meta:
        model = LaboratoryBrand

    name = "ABC"
    is_active = True


class LaboratoryFactory(factory.DjangoModelFactory):
    class Meta:
        model = Laboratory

    is_active = True
    external_id = "ABC"
    description = "Description of ABC"

    @factory.sequence
    def brand(n):
        return LaboratoryBrandFactory()

    @factory.sequence
    def cnpj(n):
        return "99.999.999/9999-9{0}".format(n)

    street = "Lost Avenue"

    @factory.sequence
    def street_number(n):
        return "{0}".format(n)

    @factory.sequence
    def zip_code(n):
        return "04802-08{0}".format(n)

    city = "Lost Town"
    district = "Lost District"
    country = "Lost Country"
    lat = -23.604497792223157
    lng = -46.66052340811692
    point = Point(-46.66052340811692, -23.604497792223157)


class UserFactory(factory.DjangoModelFactory):
    class Meta:
        model = settings.AUTH_USER_MODEL

    @factory.sequence
    def username(n):
        return "user_{0}@email.com".format(n)

    @factory.sequence
    def email(n):
        return "user_{0}@email.com".format(n)


class PatientFactory(factory.DjangoModelFactory):
    class Meta:
        model = Patient

    @factory.sequence
    def user(n):
        return UserFactory()

    @factory.sequence
    def preferred_laboratories(n):
        return [LaboratoryFactory()]

    id_device = "123456789"
    gender = 'M'
    birth_date = datetime.date(1989, 10, 24)
    full_name = "user lastname"
    phone = 5511988888888
    is_confirmed = True
    token = "asd23ed2312312312"

    @factory.sequence
    def picture_id_front(n):
        return "id/picture_patient_front_{0}.jpg".format(n)

    @factory.sequence
    def picture_id_back(n):
        return "id/picture_patient_back_{0}.jpg".format(n)

    @factory.sequence
    def selfie(n):
        return "selfie/picture_patient_{0}.jpg".format(n)


class InsuranceCompanyFactory(factory.DjangoModelFactory):
    class Meta:
        model = InsuranceCompany

    name = "Company"
    description = "Description of company"

    @factory.sequence
    def cnpj(n):
        return "99.999.999/9999-9{0}".format(n)


class HealthInsuranceFactory(factory.DjangoModelFactory):
    class Meta:
        model = HealthInsurance

    @factory.sequence
    def insurance_company(n):
        return InsuranceCompanyFactory()

    external_id = "1234124"
    description = "Health Insurance test"

    @factory.sequence
    def cnpj(n):
        return "99.999.999/9999-9{0}".format(n)

    is_active = True


class HealthInsurancePlanFactory(factory.DjangoModelFactory):
    class Meta:
        model = HealthInsurancePlan

    @factory.sequence
    def health_insurance(n):
        return HealthInsuranceFactory()

    plan_code = "0001"


class MedicalPrescriptionFactory(factory.DjangoModelFactory):
    class Meta:
        model = MedicalPrescription

    @factory.sequence
    def patient(n):
        return PatientFactory()

    @factory.sequence
    def insurance_company(n):
        return InsuranceCompanyFactory()

    @factory.sequence
    def health_insurance_plan(n):
        return HealthInsurancePlanFactory()

    status = MedicalPrescription.PATIENT_REQUESTED

    @factory.sequence
    def doctor_crm(n):
        return "123456789{0}".format(n)

    @factory.sequence
    def doctor_name(n):
        return "Dr. Joseph {0}".format(n)

    @factory.sequence
    def picture_insurance_card_front(n):
        return "insurance_card/picture_front_{0}.jpg".format(n)

    @factory.sequence
    def picture_insurance_card_back(n):
        return "insurance_card/picture_back_{0}.jpg".format(n)

    @factory.sequence
    def picture_prescription(n):
        return "prescription/picture_{0}.jpg".format(n)

    @factory.sequence
    def modified_by(n):
        return UserFactory()

recover_serializer = RecoverPasswordSerializer()


class RecoverPasswordFactory(factory.DjangoModelFactory):
    class Meta:
        model = RecoverPassword

    expiration_date = recover_serializer.get_user_password_expiration_date()
    is_used = False

    @factory.sequence
    def user(n):
        return UserFactory()

    @factory.sequence
    def token(n):
        return "XXX{0}".format(n)


class PreparationStepFactory(factory.DjangoModelFactory):
    class Meta:
        model = PreparationStep

    title = "Fasting"
    description = "Patient can't eat for the next 24 hours"
    is_mandatory = False

    @factory.sequence
    def exam(n):
        return ExamFactory()

    @factory.sequence
    def laboratory(n):
        return LaboratoryFactory()


class ExamResultFactory(factory.DjangoModelFactory):
    class Meta:
        model = ExamResult

    file = utils.base_64_to_image_file("R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=", "result.jpg")

    @factory.sequence
    def scheduled_exam(n):
        return ScheduledExamFactory()


class ExamResultDetailFactory(factory.DjangoModelFactory):
    class Meta:
        model = ExamResultDetail

    title = ""
    description = "Glicose"
    result = "10mg"
    reference_values = "5mg - 10mg"

    @factory.sequence
    def exam_result(n):
        return ExamResultFactory()


class PrescriptionPieceFactory(factory.DjangoModelFactory):
    class Meta:
        model = PrescriptionPiece

    @factory.sequence
    def prescription(n):
        return MedicalPrescriptionFactory()

    annotations = "BLA BLA"
    doctor_crm = "1234567"
    exams_not_registered = "Exam A, Exam B"
    prescription_issued_at = "2016-12-07T11:30:00Z"


class ScheduledExamFactory(factory.DjangoModelFactory):
    class Meta:
        model = ScheduledExam

    @factory.sequence
    def prescription(n):
        return MedicalPrescriptionFactory()

    @factory.sequence
    def prescription_piece(n):
        return PrescriptionPieceFactory()

    @factory.sequence
    def exam(n):
        return ExamFactory()

    @factory.sequence
    def laboratory(n):
        return LaboratoryFactory()

    status = ScheduledExam.EXAM_IDENTIFIED
    scheduled_time = "2016-12-07T11:30:00Z"

    @factory.sequence
    def lab_file_code(n):
        return "123456789{0}".format(n)

    @factory.sequence
    def modified_by(n):
        return UserFactory()


class ScheduledExamPhoneCallFactory(factory.DjangoModelFactory):
    class Meta:
        model = ScheduledExamPhoneCall

    @factory.sequence
    def scheduled_exam(n):
        return ScheduledExamFactory()

    phone = 5511961991225
    call_time = datetime.datetime.now()
    is_canceled = False


class ExamExpirationFactory(factory.DjangoModelFactory):
    class Meta:
        model = ExamExpiration

    @factory.sequence
    def exam(n):
        return ExamFactory()

    @factory.sequence
    def insurance_company(n):
        return InsuranceCompanyFactory()

    expiration_in_days = 30
