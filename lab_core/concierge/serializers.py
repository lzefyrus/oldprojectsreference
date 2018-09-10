# encode: utf-8

import datetime
import json
import pytz

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from rest_framework import serializers

from dateutil import parser
from reversion.models import Version
import domain.models as domain_models
from domain.tasks import send_push_notification
from domain.utils import (
    firebase_token,
    remove_milliseconds_from_timestamp,
    get_notification_data,
    grouped_exams_by_lab_date_keygen,
    get_date_from_timestamp,
    get_gmt_time
)

from .models import Operator

import reversion

from patient_api.utils import (
    get_prescription_version,
    get_scheduled_exam_version
)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'is_staff')


class OperatorInfoSerializer(serializers.ModelSerializer):
    abbreviation = serializers.SerializerMethodField()
    user = UserSerializer()
    firebase_token = serializers.SerializerMethodField()

    class Meta:
        model = Operator
        fields = ('avatar', 'pk', 'user', 'abbreviation', 'firebase_token')

    @staticmethod
    def get_abbreviation(obj):
        return (obj.user.username and obj.user.username[:1].upper()) or (
                obj.user.email and obj.user.email[:1].upper) or obj.user.first_name

    @staticmethod
    def get_firebase_token(obj):
        return firebase_token(obj)


class PreparationStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = domain_models.PreparationStep
        fields = '__all__'

        extra_kwargs = {
            "description": {"required": False, },
            "exam": {"required": False, },
            "laboratory": {"required": False, },
        }


class LaboratorySerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    brand = serializers.StringRelatedField()
    preparation_steps = serializers.SerializerMethodField()

    class Meta:
        model = domain_models.Laboratory
        fields = ('name', 'brand', 'description', 'id', 'street', 'preparation_steps')

    @staticmethod
    def get_name(obj):
        return str(obj)

    @staticmethod
    def get_preparation_steps(obj):
        return []
        # return PreparationStepSerializer(obj.preparationstep_set.all(), many=True).data


class PatientRetrieveSerializer(serializers.ModelSerializer):
    preferred_laboratories = LaboratorySerializer(many=True)
    email = serializers.SerializerMethodField(required=False)
    selfie = serializers.SerializerMethodField(required=False)

    class Meta:
        model = domain_models.Patient
        fields = ('preferred_laboratories', 'gender', 'email', 'birth_date', 'created', 'selfie', 'full_name', 'phone')

    @staticmethod
    def get_email(instance):
        return instance.user.email

    def get_selfie(self, instance):
        try:
            request = self.context.get('request')
            if instance.selfie_uploadcare:
                picture_url = getattr(instance, 'selfie_uploadcare').url
            else:
                picture_url = getattr(instance, 'selfie').url
            return request.build_absolute_uri(picture_url)
        except:
            return None


class PrescriptionExamSerializer(serializers.ModelSerializer):
    class Meta:
        model = domain_models.Exam
        fields = ('pk', 'name', 'description', 'external_id', 'exam_type', 'is_scheduled_by_phone')
        read_only = True


class ExamSerializer(serializers.ModelSerializer):
    class Meta:
        model = domain_models.Exam
        fields = '__all__'


class InsuranceCompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = domain_models.InsuranceCompany
        fields = '__all__'


class HealthInsuranceSerializer(serializers.ModelSerializer):
    insurance_company = InsuranceCompanySerializer()

    class Meta:
        model = domain_models.HealthInsurance
        fields = ('id', 'external_id', 'description', 'cnpj', 'insurance_company')


class HealthInsurancePlanSerializer(serializers.ModelSerializer):
    health_insurance_external_id = serializers.SerializerMethodField()

    class Meta:
        model = domain_models.HealthInsurancePlan
        fields = ('id', 'health_insurance_external_id', 'plan_code')

    @staticmethod
    def get_health_insurance_external_id(instance):
        try:
            return instance.health_insurance.external_id
        except AttributeError:
            return None


class DashboardSerializer(serializers.Serializer):
    prescription_total = serializers.IntegerField()
    prescription_oldest_today = serializers.IntegerField()
    eligible_total = serializers.IntegerField()
    eligible_oldest_today = serializers.IntegerField()
    preregister_total = serializers.IntegerField()
    preregister_oldest_today = serializers.IntegerField()
    canceled_total = serializers.IntegerField()
    canceled_oldest_today = serializers.IntegerField()


class ScheduledExamPhoneCallExamSerializer(serializers.ModelSerializer):
    call_time_timestamp = serializers.SerializerMethodField()

    class Meta:
        model = domain_models.ScheduledExamPhoneCall
        fields = ('id', 'phone', 'call_time_timestamp', 'attempt')

    @staticmethod
    def get_call_time_timestamp(instance):
        """
        Gets call_time as timestamp dynamically
        :param instance:
        :return:
        """
        return int(instance.call_time.timestamp())


