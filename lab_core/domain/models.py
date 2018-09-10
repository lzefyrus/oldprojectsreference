# encoding: utf-8

import reversion
import uuid

from django.conf import settings
from django.contrib.gis.db import models as geo_models
from django.db import models
from django_extensions.db.models import TimeStampedModel
from domain import utils
from m2m.models import ZendeskASFTicket


class Exam(TimeStampedModel):
    RDI = 'RDI'
    AC = 'AC'
    EXAM_TYPE_CHOICES = (
        (RDI, 'RDI'),
        (AC, 'Análises Clínicas'),
    )

    external_id = models.CharField(max_length=50, null=True, blank=True)
    name = models.CharField(max_length=50, null=False)
    description = models.TextField(null=True)
    synonymy = models.TextField(null=True)
    exam_type = models.CharField(choices=EXAM_TYPE_CHOICES, default=AC, max_length=8)
    is_scheduled_by_phone = models.BooleanField(default=False)

    __original_exam_type = None

    def __str__(self):
        return "%s: %s" % (self.id, self.name)

    def __init__(self, *args, **kwargs):
        super(Exam, self).__init__(*args, **kwargs)
        self.__original_exam_type = self.exam_type


class LaboratoryBrand(TimeStampedModel):
    external_id = models.CharField(max_length=50, null=True, blank=True, db_index=True)
    name = models.CharField(max_length=70, null=False, blank=False, db_index=True)
    # Set to false to hide this laboratory brand plus its unities (Laboratory) from the user
    is_active = models.BooleanField(default=False)
    similar_brand = models.ForeignKey('LaboratoryBrand', null=True, blank=True)
    premium = models.BooleanField(default=False)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return "%s: %s" % (self.id, self.name)


class Laboratory(TimeStampedModel):
    exams = models.ManyToManyField(Exam, blank=True)
    brand = models.ForeignKey(LaboratoryBrand, null=True, blank=True)
    external_id = models.CharField(max_length=50, null=True, blank=True, db_index=True)
    description = models.CharField(max_length=250, null=True)
    is_active = models.BooleanField(default=False)
    cnpj = models.CharField(max_length=50, null=False)
    street = models.CharField(max_length=250, null=False, db_index=True)
    street_number = models.CharField(max_length=10, null=False)
    complement = models.CharField(max_length=200, null=True, blank=True)
    zip_code = models.CharField(max_length=20, null=False)
    district = models.TextField(null=False)
    city = models.TextField(null=False)
    state = models.TextField(null=False)
    state_abbreviation = models.TextField(null=False)
    country = models.CharField(max_length=200, null=False)
    lat = models.FloatField(blank=True, null=True, help_text='Lat')
    lng = models.FloatField(blank=True, null=True, help_text='Long')
    point = geo_models.PointField(null=True, blank=True, help_text='Lat/Long coordinates')
    objects = geo_models.GeoManager()

    class Meta:
        index_together = (
            ('is_active', 'brand'),
            ('is_active', 'point'),
        )

    def __str__(self):
        return "%s" % self.description


class LaboratoryFacilities(TimeStampedModel):
    laboratory = models.ForeignKey(Laboratory, null=False, blank=False)
    description = models.TextField(null=False, blank=False)

    def __str__(self):
        return "%s: %s %s" % (self.id, self.laboratory.description, self.description)


class LaboratoryOpeningHours(TimeStampedModel):
    MONDAY = 1
    TUESDAY = 2
    WEDNESDAY = 3
    THURSDAY = 4
    FRIDAY = 5
    SATURDAY = 6
    SUNDAY = 7
    HOLIDAYS = 8

    DAYS_OF_THE_WEEK = (
        (MONDAY, 'Segunda-feira'),
        (TUESDAY, 'Terça-feira'),
        (WEDNESDAY, 'Quarta-feira'),
        (THURSDAY, 'Quinta-feira'),
        (FRIDAY, 'Sexta-feira'),
        (SATURDAY, 'Sábado'),
        (SUNDAY, 'Domingo'),
        (HOLIDAYS, 'Feriados'),
    )
    laboratory = models.ForeignKey(Laboratory, null=False, blank=False)
    week_day = models.IntegerField(null=False, choices=DAYS_OF_THE_WEEK)
    is_open = models.BooleanField(default=True)
    opens_at = models.TimeField(null=True, blank=True)
    closes_at = models.TimeField(null=True, blank=True)

    def __str__(self):
        return "%s: %s %s" % (self.id, self.laboratory.description, self.week_day)


