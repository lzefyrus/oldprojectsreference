from patient_api.serializers.v4 import (
    MedicalPrescriptionV4Serializer,
    PrescriptionPieceSerializer,
)

from rest_framework import serializers
from domain.models import *
from patient_api.serializers.v3 import HealthInsurancePlanSerializer, ScheduledExamSerializer
from patient_api.utils import (
    get_prescription_version,
)


class RejectionReasonSerializer(serializers.ModelSerializer):

    class Meta:
        model = RejectionReason
        fields = '__all__'


class PiecesRejectionReasonSerializer(RejectionReasonSerializer):
    feedback = serializers.SerializerMethodField()

    def get_feedback(self, reason):
        """
        Retrieves feedback dynamically.
        :param reason:
        :return:
        """
        if reason.status == RejectionReason.REJECTED_REQUEST_EXPIRED:
            piece = reason.prescriptionpiece_set.get(pk=self.context.get("pk"))
            expiration_date = piece.expiration_date
            expiration_date_formatted = piece.expiration_date.strftime('%d %B')
            days = (expiration_date-piece.prescription_issued_at).days
            feedback = reason.feedback.format(date=expiration_date_formatted, days=days)
            return feedback
        return reason.feedback


class PrescriptionPieceV5Serializer(PrescriptionPieceSerializer):
    rejection_reasons = serializers.SerializerMethodField()

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
            'status',
            'rejection_reasons'
        )

    def get_rejection_reasons(self, piece):
        return PiecesRejectionReasonSerializer(
            piece.rejection_reasons.all(),
            many=True,
            context={'pk': piece.pk}).data


class MedicalPrescriptionV5Serializer(MedicalPrescriptionV4Serializer):
    pieces = PrescriptionPieceV5Serializer(many=True)
    rejection_reasons = RejectionReasonSerializer(many=True)

    class Meta(MedicalPrescriptionV4Serializer.Meta):
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
            'grouped_scheduled_exams',
            'rejection_reasons'
        )


class MedicalPrescriptionRetrieveV5Serializer(MedicalPrescriptionV5Serializer):

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
            'grouped_scheduled_exams',

            'rejection_reasons',
            'preferred_laboratory_id',
            'preferred_date_to_schedule_timestamp'
        )


class MedicalPrescriptionByPatientV5Serializer(MedicalPrescriptionV5Serializer):

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

            'pieces',
            'rejection_reasons'
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