class PrescriptionScheduledExamSerializer(serializers.ModelSerializer):
    exam = PrescriptionExamSerializer()
    laboratory = serializers.SerializerMethodField()
    suggested_lab_ids = serializers.SerializerMethodField()
    scheduled_time_timestamp = serializers.SerializerMethodField()
    phone_call = serializers.SerializerMethodField()
    # phone_call_history = serializers.SerializerMethodField()
    status_versions = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = domain_models.ScheduledExam
        fields = ('id', 'exam', 'laboratory', 'status', 'scheduled_time_timestamp', 'procedure_average_duration',
                  'confirmation', 'annotations', 'suggested_lab_ids', 'phone_call', 'status_versions')
        read_only = True

    @staticmethod
    def get_laboratory(scheduled_exam):
        """
        Retrieve the laboratory data with filtered preparation steps
        :param scheduled_exam:
        :return:
        """

        try:
            lab = scheduled_exam.laboratory
            # fields = ('name', 'brand', 'description', 'id', 'street', 'preparation_steps')
            data = {'name': lab.description,
                    'brand:': lab.brand.name,
                    'description': lab.description if lab else '',
                    'id': lab.pk,
                    'street': lab.street}
            preps = []

            ps = domain_models.PreparationStep.objects.filter(exam_id__in=[scheduled_exam.exam],
                                                              laboratory_id=lab.pk)
            data['preparation_steps'] = [{'exam': i.exam_id,
                                          'start_preparation_in_hours': i.start_preparation_in_hours,
                                          'title': i.title,
                                          'description': i.description,
                                          'recent_description': i.recent_description,
                                          'is_mandatory': i.is_mandatory} for i in ps]
            return data

        except Exception as e:
            print(e)
            return {}

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
    def get_suggested_lab_ids(scheduled_exam):
        """
        Gets all suggested lab ids as a list
        :param scheduled_exam:
        :return:
        """
        try:
            return [lab.id for lab in scheduled_exam.suggested_labs.all()]
        except:
            return []

    @staticmethod
    def get_phone_call(scheduled_exam):
        """
        Gets related ScheduledExamPhoneCall object
        :param scheduled_exam:
        :return:
        """
        try:
            swpces = ScheduledExamPhoneCallExamSerializer(
                domain_models.ScheduledExamPhoneCall.objects.get(scheduled_exam_id=scheduled_exam.id)).data
            try:
                if swpces:
                    versions = Version.objects.get_for_object(scheduled_exam.scheduledexamphonecall)

                    data = {"scheduled_time": int(
                        scheduled_exam.scheduledexamphonecall.call_time.timestamp()) if scheduled_exam.scheduledexamphonecall.created else 0,
                            "call_time": 0}
                    vdata = []
                    tmp_call = 0
                    for version in versions:
                        version_data = json.loads(version.serialized_data)[0]['fields']
                        vdata.append({"scheduled_time": int(
                            parser.parse(version_data.get('call_time', '')).timestamp() if version_data.get('call_time',
                                                                                                            None) else 0),
                                      "call_time": tmp_call
                                      })
                        tmp_call = int(
                            version.revision.date_created.timestamp()) if version.revision.date_created else 0

                    print("#####")
                    print(vdata)
                    if len(vdata) > 0:
                        vdata.reverse()
                        vdata.pop()
                    vdata.append(data)
                    swpces['phone_call_history'] = vdata
                    print(swpces['phone_call_history'])
            except Exception as e:
                print(e)

            return swpces

        except Exception as e:
            print(e)
            return {}

    @staticmethod
    def get_phone_call_history(scheduled_exam):
        """
        Gets related ScheduledExamPhoneCall history object
        :param scheduled_exam:
        :return:
        """
        # TODO retrieve the versions data for item and return a ordered list
        try:

            versions = Version.objects.get_for_object(scheduled_exam.scheduledexamphonecall)

            data = [{"scheduled_time": int(scheduled_exam.scheduledexamphonecall.created.timestamp()),
                     "call_time": int(scheduled_exam.scheduledexamphonecall.call_time.timestamp())}]
            for version in versions:
                version_data = json.loads(version.serialized_data)[0]['fields']
                data.append({"scheduled_time": int(parser.parse(version.created).timestamp()),
                             "call_time": int(parser.parse(version_data['modified']).timestamp())
                             })
            return data
        except:
            return {}

    @staticmethod
    def get_status_versions(instance):
        """
        Retrieves status versions dynamically.
        :param scheduled_exam:
        :return:
        """
        try:
            return get_prescription_version(instance, "status")
        except:
            return []


class RejectionReasonSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField(read_only=True)
    label = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = domain_models.RejectionReason
        fields = '__all__'

    @staticmethod
    def get_type(instance):
        """
        Dynamically gets type
        :param instance:
        :return:
        """
        if instance.status == domain_models.RejectionReason.REJECTED_REQUEST_EXPIRED:
            return 'expired'
        return 'prescription' if instance.status in domain_models.RejectionReason.PRESCRIPTION_REASONS else 'piece'

    @staticmethod
    def get_label(instance):
        """
        Dynamically gets label
        :param instance:
        :return:
        """
        return instance.get_status_display()


class PrescriptionPieceSerializer(serializers.ModelSerializer):
    prescription_issued_at_timestamp = serializers.SerializerMethodField(read_only=True)
    expiration_date_timestamp = serializers.SerializerMethodField(read_only=True)
    rejection_reasons = serializers.SerializerMethodField(read_only=True)
    created = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = domain_models.PrescriptionPiece
        fields = '__all__'

    @staticmethod
    def get_expiration_date_timestamp(instance):
        """
        Dynamically gets expiration_date as timestamp
        :param instance:
        :return:
        """
        try:
            return int(instance.expiration_date.timestamp())
        except:
            return None

    @staticmethod
    def get_prescription_issued_at_timestamp(instance):
        """
        Dynamically gets prescription_issued_at as timestamp
        :param instance:
        :return:
        """
        try:
            return int(instance.prescription_issued_at.timestamp())
        except:
            return None

    @staticmethod
    def get_rejection_reasons(instance):
        rejection_reasons = instance.rejection_reasons.all()
        if rejection_reasons.exists():
            return [reason.status for reason in rejection_reasons]

    @staticmethod
    def get_created(instance):
        """
        Dynamically gets creation as timestamp
        :param instance:
        :return:
        """
        try:
            return int(instance.created.timestamp())
        except:
            return instance.created


