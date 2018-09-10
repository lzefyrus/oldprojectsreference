# encode: utf-8

import datetime

import django_filters
import pytz
import reversion
from django.core.exceptions import ObjectDoesNotExist
from django.core.files import File
from django.db.models import Q
from django.http import Http404
from rest_framework.decorators import detail_route, list_route
from rest_framework.filters import DjangoFilterBackend
from rest_framework.response import Response
from rest_framework import mixins, status, viewsets
from rest_framework.parsers import FormParser, MultiPartParser
from reversion.views import RevisionMixin

from .filters import *
from .serializers import *

from domain.utils import RequestLogViewMixin, grouped_exams_by_lab_date_keygen


class OperatorViewSet(RequestLogViewMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):

    def get_serializer_class(self):
        if self.request.version in ('v3', 'v4', 'v5'):
            return OperatorInfoSerializer

    def get_queryset(self):
        return Operator.objects.filter(pk=int(self.kwargs['pk']))

    @list_route()
    def current(self, request, *args, **kwargs):
        """
        Retrieves current operator instance.
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        try:
            operator = Operator.objects.get(pk=request.user.operator)
            return Response(OperatorInfoSerializer(operator).data)
        except ObjectDoesNotExist:
            raise Http404()


class PatientRetrieveViewSet(RequestLogViewMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = domain_models.Patient.objects.all()

    def retrieve(self, request, *args, **kwargs):
        """
        Overwrites retrieve method.
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        try:
            patient = domain_models.Patient.objects.get(pk=kwargs['pk'])
            return Response(PatientRetrieveSerializer(patient, context={"request": request}).data)
        except ObjectDoesNotExist as exc:
            return Response({"detail": str(exc),
                             "status_code": status.HTTP_404_NOT_FOUND},
                            status=status.HTTP_404_NOT_FOUND)


class MedicalPrescriptionViewSet(RequestLogViewMixin, RevisionMixin, mixins.RetrieveModelMixin,
                                 mixins.UpdateModelMixin, viewsets.GenericViewSet):
    queryset = domain_models.MedicalPrescription.objects.all()

    def get_serializer_class(self):
        if self.request.version in ('v3', 'v4', 'v5'):
            if self.action == 'retrieve':
                return PrescriptionSerializer

            if self.action in ('partial_update', 'update'):
                return PrescriptionUpdateSerializer

    def update(self, request, *args, **kwargs):
        with reversion.create_revision():
            try:
                partial = kwargs.pop('partial', False)
                instance = self.get_object()
                serializer = self.get_serializer(instance, data=request.data, partial=partial)
                serializer.is_valid(raise_exception=True)

                self.perform_update(serializer)
                reversion.set_user(self.request.user)
                reversion.set_comment("Sara Concierge Backoffice")
                response = Response(PrescriptionSerializer(instance, context={"request": request}).data,
                                    status=status.HTTP_200_OK)


            except (ObjectDoesNotExist, ValueError) as exc:
                return Response({"detail": str(exc),
                                 "status_code": status.HTTP_400_BAD_REQUEST}, status=status.HTTP_400_BAD_REQUEST)
        return response

    @list_route(url_path='group/(?P<groupid>[^/.]+)')
    def group(self, request, groupid, *args, **kwargs):
        """
        Return all the exams in a group
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        try:
            d, user, lab = grouped_exams_by_lab_date_keygen(groupid, 'decode')
        except:
            return Response({"detail": "No group found",
                             "status_code": status.HTTP_404_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
        try:
            queryset = domain_models.MedicalPrescription.objects.filter(scheduledexam__scheduled_time__date=d,
                                                                        patient_id=user,
                                                                        scheduledexam__laboratory_id=lab)[0]
            serializer = PreregisterPrescriptionSerializer(queryset)

            return Response(serializer.data)

        except Exception as exc:
            return Response({"detail": str(exc),
                             "status_code": status.HTTP_400_BAD_REQUEST},
                            status=status.HTTP_400_BAD_REQUEST)

    @detail_route(url_path="scheduled-exams")
    def scheduled_exams(self, request, *args, **kwargs):
        """
        Retrieves all scheduled exams within a medical prescription.
        TODO: check if concierge still using this
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        prescription = self.get_object()
        scheduled_exams = domain_models.ScheduledExam.objects.filter(prescription=prescription.id)\
            .exclude(status=domain_models.ScheduledExam.EXAM_EXPIRED)

        if not len(scheduled_exams):
            raise Http404()
        with reversion.create_revision():
            scheduled_exams = ScheduledExamByPrescriptionSerializer(scheduled_exams, many=True,
                                                                    context={"request": request}).data
            reversion.set_user(self.request.user)
            reversion.set_comment("Sara Concierge Backoffice MP SC")
        return Response({"prescription": ScheduledExamPrescriptionSerializer(prescription).data,
                         "scheduled_exams": scheduled_exams})





class InsuranceCompanyFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(name="name", lookup_expr='icontains')

    class Meta:
        model = domain_models.InsuranceCompany
        fields = '__all__'


class InsuranceCompanyViewSet(RequestLogViewMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = domain_models.InsuranceCompany.objects.filter(is_active=True)
    filter_backends = (DjangoFilterBackend,)
    filter_class = InsuranceCompanyFilter

    def get_serializer_class(self):
        if self.request.version in ('v3', 'v4', 'v5'):
            return InsuranceCompanySerializer


class ExamViewSet(RequestLogViewMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = domain_models.Exam.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filter_class = ExamFilter

    def get_serializer_class(self):
        if self.request.version in ('v3', 'v4', 'v5'):
            return ExamSerializer


class LaboratoryViewSet(RequestLogViewMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = domain_models.Laboratory.objects.filter(is_active=True, brand__is_active=True)
    filter_backends = (DjangoFilterBackend,)
    filter_class = LaboratoryFilter

    def get_serializer_class(self):
        if self.request.version in ('v3', 'v4', 'v5'):
            return LaboratorySerializer

    def filter_queryset(self, queryset):
        brand_name = self.request.query_params.get('brand__name', '')
        street = self.request.query_params.get('street', '')
        if not brand_name and not street:
            return domain_models.Laboratory.objects.filter(is_active=True, brand__is_active=True)

        if not brand_name:
            return domain_models.Laboratory.objects.filter(Q(street__icontains=street))

        if not street:
            return domain_models.Laboratory.objects.filter(Q(brand__name__icontains=brand_name))


class DashboardViewSet(viewsets.ViewSet):

    def list(self, request):
        prescription_total, prescription_oldest_today = self._get_today_stats(domain_models.IN_PRESCRIPTION)
        eligible_total, eligible_oldest_today = self._get_today_stats(domain_models.IN_ELIGIBLE)
        preregister_total, preregister_oldest_today = self._get_today_stats(domain_models.IN_PREREGISTER)
        canceled_total, canceled_oldest_today = self._get_today_stats(domain_models.IN_CANCELED)

        serializer = DashboardSerializer({
            'prescription_total': prescription_total,
            'prescription_oldest_today': prescription_oldest_today,
            'eligible_total': eligible_total,
            'eligible_oldest_today': eligible_oldest_today,
            'preregister_total': preregister_total,
            'preregister_oldest_today': preregister_oldest_today,
            'canceled_total': canceled_total,
            'canceled_oldest_today': canceled_oldest_today
        })

        return Response(serializer.data)

    @staticmethod
    def _get_today_stats(in_status):
        total = domain_models.MedicalPrescription.objects.filter(
            created__gt=datetime.datetime.combine(datetime.datetime.today(), datetime.time(0)),
            status__in=in_status).count()
        oldest_today = domain_models.MedicalPrescription.objects.filter(
            created__gt=datetime.datetime.combine(datetime.datetime.today(), datetime.time(0)),
            status__in=in_status).order_by('-id')[:1]

        today_age = None

        if oldest_today:
            today_delta = datetime.datetime.now(pytz.timezone('America/Sao_Paulo')) - oldest_today[0].modified
            (today_age, _) = divmod(today_delta.days * 86400 + today_delta.seconds, 60)

        return total, today_age


class ScheduledExamViewSet(RequestLogViewMixin,
                           RevisionMixin,
                           mixins.RetrieveModelMixin,
                           mixins.UpdateModelMixin,
                           viewsets.GenericViewSet):
    queryset = domain_models.ScheduledExam.objects.all().exclude(status=domain_models.ScheduledExam.EXAM_EXPIRED)

    def get_serializer_class(self):
        if self.request.version in ('v3', 'v4', 'v5'):
            return ScheduledExamSerializer

    def update(self, request, *args, **kwargs):
        try:
            with reversion.create_revision():
                response = super(ScheduledExamViewSet, self).update(request, *args, **kwargs, context={"request": request})
                reversion.set_user(self.request.user)
                reversion.set_comment("Sara Concierge Backoffice Schedule")
        except ObjectDoesNotExist as exc:
            return Response({"detail": str(exc),
                             "status_code": status.HTTP_400_BAD_REQUEST}, status=status.HTTP_400_BAD_REQUEST)
        return response

    @detail_route(methods=['post', 'get'], parser_classes=(FormParser, MultiPartParser,))
    def results(self, request, *args, **kwargs):
        if request.method in ['POST']:
            result_file = request.FILES.get('result_file')
            if not result_file:
                return Response({"detail": "File not found inside request",
                                 "status_code": status.HTTP_400_BAD_REQUEST}, status=status.HTTP_400_BAD_REQUEST)

            scheduled_exam = self.get_object()

            try:
                result = domain_models.ExamResult(scheduled_exam=scheduled_exam, file=File(result_file))
                result.save()
                return Response(status=200)

            except:
                return Response({"detail": "Invalid file",
                                 "status_code": status.HTTP_400_BAD_REQUEST}, status=status.HTTP_400_BAD_REQUEST)

    @list_route(methods=['put', 'patch'])
    def status(self, request, *args, **kwargs):
        try:
            for item in request.data.get("exams_data"):
                serializer = StatusScheduledExamSerializer(data=item, context={"request": request})
                serializer.is_valid(raise_exception=True)

                request_data = serializer.data

                try:
                    exams = domain_models.ScheduledExam.objects.filter(pk__in=request_data["scheduled_exam_ids"])
                    if not exams:
                        return Response({"detail": "No exams found",
                                         "status_code": status.HTTP_404_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)

                    for exam in exams:
                        upd = True
                        try:
                            if exam.scheduledexamphonecall.attempt <= 4 and request_data["status"] == domain_models.ScheduledExam.PHONE_CALL_NOT_ANSWERED:
                                # update phonecalltime on schedule
                                upd = False
                                with reversion.create_revision():
                                    instance = exam.scheduledexamphonecall.attempt
                                    newtime = instance.call_time + \
                                              datetime.timedelta(minutes=instance.ATTEMPT_INCR_MINUTES(instance.attempt))
                                    instance.call_time = newtime
                                    instance.attempt = instance.attempt + 1
                                    instance.save()
                                    reversion.set_user(self.request.user)
                                    reversion.set_comment("Sara Concierge Backoffice Call Attempt: #{}".format(instance.attempt))
                                if instance.attempt >= 4:
                                    upd = True
                        except Exception as e:
                            print('Not Scheduled Exam Call')

                        finally:
                            if upd is True:
                                exam.status = request_data["status"]
                                exam.modified_by = self.request.user
                                exam.save()

                except Exception as exc:
                    return Response({"detail": str(exc),
                                     "status_code": status.HTTP_400_BAD_REQUEST},
                                    status=status.HTTP_400_BAD_REQUEST)
            return Response(status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": str(e),
                             "status_code": status.HTTP_400_BAD_REQUEST}, status=status.HTTP_400_BAD_REQUEST)

    @list_route(methods=['put', 'patch'])
    def eligibility(self, request, *args, **kwargs):

        serializer = EligibilityScheduledExamSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        try:
            serializer.eligibility_update(request.data, self.request.user)

            return Response(status=status.HTTP_200_OK)
        except Exception as exc:
            return Response({"detail": str(exc),
                             "status_code": status.HTTP_400_BAD_REQUEST},
                            status=status.HTTP_400_BAD_REQUEST)

    @list_route(methods=['put', 'patch'])
    def call(self, request, *args, **kwargs):
        serializer = CallScheduledExamSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        try:
            serializer.call_update(request.data, self.request.user)
            return Response(status=status.HTTP_200_OK)
        except (ObjectDoesNotExist, ValueError) as exc:
            return Response({"detail": str(exc),
                             "status_code": status.HTTP_400_BAD_REQUEST},
                            status=status.HTTP_400_BAD_REQUEST)

    @list_route(url_path='group/(?P<groupid>[^/.]+)')
    def group(self, request, groupid, *args, **kwargs):
        """
        Return all the exams in a group
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        try:
            d, user, lab = grouped_exams_by_lab_date_keygen(groupid, 'decode')
        except:
            return Response({"detail": "No group found",
                             "status_code": status.HTTP_404_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)

        try:
            exams = domain_models.ScheduledExam.objects.filter(scheduled_time__date=d,
                                                               prescription__patient_id=user,
                                                               laboratory_id=lab,
                                                               status=domain_models.ScheduledExam.EXAM_TIME_SCHEDULED).order_by('scheduled_time')
            serializer = GroupStatusScheduledExamSerializer(exams, many=True)

            return Response(serializer.data)

        except Exception as exc:
            return Response({"detail": str(exc),
                             "status_code": status.HTTP_400_BAD_REQUEST},
                            status=status.HTTP_400_BAD_REQUEST)

    @list_route(methods=['put', 'patch'])
    def preregister(self, request, *args, **kwargs):

        serializer = PreregisterScheduledExamSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        try:
            serializer.preregister_update(request.data, self.request.user)

            return Response(status=status.HTTP_200_OK)
        except Exception as exc:
            return Response({"detail": str(exc),
                             "status_code": status.HTTP_400_BAD_REQUEST},
                            status=status.HTTP_400_BAD_REQUEST)


class ExamPhoneCallViewSet(RequestLogViewMixin,
                           mixins.ListModelMixin,
                           mixins.RetrieveModelMixin,
                           viewsets.GenericViewSet):
    queryset = domain_models.ScheduledExamPhoneCall.objects.all()

    def get_serializer_class(self):
        if self.request.version in ('v3', 'v4', 'v5'):
            return ScheduledExamPhoneCallSerializer

# TODO: Tests missing for these two views
class HealthInsuranceViewSet(RequestLogViewMixin,
                             mixins.ListModelMixin,
                             viewsets.GenericViewSet):
    queryset = domain_models.HealthInsurance.objects.filter(is_active=True).all()

    def get_serializer_class(self):
        if self.request.version in ('v3', 'v4', 'v5'):
            return HealthInsuranceSerializer

    @detail_route(url_path="plans")
    def plans(self, request, *args, **kwargs):
        """
        Retrieves health insurance plans from a given health insurance.
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        health_insurance = self.get_object()
        plans = domain_models.HealthInsurancePlan.objects.filter(health_insurance=health_insurance).all()
        if not len(plans):
            raise Http404()

        return Response({"insurance_health_plans": HealthInsurancePlanSerializer(plans, many=True).data})


class HealthInsurancePlanViewSet(RequestLogViewMixin,
                                 mixins.ListModelMixin,
                                 viewsets.GenericViewSet):
    queryset = domain_models.HealthInsurancePlan.objects.all()

    def get_serializer_class(self):
        if self.request.version in ('v3', 'v4', 'v5'):
            return HealthInsurancePlanSerializer


class RejectionReasonListViewSet(RequestLogViewMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = domain_models.RejectionReason.objects.all()
    serializer_class = RejectionReasonSerializer


class PreparationStepViewSet(RequestLogViewMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    queryset = domain_models.PreparationStep.objects.all()
    serializer_class = PreparationStepSerializer