class LaboratoryCollectionTime(TimeStampedModel):
    MONDAY = 1
    TUESDAY = 2
    WEDNESDAY = 3
    THURSDAY = 4
    FRIDAY = 5
    SATURDAY = 6
    SUNDAY = 7
    HOLIDAYS = 8

    DAYS_OF_THE_WEEK = (
        (MONDAY, 'Segunda-feira'),
        (TUESDAY, 'Terça-feira'),
        (WEDNESDAY, 'Quarta-feira'),
        (THURSDAY, 'Quinta-feira'),
        (FRIDAY, 'Sexta-feira'),
        (SATURDAY, 'Sábado'),
        (SUNDAY, 'Domingo'),
        (HOLIDAYS, 'Feriados'),
    )
    laboratory = models.ForeignKey(Laboratory, null=False, blank=False)
    week_day = models.IntegerField(null=False, choices=DAYS_OF_THE_WEEK)
    is_open = models.BooleanField(default=True)
    opens_at = models.TimeField(null=True, blank=True)
    closes_at = models.TimeField(null=True, blank=True)

    def __str__(self):
        return "%s: %s %s" % (self.id, self.laboratory.description, self.week_day)


class Patient(TimeStampedModel):
    MALE = 'M'
    FEMALE = 'F'
    GENDER_CHOICES = (
        (MALE, 'Masculino'),
        (FEMALE, 'Feminino'),
    )

    user = models.OneToOneField(settings.AUTH_USER_MODEL, primary_key=True, on_delete=models.CASCADE)
    preferred_laboratories = models.ManyToManyField(Laboratory, null=True, blank=True)
    id_device = models.TextField(null=True, blank=True)
    full_name = models.TextField(null=False, blank=False)
    token = models.TextField(null=True, blank=True)
    phone = models.BigIntegerField(null=True, blank=True)
    gender = models.CharField(
        max_length=1,
        choices=GENDER_CHOICES,
        null=False
    )
    birth_date = models.DateField(null=True, blank=True)
    picture_id_back = models.ImageField(upload_to=utils.user_data_path, null=True, blank=True)
    picture_id_front = models.ImageField(upload_to=utils.user_data_path, null=True, blank=True)
    selfie = models.ImageField(upload_to=utils.user_data_path, null=True, blank=True)
    picture_id_back_uploadcare = models.ImageField(upload_to=utils.user_data_path, null=True, blank=True)
    picture_id_front_uploadcare = models.ImageField(upload_to=utils.user_data_path, null=True, blank=True)
    selfie_uploadcare = models.ImageField(upload_to=utils.user_data_path, null=True, blank=True)
    is_confirmed = models.BooleanField(null=False, default=False)

    hash = models.CharField(max_length=32, null=True, blank=True, unique=True)

    preferred_laboratory_id = None

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return "{0}: {1}".format(self.user.id, self.user.email)