class PrescriptionSerializer(serializers.ModelSerializer):
    scheduled_exams = serializers.SerializerMethodField(required=False)
    insurance_company = serializers.StringRelatedField(read_only=True)
    health_insurance_plan = HealthInsurancePlanSerializer(required=False)
    expiration_date_timestamp = serializers.SerializerMethodField(read_only=True)
    expiration_date = serializers.DateTimeField(required=False, write_only=True)
    prescription_issued_at_timestamp = serializers.SerializerMethodField(read_only=True)
    prescription_issued_at = serializers.DateTimeField(required=False, write_only=True)
    created = serializers.SerializerMethodField(read_only=True)
    modified = serializers.SerializerMethodField(read_only=True)
    health_insurance = HealthInsuranceSerializer(required=False)
    status_versions = serializers.SerializerMethodField(read_only=True)
    pieces = PrescriptionPieceSerializer(many=True)
    rejection_reasons = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = domain_models.MedicalPrescription
        fields = '__all__'

    @staticmethod
    def get_scheduled_exams(prescription):
        return PrescriptionScheduledExamSerializer(domain_models.ScheduledExam.objects.filter(
            prescription=prescription.id).exclude(status=domain_models.ScheduledExam.EXAM_EXPIRED), many=True).data

    @staticmethod
    def get_expiration_date_timestamp(instance):
        """
        Dynamically gets expiration_date as timestamp
        :param instance:
        :return:
        """
        try:
            return int(instance.expiration_date.timestamp())
        except:
            return None

    @staticmethod
    def get_prescription_issued_at_timestamp(instance):
        """
        Dynamically gets prescription_issued_at as timestamp
        :param instance:
        :return:
        """
        try:
            return int(instance.prescription_issued_at.timestamp())
        except:
            return None

    @staticmethod
    def get_created(instance):
        """
        Dynamically gets creation as timestamp
        :param instance:
        :return:
        """
        try:
            return int(instance.created.timestamp())
        except:
            return None

    @staticmethod
    def get_modified(instance):
        """
        Dynamically gets modification date as timestamp
        :param instance:
        :return:
        """
        try:
            return int(instance.modified.timestamp())
        except:
            return None

    @staticmethod
    def get_status_versions(instance):
        """
        Retrieves status versions dynamically.
        :param scheduled_exam:
        :return:
        """
        try:
            return get_prescription_version(instance, "status")
        except:
            return []

    @staticmethod
    def get_rejection_reasons(instance):
        rejection_reasons = instance.rejection_reasons.all()
        if rejection_reasons.exists():
            return [reason.status for reason in rejection_reasons]