class InsuranceCompany(models.Model):
    name = models.CharField(max_length=200, null=False)
    description = models.TextField(null=True, blank=True)
    cnpj = models.CharField(max_length=50, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return "{0}: {1}".format(self.id, self.name)


class HealthInsurance(models.Model):
    insurance_company = models.ForeignKey(InsuranceCompany, null=True, blank=True)
    laboratories = models.ManyToManyField(Laboratory, null=True, blank=True)
    external_id = models.CharField(max_length=50, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    cnpj = models.CharField(max_length=50, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['external_id']

    def __str__(self):
        return "{0}: {1}".format(self.id, self.external_id)


class HealthInsurancePlan(models.Model):
    health_insurance = models.ForeignKey(HealthInsurance, null=False, blank=False)
    plan_code = models.CharField(max_length=250, null=False, blank=False)

    class Meta:
        ordering = ['plan_code']

    def __str__(self):
        return "{0}: {1}".format(self.id, self.plan_code)


class RejectionReason(models.Model):
    REJECTED_PIECE_NO_STAMP = 'REJECTED_PIECE_NO_STAMP'
    REJECTED_PIECE_NO_CRM = 'REJECTED_PIECE_NO_CRM'
    REJECTED_PIECE_NO_SIGNATURE = 'REJECTED_PIECE_NO_SIGNATURE'
    REJECTED_PIECE_CROPPED = 'REJECTED_PIECE_CROPPED'
    REJECTED_PIECE_BAD_CALLIGRAPHY = 'REJECTED_PIECE_BAD_CALLIGRAPHY'
    REJECTED_PIECE_ERASURE = 'REJECTED_PIECE_ERASURE'
    REJECTED_PIECE_MULTIPLE_COLORS = 'REJECTED_PIECE_MULTIPLE_COLORS'
    REJECTED_PIECE_NOT_IN_INSURANCE_RULES = 'REJECTED_PIECE_NOT_IN_INSURANCE_RULES'
    REJECTED_PIECE_NOT_A_PRESCRIPTION = 'REJECTED_PIECE_NOT_A_PRESCRIPTION'
    REJECTED_PIECE_UNREADABLE_IMAGE = 'REJECTED_PIECE_UNREADABLE_IMAGE'

    REJECTED_PRESCRIPTION_PICTURES_ID_SELFIE_DONT_MATCH = 'REJECTED_PRESCRIPTION_PICTURES_ID_SELFIE_DONT_MATCH'
    REJECTED_PRESCRIPTION_INVALID_HEALTH_CARD_PIC = 'REJECTED_PRESCRIPTION_INVALID_HEALTH_CARD_PIC'
    REJECTED_PRESCRIPTION_INVALID_ID_PIC = 'REJECTED_PRESCRIPTION_INVALID_ID_PIC'
    REJECTED_PRESCRIPTION_NOT_A_PRESCRIPTION_PACKAGE = 'REJECTED_PRESCRIPTION_NOT_A_PRESCRIPTION_PACKAGE'
    REJECTED_HEALTH_INSURANCE_NOT_COVERED = 'REJECTED_HEALTH_INSURANCE_NOT_COVERED'

    REJECTED_REQUEST_EXPIRED = 'REJECTED_REQUEST_EXPIRED'

    PRESCRIPTION_REASONS = (
        REJECTED_PRESCRIPTION_PICTURES_ID_SELFIE_DONT_MATCH,
        REJECTED_PRESCRIPTION_INVALID_HEALTH_CARD_PIC,
        REJECTED_PRESCRIPTION_INVALID_ID_PIC,
        REJECTED_PRESCRIPTION_NOT_A_PRESCRIPTION_PACKAGE,
        REJECTED_HEALTH_INSURANCE_NOT_COVERED
    )

    STATUS_CHOICES = (
        (REJECTED_PIECE_NO_STAMP, 'Carimbo não está visível'),
        (REJECTED_PIECE_NO_CRM, 'CRM não está visível'),
        (REJECTED_PIECE_NO_SIGNATURE, 'Assinatura não está visível'),
        (REJECTED_PIECE_CROPPED, 'A imagem está cortada'),
        (REJECTED_PIECE_BAD_CALLIGRAPHY, 'Escrita ilegível'),
        (REJECTED_PIECE_ERASURE, 'Apresenta rasuras'),
        (REJECTED_PIECE_MULTIPLE_COLORS, 'Mais de uma cor de caneta'),
        (REJECTED_PIECE_NOT_IN_INSURANCE_RULES, 'Fora das regras do convênio'),
        (REJECTED_PIECE_NOT_A_PRESCRIPTION, 'Não é uma prescrição'),
        (REJECTED_PIECE_UNREADABLE_IMAGE, 'Imagem ilegível'),

        (REJECTED_PRESCRIPTION_PICTURES_ID_SELFIE_DONT_MATCH, 'Pessoa da selfie difere do documento'),
        (REJECTED_PRESCRIPTION_INVALID_HEALTH_CARD_PIC, 'Fotos inválidas da carteirinha'),
        (REJECTED_PRESCRIPTION_INVALID_ID_PIC, 'Fotos inválidas do documento'),
        (REJECTED_HEALTH_INSURANCE_NOT_COVERED, 'Sem cobertura do plano de saúde'),
        (REJECTED_PRESCRIPTION_NOT_A_PRESCRIPTION_PACKAGE, 'Não há um pedido médico no envio'),
        (REJECTED_REQUEST_EXPIRED, 'Prescrição expirou'),
    )

    status = models.CharField(choices=STATUS_CHOICES, default=REJECTED_PIECE_NO_STAMP, max_length=150, db_index=True)
    feedback = models.TextField(null=False, blank=False)
    instruction = models.TextField(null=False, blank=False)
    sort_order = models.IntegerField(default=0, null=False, blank=False, unique=True,)

    class Meta:
        ordering = ['sort_order']

    def __str__(self):
        return self.status


@reversion.register()
class MedicalPrescription(TimeStampedModel):
    PATIENT_REQUESTED = 'PATIENT_REQUESTED'
    EXAMS_IDENTIFIED = 'EXAMS_IDENTIFIED'
    UNREADABLE_PICTURES = 'UNREADABLE_PICTURES'
    NOT_REGISTERED_EXAMS_FOUND = 'NOT_REGISTERED_EXAMS_FOUND'
    PICTURES_ID_SELFIE_DONT_MATCH = 'PICTURES_ID_SELFIE_DONT_MATCH'
    EXAMS_ANALYZED = 'EXAMS_ANALYZED'
    REQUEST_EXPIRED = 'REQUEST_EXPIRED'
    PACKAGE_REJECTED = 'PACKAGE_REJECTED'
    PATIENT_CANCELED_BY_CALL = 'PATIENT_CANCELED_BY_CALL'
    PHONECALL_NOT_ANSWERED = 'PHONECALL_NOT_ANSWERED'
    PICTURES_HEALTHCARD_ID_DONT_MATCH = 'PICTURES_HEALTHCARD_ID_DONT_MATCH'
    INVALID_HEALDH_CARD_PICTURE = 'INVALID_HEALDH_CARD_PICTURE'
    INVALID_ID_PICTURE = 'INVALID_ID_PICTURE'
    NOT_A_PRESCRIPTION = 'NOT_A_PRESCRIPTION'
    PROCEDURES_NOT_COVERED = 'PROCEDURES_NOT_COVERED'

    STATUS_CHOICES = ((PATIENT_REQUESTED, 'Paciente submeteu pedido'),
                      (EXAMS_IDENTIFIED, 'Exames identificados'),
                      (UNREADABLE_PICTURES, 'Imagem da prescrição está ilegível'),
                      (NOT_REGISTERED_EXAMS_FOUND, 'Há exame(s) não contemplado(s) pelo Sara'),
                      (EXAMS_ANALYZED, 'Exames analizados para aprovação/reprovação'),
                      (REQUEST_EXPIRED, 'Prescrição expirou'),
                      (PICTURES_ID_SELFIE_DONT_MATCH, 'Imagens do documento e selfie não são correspondentes'),
                      (PACKAGE_REJECTED, 'Prescrição rejeitada'),
                      (PATIENT_CANCELED_BY_CALL, 'Cancelado pelo paciente por telefone'),
                      (PHONECALL_NOT_ANSWERED, 'Ligação não atendida'),
                      (PICTURES_HEALTHCARD_ID_DONT_MATCH, 'Fotos inválidas do plano'),
                      (INVALID_HEALDH_CARD_PICTURE, 'Fotos da Carteirinha do plano inválidas'),
                      (INVALID_ID_PICTURE, 'Fotos da identidate inválida'),
                      (NOT_A_PRESCRIPTION, 'Imagens da prescição ilegíveis'),
                      (PROCEDURES_NOT_COVERED, 'Procedimentos não cobertos pelo plano'),
                      )

    CANCEL_STATUS = (UNREADABLE_PICTURES,
                     NOT_REGISTERED_EXAMS_FOUND,
                     REQUEST_EXPIRED,
                     PICTURES_ID_SELFIE_DONT_MATCH,
                     PACKAGE_REJECTED,
                     PATIENT_CANCELED_BY_CALL,
                     PHONECALL_NOT_ANSWERED,
                     PICTURES_HEALTHCARD_ID_DONT_MATCH,
                     INVALID_HEALDH_CARD_PICTURE,
                     INVALID_ID_PICTURE,
                     NOT_A_PRESCRIPTION,
                     PROCEDURES_NOT_COVERED
                     )

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    insurance_company = models.ForeignKey(InsuranceCompany, null=True, blank=True)
    health_insurance = models.ForeignKey(HealthInsurance, null=True, blank=True)
    health_insurance_plan = models.ForeignKey(HealthInsurancePlan, null=True, blank=True)
    status = models.CharField(choices=STATUS_CHOICES, default=PATIENT_REQUESTED, max_length=150, db_index=True)
    selfie_id_matches = models.BooleanField(default=False)
    doctor_name = models.CharField(max_length=250, null=True, blank=True)
    additional_info = models.TextField(null=True, blank=True)
    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True)
    period_info = models.TextField(null=True, blank=True)
    laboratory_brands = models.CommaSeparatedIntegerField(null=True, blank=True, max_length=1000)

    picture_insurance_card_front_uploadcare = models.ImageField(upload_to=utils.prescription_path, null=True, blank=True)
    picture_insurance_card_back_uploadcare = models.ImageField(upload_to=utils.prescription_path, null=True, blank=True)
    picture_prescription_uploadcare = models.ImageField(upload_to=utils.prescription_path, null=True, blank=True)
    picture_id_back_uploadcare = models.ImageField(upload_to=utils.prescription_path, null=True, blank=True)
    picture_id_front_uploadcare = models.ImageField(upload_to=utils.prescription_path, null=True, blank=True)
    selfie_uploadcare = models.ImageField(upload_to=utils.prescription_path, null=True, blank=True)

    # Fields kept due to retro compatibility with old app versions:
    picture_insurance_card_front = models.ImageField(upload_to=utils.prescription_path, null=True, blank=True)
    picture_insurance_card_back = models.ImageField(upload_to=utils.prescription_path, null=True, blank=True)
    picture_prescription = models.ImageField(upload_to=utils.prescription_path, null=True, blank=True)
    picture_id_back = models.ImageField(upload_to=utils.prescription_path, null=True, blank=True)
    picture_id_front = models.ImageField(upload_to=utils.prescription_path, null=True, blank=True)
    selfie = models.ImageField(upload_to=utils.prescription_path, null=True, blank=True)

    # Also retro compatibility, these fields now belong to entity PrescriptionPiece:
    annotations = models.TextField(null=True, blank=True)
    doctor_crm = models.CharField(max_length=50, null=True, blank=True)
    exams_not_registered = models.TextField(null=True, blank=True)
    expiration_date = models.DateTimeField(null=True, blank=True, db_index=True)
    prescription_issued_at = models.DateTimeField(null=True, blank=True)
    rejection_reasons = models.ManyToManyField(RejectionReason, null=True, blank=True)
    preferred_laboratory = models.ForeignKey(Laboratory, null=True, blank=True)
    preferred_date_to_schedule = models.DateTimeField(null=True, blank=True)

    # Used by Signals activities:
    insurance_company_id = None
    __original_status = None
    __original_exams_not_registered = None
    __original_expiration_date = None

    class Meta:
        ordering = ['-created']

        index_together = (
            ('created', 'status'),
        )

    def __str__(self):
        return "{0}: {1}".format(self.id, self.patient.user.email)

    def __init__(self, *args, **kwargs):
        super(MedicalPrescription, self).__init__(*args, **kwargs)
        self.__original_status = self.status
        self.__original_exams_not_registered = self.exams_not_registered
        self.__original_expiration_date = self.expiration_date


class PrescriptionPiece(TimeStampedModel):
    PIECE_CREATED = 'PIECE_CREATED'
    REQUEST_EXPIRED = 'REQUEST_EXPIRED'
    PIECE_REJECTED = 'PIECE_REJECTED'

    STATUS_CHOICES = ((PIECE_CREATED, 'Pedaço de prescrição criado'),
                      (REQUEST_EXPIRED, 'Pedaço de prescrição expirou'),
                      (PIECE_REJECTED, 'Pedaço de prescrição rejeitada'),
                      )

    prescription = models.ForeignKey(MedicalPrescription, on_delete=models.CASCADE, related_name='pieces')
    picture = models.ImageField(upload_to=utils.prescription_path_for_prescription_piece, null=True, blank=True)
    annotations = models.TextField(null=True, blank=True)
    doctor_crm = models.CharField(max_length=50, null=True, blank=True)
    exams_not_registered = models.TextField(null=True, blank=True)
    expiration_date = models.DateTimeField(null=True, blank=True, db_index=True)
    prescription_issued_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(choices=STATUS_CHOICES, default=PIECE_CREATED, max_length=150, db_index=True)
    rejection_reasons = models.ManyToManyField(RejectionReason, null=True, blank=True)

    # Used by Signals activities:
    __original_status = None
    __original_exams_not_registered = None
    __original_expiration_date = None

    class Meta:
        ordering = ['pk']

    def __str__(self):
        return "{0}: {1}".format(self.id, self.prescription)

    def __init__(self, *args, **kwargs):
        super(PrescriptionPiece, self).__init__(*args, **kwargs)
        self.__original_status = self.status
        self.__original_exams_not_registered = self.exams_not_registered
        self.__original_expiration_date = self.expiration_date


@reversion.register()
class ScheduledExam(TimeStampedModel):
    EXAM_IDENTIFIED = 'EXAM_IDENTIFIED'

    ELIGIBLE_PATIENT = 'ELIGIBLE_PATIENT'
    NOT_ELIGIBLE_PATIENT_DUE_TO_AGE_OR_GENDER = 'NOT_ELIGIBLE_PATIENT_DUE_TO_AGE_OR_GENDER'
    PROCEDURES_NOT_COVERED = 'PROCEDURES_NOT_COVERED'
    ALTERNATIVE_LAB_GIVEN = 'ALTERNATIVE_LAB_GIVEN'

    PHONE_CALL_SCHEDULED = 'PHONE_CALL_SCHEDULED'
    EXAM_TIME_SCHEDULED = 'EXAM_TIME_SCHEDULED'
    PHONE_CALL_NOT_ANSWERED = 'PHONE_CALL_NOT_ANSWERED'
    PATIENT_CANCELED_BY_CALL = 'PATIENT_CANCELED_BY_CALL'
    PATIENT_CANCELED = 'PATIENT_CANCELED'
    EXAM_MISSED = 'EXAM_MISSED'

    LAB_RECORD_OPEN = 'LAB_RECORD_OPEN'
    PROCEDURES_EXECUTED = 'PROCEDURES_EXECUTED'
    LAB_RECORD_CANCELED = 'LAB_RECORD_CANCELED'
    RESULTS_DELAYED = 'RESULTS_DELAYED'
    RESULTS_RECEIVED = 'RESULTS_RECEIVED'

    EXAM_EXPIRED = 'EXAM_EXPIRED'

    ATTENDED_SCHEDULED_EXAMS = (
        PROCEDURES_EXECUTED,
        RESULTS_DELAYED,
        RESULTS_RECEIVED
    )

    STATUS_CHOICES = (
        (EXAM_IDENTIFIED, 'Exame identificado'),
        (ELIGIBLE_PATIENT, 'Paciente elegível'),
        (NOT_ELIGIBLE_PATIENT_DUE_TO_AGE_OR_GENDER, 'Paciente não elegível por questão de idade ou sexo'),
        (PROCEDURES_NOT_COVERED, 'Exame não cobertos pelo Plano ou laboratório não executa o exame'),
        (ALTERNATIVE_LAB_GIVEN, 'Laboratórios alternativos sugeridos'),
        (PHONE_CALL_SCHEDULED, 'Ligação telefônica agendada'),
        (EXAM_TIME_SCHEDULED, 'Paciente agendou horário para o exame'),
        (PHONE_CALL_NOT_ANSWERED, 'Ligação telefônica não atendida'),
        (PATIENT_CANCELED_BY_CALL, 'Paciente cancelou o exame pela ligação telefônica'),
        (PATIENT_CANCELED, 'Paciente Cancelou'),
        (EXAM_MISSED, 'Exame estava agendado mas o paciente não compareceu'),
        (LAB_RECORD_OPEN, 'Pré Cadastro criado no laboratório'),
        (PROCEDURES_EXECUTED, 'Procedimento executado'),
        (LAB_RECORD_CANCELED, 'Ficha no laboratório cancelada'),
        (RESULTS_DELAYED,'Resultados do exame estão atrasados'),
        (RESULTS_RECEIVED, 'Resultado do exame está pronto'),
        (EXAM_EXPIRED, 'Exame expirado')
    )
    # TODO: Put this as 'null=False, blank=False' after all changes regarding this feature is done here and in Concierge
    prescription_piece = models.ForeignKey(PrescriptionPiece, on_delete=models.CASCADE, related_name='scheduled_exams',
                                           null=True, blank=True)
    exam = models.ForeignKey(Exam, null=False, blank=False)
    laboratory = models.ForeignKey(Laboratory, null=True, blank=True)
    suggested_labs = models.ManyToManyField(Laboratory, blank=True, related_name="suggested_labs")
    status = models.CharField(choices=STATUS_CHOICES, default=EXAM_IDENTIFIED, max_length=150, db_index=True)
    scheduled_time = models.DateTimeField(null=True, blank=True)
    procedure_average_duration = models.IntegerField(null=True, blank=True)
    confirmation = models.BooleanField(default=False)
    expiration_date = models.DateTimeField(null=True, blank=True)
    plan_product_code = models.CharField(max_length=50, null=True, blank=True)
    annotations = models.TextField(null=True, blank=True)
    results_expected_at = models.DateField(null=True, blank=True)
    lab_file_code = models.CharField(max_length=250, null=True, blank=True, db_index=True)
    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True)
    is_grouped = models.BooleanField(default=False)
    results_arrived_at = models.DateTimeField(null=True, blank=True, default=None, db_index=True)
    zendesk_adf_ticket = models.ForeignKey(ZendeskASFTicket, null=True, blank=True, db_index=True)

    # Old field kept due to retro compatibility with old app versions,
    # this FK relationship was replaced by 'prescription_piece':
    prescription = models.ForeignKey(MedicalPrescription, on_delete=models.CASCADE, null=False, blank=False)

    # Used by Signals activities:
    exams_id = None
    laboratory_id = None
    suggested_labs_id = None
    __original_scheduled_time = None
    __original_status = None
    __original_results_expected_at = None

    class Meta:
        ordering = ['-created']

        index_together = (
            ('prescription', 'exam'),
            ('prescription', 'status'),
            ('scheduled_time', 'status'),
            ('exam', 'status'),
            ('laboratory', 'prescription'),
        )

    def __str__(self):
        return "{0}: {1} - {2}".format(self.id, self.prescription or self.prescription_piece, self.exam)

    def __init__(self, *args, **kwargs):
        super(ScheduledExam, self).__init__(*args, **kwargs)
        self.__original_scheduled_time = self.scheduled_time
        self.__original_status = self.status
        self.__original_results_expected_at = self.results_expected_at


IN_PRESCRIPTION = [MedicalPrescription.PATIENT_REQUESTED]
IN_ELIGIBLE = [MedicalPrescription.EXAMS_IDENTIFIED]
IN_SCHEDULE = [ScheduledExam.EXAM_IDENTIFIED]
IN_PREREGISTER = [ScheduledExam.EXAM_TIME_SCHEDULED]
IN_CANCELED = [ScheduledExam.PATIENT_CANCELED]


@reversion.register()
class ScheduledExamPhoneCall(TimeStampedModel):

    ATTEMPT_INCR_MINUTES = [0, 10, 20, 30, 60]

    scheduled_exam = models.OneToOneField(ScheduledExam, on_delete=models.CASCADE, null=False)
    phone = models.BigIntegerField(null=False, blank=False)
    call_time = models.DateTimeField(null=False, blank=False)
    is_canceled = models.BooleanField(default=False)
    attempt = models.SmallIntegerField(default=0)

    __original_is_canceled = None

    def __str__(self):
        return "{}: {} attempt:{} ".format(self.id, self.scheduled_exam, self.attempt)

    def __init__(self, *args, **kwargs):
        super(ScheduledExamPhoneCall, self).__init__(*args, **kwargs)
        self.__original_is_canceled = self.is_canceled


class PreparationStep(models.Model):
    exam = models.ForeignKey(Exam, null=False, blank=False)
    start_preparation_in_hours = models.PositiveSmallIntegerField(default=0, null=False, blank=False)
    laboratory = models.ForeignKey(Laboratory, null=False, blank=False)
    title = models.TextField(null=True, blank=True)
    description = models.TextField(null=False, blank=False)
    recent_description = models.TextField(null=True, blank=True)
    is_mandatory = models.BooleanField(default=False)

    class Meta:
        index_together = (
            ('exam', 'laboratory'),
        )

    def __str__(self):
        return "{0}: {1} - Exam: {2} - Lab: {3}."\
            .format(self.id, self.title, self.exam.name, self.laboratory.description)


class ExamResult(models.Model):
    scheduled_exam = models.ForeignKey(ScheduledExam, null=False, blank=False, on_delete=models.CASCADE)
    file = models.FileField(upload_to=utils.exam_result_path, null=True, blank=True)

    def __str__(self):
        return "{0}: {1}".format(self.id, self.scheduled_exam)


class ExamResultDetail(models.Model):
    exam_result = models.ForeignKey(ExamResult, null=False, blank=False, on_delete=models.CASCADE)
    title = models.CharField(max_length=150, null=True, blank=True)
    description = models.CharField(max_length=250, null=False, blank=False)
    result = models.CharField(max_length=150, null=False, blank=False)
    reference_values = models.CharField(max_length=150, null=False, blank=False)

    def __str__(self):
        return "{0}: {1}".format(self.id, self.description)


class ExamExpiration(models.Model):
    exam = models.ForeignKey(Exam, null=False, blank=False)
    insurance_company = models.ForeignKey(InsuranceCompany, null=False, blank=False)
    expiration_in_days = models.IntegerField(null=False, blank=False)

    def __str__(self):
        return "{0}: {1} days. Exam: {2} - Insurance: {3}".format(self.id, self.expiration_in_days, self.exam,
                                                                  self.insurance_company)


class RecoverPassword(models.Model):
    token = models.CharField(max_length=32, null=False, unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=False)
    expiration_date = models.DateTimeField(null=False, blank=False)
    is_used = models.BooleanField(default=False)

    class Meta:
        index_together = (
            ('user', 'is_used'),
        )

    def __str__(self):
        return "{0}: {1} - {2}".format(self.id, self.user.first_name, self.token)


class Holiday(models.Model):
    country = models.CharField(max_length=90, null=False, blank=False)
    state = models.CharField(max_length=90, null=True, blank=True)
    city = models.CharField(max_length=90, null=True, blank=True)
    description = models.CharField(max_length=150, null=True, blank=True)
    date = models.DateField()

    class Meta:
        index_together = (
            ('country', 'state', 'city'),
        )

    def __str__(self):
        return "{0} {1} {2}: {3}".format(
            self.country,
            self.state if self.state else '',
            self.city if self.city else '',
            self.date,
        )