class PrescriptionUpdateSerializer(PrescriptionSerializer):
    exams = serializers.ListField(required=False)
    # rejection_reasons = RejectionReasonSerializer(many=True)
    rejection_reasons = serializers.ListField(required=False)
    health_insurance_plan_id = serializers.IntegerField(write_only=True, required=False)
    insurance_company_id = serializers.IntegerField(write_only=True, required=False)

    expiration_date = serializers.IntegerField(required=False, write_only=True)
    prescription_issued_at = serializers.IntegerField(required=False, write_only=True)
    pieces = serializers.ListField(required=False)

    class Meta:
        model = domain_models.MedicalPrescription
        fields = (
            'exams', 'status', 'health_insurance_plan_id', 'insurance_company_id',
            'insurance_company', 'doctor_crm', 'doctor_name', 'selfie_id_matches',
            'picture_insurance_card_front', 'picture_insurance_card_back', 'picture_prescription',
            'picture_id_back', 'picture_id_front', 'selfie', 'exams', 'health_insurance_plan',
            'exams_not_registered', 'additional_info', 'expiration_date', 'expiration_date_timestamp',
            'prescription_issued_at', 'prescription_issued_at_timestamp', 'annotations', 'laboratory_brands',
            'period_info',
            'pieces',
            'rejection_reasons'
        )

    @transaction.atomic
    def update(self, instance, validated_data):
        """
        Update and return an existing `Prescription` and `PrescriptionPiece` instance(s), given the validated data.
        """
        pieces_data = validated_data.pop("pieces", [])
        instance_pieces_count = instance.pieces.count()

        insurance_company = self.get_insurance_company(validated_data)
        if insurance_company:
            instance.insurance_company = insurance_company

        health_insurance_plan = self.get_health_insurance_plan(validated_data)
        if health_insurance_plan:
            instance.health_insurance_plan = health_insurance_plan

        health_insurance = self.get_health_insurance(validated_data)
        if health_insurance:
            instance.health_insurance = health_insurance

        with transaction.atomic():

            if pieces_data:
                instance = self._save_pieces(pieces_data, instance, validated_data)

                # Update same fields on MedicalPrescription due to retro compatibility with old app versions
                prescription_pieces = instance.pieces.all()
                not_expired_pieces = prescription_pieces.exclude(
                    status=domain_models.PrescriptionPiece.REQUEST_EXPIRED).count()

                # MedicalPrescription must maintain its status=REQUEST_EXPIRED
                if not_expired_pieces == 0:
                    validated_data.pop("status")

                # Since old MedicalPrescription instance can have only one PrescriptionPiece:
                if instance_pieces_count == 1:
                    pieces_data[0].pop('id', None)
                    instance.__dict__.update(pieces_data[0])
            prescription_rejection_reasons = validated_data.get('rejection_reasons', None)
            if prescription_rejection_reasons:
                instance.rejection_reasons.clear()
                [instance.rejection_reasons.add(reason) for reason in prescription_rejection_reasons]
            instance.__dict__.update(validated_data)
            instance.save()



            return instance

    def _save_pieces(self, pieces_data, instance, validated_data):
        """
        Saves nested piece objects
        :param pieces_data:
        :param instance:
        :param validated_data:
        :return:
        """
        for piece_data in pieces_data:
            prescription_piece = instance.pieces.get(
                pk=piece_data.get("id")
            )

            expiration_date = self._get_expiration_date(piece_data)
            if expiration_date:
                validated_data["expiration_date"] = expiration_date
                piece_data["expiration_date"] = expiration_date

            prescription_issued_at = self._get_prescription_issued_at(piece_data)
            if prescription_issued_at:
                validated_data["prescription_issued_at"] = prescription_issued_at
                piece_data["prescription_issued_at"] = prescription_issued_at

            exam_ids = piece_data.get("exams", None)
            rejection_reasons = piece_data.get("rejection_reasons", None)
            if rejection_reasons:
                prescription_piece.rejection_reasons.clear()
                [prescription_piece.rejection_reasons.add(reason) for reason in rejection_reasons]
            if not exam_ids:
                prescription_piece.__dict__.update(piece_data)
                prescription_piece.save()

                continue

            # Appending exams...

            # Delete existing exams:
            old_exams = domain_models.ScheduledExam.objects.filter(prescription_piece=prescription_piece.id).all()
            for exam in old_exams:
                exam.delete()

            # Insert new exams:
            exams = domain_models.Exam.objects.filter(pk__in=exam_ids).all()
            for exam in exams:
                scheduled_exam = domain_models.ScheduledExam(
                    exam=exam,
                    prescription=instance,
                    prescription_piece=prescription_piece
                )
                scheduled_exam.save()

            prescription_piece.__dict__.update(piece_data)
            prescription_piece.save()

        # If current Prescription's status was changed due to PrescriptionPiece signals, update it:
        instance = domain_models.MedicalPrescription.objects.get(pk=instance.pk)

        self.do_schedule(instance)

        return instance

    @staticmethod
    def _group_exams_v2(exams):
        """
        Groups ScheduledExams by using V2 logic:
        https://realtimeboard.com/app/board/o9J_k0A-3ak=/?moveToWidget=3074457345887589206

        :param exams:
        :return:
        """
        ac_exams = [scheduled_exam for scheduled_exam in exams if
                    scheduled_exam.exam.exam_type == domain_models.Exam.AC]
        rdi_exams = [scheduled_exam for scheduled_exam in exams if
                     scheduled_exam.exam.exam_type == domain_models.Exam.RDI]
        grouped_exams = []

        if (ac_exams and rdi_exams) or (not ac_exams and rdi_exams):

            for exam in ac_exams + rdi_exams:
                if exam.status == domain_models.ScheduledExam.PHONE_CALL_SCHEDULED:
                    grouped_exams.append(exam.id)

            if len(grouped_exams) <= 1:
                return

            domain_models.ScheduledExam.objects.filter(pk__in=grouped_exams).update(is_grouped=True)
            return

        if ac_exams:
            for exam in ac_exams:
                if exam.status == domain_models.ScheduledExam.PHONE_CALL_SCHEDULED:
                    grouped_exams.append(exam.id)
            if len(grouped_exams) <= 1:
                return

            domain_models.ScheduledExam.objects.filter(pk__in=grouped_exams).update(is_grouped=True)
            return

            # suggested_labs = set()
            # for lab_list in [lab.suggested_labs.all() for lab in grouped_exams]:
            #     for lab in lab_list:
            #         suggested_labs.add(lab)
            #
            # for lab in suggested_labs:
            #     lab_exams_counter = 0
            #     for exam in grouped_exams:
            #         if lab in exam.suggested_labs.all():
            #             lab_exams_counter += 1
            #
            #     if len(grouped_exams) == lab_exams_counter:
            #         grouped_exam_ids = [exam.id for exam in grouped_exams]
            #         domain_models.ScheduledExam.objects.filter(pk__in=grouped_exam_ids).update(is_grouped=True)
            #         break

    def do_schedule(self, instance):
        """
        Skip the prescription to phone call for all exams
        must update all schedule_exams also
        :param instance:
        :return: instance
        """
        sc_status = domain_models.ScheduledExam.PHONE_CALL_SCHEDULED
        mp_status = domain_models.MedicalPrescription.EXAMS_ANALYZED

        now = datetime.datetime.now()
        phone = instance.patient.phone

        sc_pieces = instance.scheduledexam_set.all()

        with transaction.atomic():

            for scp in sc_pieces:
                scp.status = sc_status
                # scp.scheduled_time = now
                ss = domain_models.ScheduledExamPhoneCall(scheduled_exam=scp,
                                                          phone=phone,
                                                          call_time=now+datetime.timedelta(seconds=10),
                                                          is_canceled=False,
                                                          attempt=0)
                ss.save()
                scp.save()

            instance.status = mp_status
            instance.save()

            try:
                PrescriptionUpdateSerializer.send_one_notification(instance, now, sc_pieces)
            except Exception as e:
                print("Could not send the notification to user. Traceback: {}".format(e))
        self._group_exams_v2(sc_pieces)
        return instance

    @staticmethod
    def send_one_notification(instance, now, schedules):
        print('send_one_notification')
        subject = "Você vai receber uma ligação em breve"
        message = "Sua ligação para agendamento de exame acontecerá em breve."

        eta = now + datetime.timedelta(seconds=5)
        exam = schedules.first()
        data = {
            "scheduled_exam_id": exam.pk,
            "status": domain_models.ScheduledExam.PHONE_CALL_SCHEDULED,
            "scheduled_call_time": int(exam.scheduledexamphonecall.call_time.timestamp()),
            "exam_description": ",".join([i.exam.description for i in schedules]),
            "first_name": instance.patient.full_name.split(" ")[0]
        }
        print('good')
        send_push_notification.apply_async(
            args=[instance.patient.token, subject, message, data],
            eta=eta,
        )

    @staticmethod
    def get_insurance_company(validated_data):
        """
        Gets nested insurance company by id
        :param validated_data:
        :return:
        """
        insurance_company_id = validated_data.pop('insurance_company_id', None)
        if insurance_company_id:
            return domain_models.InsuranceCompany.objects.get(pk=insurance_company_id)

        return None

    @staticmethod
    def get_health_insurance(validated_data):
        """
        Gets nested health_insurance by id
        :param validated_data:
        :return:
        """
        health_insurance_id = validated_data.pop('health_insurance_id', None)
        if health_insurance_id:
            return domain_models.HealthInsurance.objects.get(pk=health_insurance_id)

        return None

    @staticmethod
    def get_health_insurance_plan(validated_data):
        """
        Gets nested health_insurance_plan by id
        :param validated_data:
        :return:
        """
        health_insurance_plan_id = validated_data.pop('health_insurance_plan_id', None)
        if health_insurance_plan_id:
            return domain_models.HealthInsurancePlan.objects.get(pk=health_insurance_plan_id)

        return None

    @staticmethod
    def _get_expiration_date(validated_data):
        """
        Gets expiration_time field from timestamp to  datetime.
        :param validated_data:
        :return:
        """
        # Parses timestamp into datetime
        expiration_date_timestamp = validated_data.get("expiration_date", None)
        if expiration_date_timestamp:
            expiration_date_timestamp = remove_milliseconds_from_timestamp(expiration_date_timestamp)
            return datetime.datetime.fromtimestamp(expiration_date_timestamp)

        return None

    @staticmethod
    def _get_prescription_issued_at(validated_data):
        """
        Gets prescription_issued_at field from timestamp to  datetime.
        :param validated_data:
        :return:
        """
        # Parses timestamp into datetime
        prescription_issued_at_timestamp = validated_data.get("prescription_issued_at", None)
        if prescription_issued_at_timestamp:
            prescription_issued_at_timestamp = remove_milliseconds_from_timestamp(prescription_issued_at_timestamp)
            return datetime.datetime.fromtimestamp(prescription_issued_at_timestamp)

        return None


class PreregisterPrescriptionSerializer(PrescriptionSerializer):

    @staticmethod
    def get_scheduled_exams(prescription):
        return PrescriptionScheduledExamSerializer(domain_models.ScheduledExam.objects.filter(
            prescription=prescription.id, status=domain_models.ScheduledExam.EXAM_TIME_SCHEDULED), many=True).data


class ScheduledExamPrescriptionSerializer(serializers.ModelSerializer):
    insurance_company = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = domain_models.MedicalPrescription
        fields = '__all__'


class ScheduledExamSerializer(serializers.ModelSerializer):
    exam = ExamSerializer(required=False)
    laboratory = LaboratorySerializer(read_only=True)
    laboratory_id = serializers.IntegerField(write_only=True, required=False)
    prescription = ScheduledExamPrescriptionSerializer(required=False)
    scheduled_time_timestamp = serializers.SerializerMethodField()
    expiration_date_timestamp = serializers.SerializerMethodField()
    results_expected_at = serializers.IntegerField(required=False, write_only=True, allow_null=True)
    status_versions = serializers.SerializerMethodField()

    class Meta:
        model = domain_models.ScheduledExam
        fields = ('id', 'exam', 'laboratory', 'laboratory_id', 'prescription', 'status', 'scheduled_time_timestamp',
                  'procedure_average_duration', 'confirmation', 'expiration_date_timestamp',
                  'plan_product_code', 'suggested_labs', 'annotations', 'scheduled_time', 'lab_file_code',
                  'results_expected_at', 'status_versions')
        read_only = True

    @transaction.atomic
    def update(self, instance, validated_data):
        """
        Update and return an existing `ScheduledExam` instance, given the validated data.
        """
        try:
            validated_data["results_expected_at"] = get_date_from_timestamp(validated_data, "results_expected_at")
        except KeyError:
            pass

        instance.__dict__.update(validated_data)

        # Update lab info:
        lab = self.get_laboratory(validated_data)
        if lab:
            instance.laboratory = lab

        # Update suggested labs:
        suggested_labs = self._get_suggested_labs(validated_data)
        if suggested_labs:
            instance.suggested_labs = suggested_labs

        request = self.context.get('request', None)
        if request and request.user:
            instance.modified_by = request.user

        instance.save()

        return instance

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
    def get_expiration_date_timestamp(scheduled_exam):
        """
        Dynamically gets expiration date
        :param scheduled_exam:
        :return:
        """
        try:
            exam_expiration = domain_models.ExamExpiration.objects.filter(exam=scheduled_exam.exam.id,
                                                                          insurance_company=scheduled_exam.prescription.insurance_company.id).first()
            pre_defined_expiration = scheduled_exam.created + datetime.timedelta(
                days=exam_expiration.expiration_in_days)
        except AttributeError:
            pre_defined_expiration = None

        registered_expiration = int(
            scheduled_exam.expiration_date.timestamp()) if scheduled_exam.expiration_date else None
        pre_defined_expiration = int(pre_defined_expiration.timestamp()) if pre_defined_expiration else None

        return registered_expiration or pre_defined_expiration

    @staticmethod
    def get_laboratory(validated_data):
        """
        Gets laboratory by id
        :param validated_data:
        :return:
        """
        laboratory_id = validated_data.pop('laboratory_id', None)
        if laboratory_id:
            return domain_models.Laboratory.objects.get(pk=laboratory_id)

        return None

    @staticmethod
    def _get_suggested_labs(validated_data):
        suggested_labs = validated_data.pop('suggested_labs', None)
        if not suggested_labs:
            return None

        return suggested_labs

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


class ScheduledExamPhoneCallSerializer(serializers.ModelSerializer):
    call_time_timestamp = serializers.SerializerMethodField()
    scheduled_exam = ScheduledExamSerializer()

    class Meta:
        model = domain_models.ScheduledExamPhoneCall
        fields = ('id', 'scheduled_exam', 'phone', 'call_time_timestamp', 'attempt')

    @staticmethod
    def get_call_time_timestamp(instance):
        """
        Gets call_time as timestamp dynamically
        :param instance:
        :return:
        """
        return int(instance.call_time.timestamp())


class ScheduledExamByPrescriptionSerializer(serializers.ModelSerializer):
    exam = ExamSerializer(required=False)
    laboratory = LaboratorySerializer(required=False)
    scheduled_time_timestamp = serializers.SerializerMethodField()
    expiration_date_timestamp = serializers.SerializerMethodField()
    status_versions = serializers.SerializerMethodField()

    class Meta:
        model = domain_models.ScheduledExam
        fields = ('id', 'exam', 'laboratory', 'status', 'scheduled_time_timestamp',
                  'procedure_average_duration', 'confirmation', 'suggested_labs_id', 'expiration_date_timestamp',
                  'plan_product_code', 'suggested_labs', 'annotations', 'status_versions')
        read_only = True

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
    def get_expiration_date_timestamp(scheduled_exam):
        """
        Dynamically gets expiration date
        :param scheduled_exam:
        :return:
        """
        try:
            exam_expiration = domain_models.ExamExpiration.objects.filter(exam=scheduled_exam.exam.id,
                                                                          insurance_company=scheduled_exam.prescription.insurance_company.id).first()
            pre_defined_expiration = scheduled_exam.created + datetime.timedelta(
                days=exam_expiration.expiration_in_days)
        except AttributeError:
            pre_defined_expiration = None

        registered_expiration = int(
            scheduled_exam.expiration_date.timestamp()) if scheduled_exam.expiration_date else None
        pre_defined_expiration = int(pre_defined_expiration.timestamp()) if pre_defined_expiration else None

        return registered_expiration or pre_defined_expiration

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


class ExamResultSerializer(serializers.ModelSerializer):
    file = serializers.ImageField()

    class Meta:
        model = domain_models.ExamResult
        fields = ('file',)


class StatusScheduledExamSerializer(serializers.ModelSerializer):
    scheduled_exam_ids = serializers.ListField(required=True)
    status = serializers.CharField(required=True)

    class Meta:
        model = domain_models.ScheduledExam
        fields = ('scheduled_exam_ids', 'status')

    @staticmethod
    def validate_status(value):
        for item in domain_models.ScheduledExam.STATUS_CHOICES:
            if item[0] == value:
                return value

        raise serializers.ValidationError("Invalid status value: {0}".format(value))


class GroupStatusScheduledExamSerializer(ScheduledExamSerializer):
    class Meta:
        model = domain_models.ScheduledExam
        fields = ('id', 'exam', 'laboratory', 'laboratory_id', 'prescription', 'status', 'scheduled_time_timestamp',
                  'procedure_average_duration', 'confirmation', 'expiration_date_timestamp',
                  'plan_product_code', 'suggested_labs', 'annotations', 'scheduled_time', 'lab_file_code',
                  'results_expected_at', 'status_versions')
        read_only = True


class PreregisterScheduledExamSerializer(serializers.ModelSerializer):
    scheduled_exams = serializers.ListField(required=True)

    class Meta:

        model = domain_models.ScheduledExam
        fields = (
            'scheduled_exams',
            'lab_file_code'
        )

    @transaction.atomic
    def preregister_update(self, data, request_user):
        """
        Updates a bunch of scheduled_exams all together at once as a batch.

        Used on 'Abertura de Ficha' screen

        :param data:
        :param request_user:
        :return:
        """
        with transaction.atomic():
            self._save_exams(data, request_user)

    @staticmethod
    def _save_exams(data, request_user):
        """
        Save on exams

        :param data:
        :param request_user:
        :return:
        """

        # Updates each exam:
        for exam_data in data["scheduled_exams"]:
            exam = domain_models.ScheduledExam.objects.get(pk=exam_data.get("id"))

            results_expected_at = get_date_from_timestamp(exam_data, "results_expected_at")
            if not exam_data.get("status") == domain_models.ScheduledExam.LAB_RECORD_CANCELED:
                exam.lab_file_code = data.get("lab_file_code")
            exam.status = exam_data.get("status")
            exam.results_expected_at = results_expected_at
            exam.modified_by = request_user

            exam.save()


class EligibilityScheduledExamSerializer(serializers.ModelSerializer):
    scheduled_exams = serializers.ListField(required=True)

    class Meta:
        model = domain_models.ScheduledExam
        fields = ('scheduled_exams',)

    @transaction.atomic
    def eligibility_update(self, data, request_user):
        """
        Updates a bunch of scheduled_exams all together at once as a batch.

        Used on 'Elegibilidade' screen

        :param data:
        :param request_user:
        :return:
        """
        with transaction.atomic():
            exams = self._save_exams(data, request_user)

            self._group_exams_v2(exams)
            self._send_eligibility_notification(exams)

    @staticmethod
    def _save_exams(data, request_user):
        """
        Save on exams and the related prescription

        :param data:
        :param request_user:
        :return:
        """
        exams = []
        prescription_id = None

        # Updates each exam:
        for exam_data in data["scheduled_exams"]:
            exam = domain_models.ScheduledExam.objects.get(pk=exam_data["id"])

            current_prescription_id = exam.prescription.id if exam.prescription else exam.prescription_piece.prescription.id
            if prescription_id and prescription_id != current_prescription_id:
                raise ValueError("All ScheduledExams must belong to the same Prescription")

            prescription_id = exam.prescription.id or exam.prescription_piece.prescription.id
            exam.status = exam_data["status"]
            exam.suggested_labs = domain_models.Laboratory.objects.filter(pk__in=exam_data["suggested_labs"])
            exam.modified_by = request_user

            exam.save()
            exams.append(exam)

        # Save related prescription:
        with reversion.create_revision():
            prescription = domain_models.MedicalPrescription.objects.get(pk=prescription_id)
            prescription.status = domain_models.MedicalPrescription.EXAMS_ANALYZED
            prescription.save()
            reversion.set_user(request_user)
            reversion.set_comment("Sara Concierge Backoffice MP EL")

        return exams

    @staticmethod
    def _group_exams_v1(exams):
        """
        Groups ScheduledExams by using V1 logic:
        https://realtimeboard.com/app/board/o9J_k0A-3ak=/?moveToWidget=3074457345887589206

        :param exams:
        :return:
        """

        ac_exams = [scheduled_exam for scheduled_exam in exams if
                    scheduled_exam.exam.exam_type == domain_models.Exam.AC]
        rdi_exams = [scheduled_exam for scheduled_exam in exams if
                     scheduled_exam.exam.exam_type == domain_models.Exam.RDI]

        if ac_exams and rdi_exams:
            return

        grouped_exams = []
        if rdi_exams:
            for exam in rdi_exams:
                if exam.status == domain_models.ScheduledExam.ELIGIBLE_PATIENT:
                    grouped_exams.append(exam.id)

            if len(grouped_exams) <= 1:
                return

            domain_models.ScheduledExam.objects.filter(pk__in=grouped_exams).update(is_grouped=True)

        if ac_exams:
            for exam in ac_exams:
                if exam.status == domain_models.ScheduledExam.ELIGIBLE_PATIENT:
                    grouped_exams.append(exam)

            if len(grouped_exams) <= 1:
                return

            suggested_labs = set()
            for lab_list in [lab.suggested_labs.all() for lab in grouped_exams]:
                for lab in lab_list:
                    suggested_labs.add(lab)

            for lab in suggested_labs:
                lab_exams_counter = 0
                for exam in grouped_exams:
                    if lab in exam.suggested_labs.all():
                        lab_exams_counter += 1

                if len(grouped_exams) == lab_exams_counter:
                    grouped_exam_ids = [exam.id for exam in grouped_exams]
                    domain_models.ScheduledExam.objects.filter(pk__in=grouped_exam_ids).update(is_grouped=True)
                    break

    @staticmethod
    def _group_exams_v2(exams):
        """
        Groups ScheduledExams by using V2 logic:
        https://realtimeboard.com/app/board/o9J_k0A-3ak=/?moveToWidget=3074457345887589206

        :param exams:
        :return:
        """

        ac_exams = [scheduled_exam for scheduled_exam in exams if
                    scheduled_exam.exam.exam_type == domain_models.Exam.AC]
        rdi_exams = [scheduled_exam for scheduled_exam in exams if
                     scheduled_exam.exam.exam_type == domain_models.Exam.RDI]

        grouped_exams = []

        if (ac_exams and rdi_exams) or (not ac_exams and rdi_exams):

            for exam in ac_exams + rdi_exams:
                if exam.status == domain_models.ScheduledExam.PHONE_CALL_SCHEDULED:
                    grouped_exams.append(exam.id)

            if len(grouped_exams) <= 1:
                return

            domain_models.ScheduledExam.objects.filter(pk__in=grouped_exams).update(is_grouped=True)
            return

        if ac_exams:
            for exam in ac_exams:
                if exam.status == domain_models.ScheduledExam.PHONE_CALL_SCHEDULED:
                    grouped_exams.append(exam)

            if len(grouped_exams) <= 1:
                return

            suggested_labs = set()
            for lab_list in [lab.suggested_labs.all() for lab in grouped_exams]:
                for lab in lab_list:
                    suggested_labs.add(lab)

            for lab in suggested_labs:
                lab_exams_counter = 0
                for exam in grouped_exams:
                    if lab in exam.suggested_labs.all():
                        lab_exams_counter += 1

                if len(grouped_exams) == lab_exams_counter:
                    grouped_exam_ids = [exam.id for exam in grouped_exams]
                    domain_models.ScheduledExam.objects.filter(pk__in=grouped_exam_ids).update(is_grouped=True)
                    break

    @staticmethod
    def _send_eligibility_notification(exams):
        """
        Sends first notification for Patient after saving items on eligilibity screen

        :param exams:
        :return:
        """
        for exam in exams:
            # Sends positive push notification to patient:
            if exam.status == domain_models.ScheduledExam.ELIGIBLE_PATIENT:
                prescription = exam.prescription or exam.prescription_piece.prescription
                first_name = prescription.patient.full_name.split(" ")[0]

                content = get_notification_data(domain_models.ScheduledExam.ELIGIBLE_PATIENT, first_name)
                data = {"prescription_id": prescription.id, "status": prescription.status}

                send_push_notification.apply_async(args=[prescription.patient.token,
                                                         content["subject"],
                                                         content["message"],
                                                         data], )
                return

        # Sends negative push notification to patient:
        prescription = exams[0].prescription or exams[0].prescription_piece.prescription
        first_name = prescription.patient.full_name.split(" ")[0]

        content = get_notification_data(domain_models.MedicalPrescription.NOT_REGISTERED_EXAMS_FOUND, first_name)
        data = {"prescription_id": prescription.id, "status": prescription.status}

        send_push_notification.apply_async(args=[prescription.patient.token,
                                                 content["subject"],
                                                 content["message"],
                                                 data], )

    @staticmethod
    def validate_scheduled_exams(value):
        """
        Validates scheduled_exams items as:

        {
            "scheduled_exams":[
                {
                    "id": 145,
                    "status": "ELIGIBLE_PATIENT",
                    "suggested_labs": []
                },
                {
                    "id": 146,
                    "status": "NOT_ELIGIBLE_PATIENT_DUE_TO_AGE_OR_GENDER",
                    "suggested_labs": [89]
                }
            ]
        }

        :param value:
        :return:
        """
        for item in value:
            keys = item.keys()
            if "id" not in keys or "status" not in keys or "suggested_labs" not in keys:
                raise serializers.ValidationError(
                    "The following fields are mandatory: {0}, {1}, {2}".format("id", "status", "suggested_labs")
                )
            if not getattr(domain_models.ScheduledExam, item["status"], None):
                raise serializers.ValidationError("Invalid status: {0}".format(item["status"]))

        return value


class CallScheduledExamSerializer(serializers.ModelSerializer):
    scheduled_exams = serializers.ListField(required=True)

    class Meta:
        model = domain_models.ScheduledExam
        fields = ('scheduled_exams',)

    @transaction.atomic
    def call_update_ond(self, data, request_user):
        """
        Updates a bunch of scheduled_exams all together at once as a batch.

        Used on 'Ligação' screen

        :param data:
        :param request_user:
        :return:
        """
        prescription_id = None
        # Updates each exam:
        for exam_data in data["scheduled_exams"]:
            exam = domain_models.ScheduledExam.objects.get(pk=exam_data["id"])

            current_prescription_id = exam.prescription.id if exam.prescription else exam.prescription_piece.prescription.id
            if prescription_id and prescription_id != current_prescription_id:
                raise ValueError("All ScheduledExams must belong to the same Prescription")
            prescription_id = exam.prescription.id or exam.prescription_piece.prescription.id

            prepared_data = self._prepare_data(exam_data.copy(), request_user)

            exam.__dict__.update(prepared_data)

            lab_id = exam_data.pop("laboratory_id", None)
            if lab_id:
                exam.laboratory = domain_models.Laboratory.objects.get(pk=lab_id)

            exam.save()

    @transaction.atomic
    def call_update(self, data, request_user):
        """
        Updates a bunch of scheduled_exams all together at once as a batch.

        Used on 'Ligação' screen

        :param data:
        :param request_user:
        :return:
        """
        prescription_id = None
        upd = False
        # Updates each exam only if all calls attempts are done:
        canceled_exam_ids = []
        for exam_data in data["scheduled_exams"]:
            exam = domain_models.ScheduledExam.objects.get(pk=exam_data["id"])
            try:
                instance = domain_models.ScheduledExamPhoneCall.objects.get(scheduled_exam=exam)
                if exam.scheduledexamphonecall.attempt < 5 and exam_data[
                    "status"] == domain_models.ScheduledExam.PHONE_CALL_NOT_ANSWERED:
                    # update phonecalltime on schedule
                    with reversion.create_revision():
                        instance.attempt += 1
                        if instance.attempt != 5:
                            new_time = datetime.datetime.now() + \
                                       datetime.timedelta(minutes=instance.ATTEMPT_INCR_MINUTES[instance.attempt])

                            if any(((datetime.date.today().weekday() == 5 and new_time.replace(
                                    microsecond=0) > get_gmt_time(settings.OP_CLOSING_TIME_SAT)),
                                    (datetime.date.today().weekday() == 6 and new_time.replace(
                                        microsecond=0) > get_gmt_time(settings.OP_CLOSING_TIME_SUN)),
                                    (datetime.date.today().weekday() not in [5, 6] and new_time.replace(
                                        microsecond=0) > get_gmt_time(settings.OP_CLOSING_TIME_OTHER)))):

                                new_time = new_time.replace(hour=get_gmt_time(settings.NEXT_DAY_CALL_TIME).hour,
                                                            minute=0, second=0)
                                if new_time.day <= datetime.datetime.now().day:
                                    new_time = new_time + datetime.timedelta(days=1)
                            instance.call_time = new_time
                            instance.save()

                            reversion.set_user(self.context.get("request").user)
                            reversion.set_comment(
                                "Sara Concierge Backoffice Call Attempt: #{}".format(instance.attempt))
                        else:
                            instance.save()
                            upd = True
                else:
                    upd = True
            except Exception as e:
                print(e)
                print('Not Scheduled Exam Call')

            finally:
                if upd is True:
                    if exam_data["status"] == domain_models.ScheduledExam.PATIENT_CANCELED_BY_CALL:
                        canceled_exam_ids.append(exam_data["id"])
                    current_prescription_id = exam.prescription.id if exam.prescription else exam.prescription_piece.prescription.id
                    if prescription_id and prescription_id != current_prescription_id:
                        raise ValueError("All ScheduledExams must belong to the same Prescription")
                    prescription_id = exam.prescription.id or exam.prescription_piece.prescription.id

                    prepared_data = self._prepare_data(exam_data.copy(), request_user)

                    exam.__dict__.update(prepared_data)

                    lab_id = exam_data.pop("laboratory_id", None)
                    if lab_id:
                        exam.laboratory = domain_models.Laboratory.objects.get(pk=lab_id)

                    exam.save()
        if canceled_exam_ids:
            if len(canceled_exam_ids) == 1:
                domain_models.ScheduledExam.objects.filter(pk__in=canceled_exam_ids).update(is_grouped=False)

    @staticmethod
    def _prepare_data(validated_data, request_user):
        """
        Prepares validated data.
        :param validated_data:
        :param request_user:
        :return:
        """
        # Parses timestamp into datetime
        scheduled_time_timestamp = validated_data.get("scheduled_time", None)
        if scheduled_time_timestamp:
            try:
                scheduled_time_timestamp = int(scheduled_time_timestamp)
            except ValueError:
                raise ValueError("Field 'scheduled_time_timestamp' should be an int timestamp")

            scheduled_time_timestamp = remove_milliseconds_from_timestamp(scheduled_time_timestamp)
            validated_data["scheduled_time"] = datetime.datetime.fromtimestamp(scheduled_time_timestamp)

        if request_user:
            validated_data["modified_by"] = request_user

        return validated_data

    @staticmethod
    def validate_scheduled_exams(value):
        """
        Validates scheduled_exams items as:

        {
            "scheduled_exams":[
                {
                    "id": 145,
                    "status": "ELIGIBLE_PATIENT"
                },
                {
                    "id": 146,
                    "status": "NOT_ELIGIBLE_PATIENT_DUE_TO_AGE_OR_GENDER",
                    "laboratory_id": 89
                }
            ]
        }

        :param value:
        :return:
        """
        for item in value:
            keys = item.keys()
            if "id" not in keys or "status" not in keys:
                raise serializers.ValidationError(
                    "The following fields are mandatory: {0}, {1}".format("id", "status")
                )
            if not getattr(domain_models.ScheduledExam, item["status"], None):
                raise serializers.ValidationError("Invalid status: {0}".format(item["status"]))

        return value
