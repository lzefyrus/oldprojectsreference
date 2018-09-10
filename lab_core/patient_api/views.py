# encode: utf-8
import os
import json
import logging
import requests

from itertools import chain
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.core.files.base import ContentFile
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404, HttpResponse
from django.db.models import Q
from rest_framework.decorators import api_view
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import authentication_classes, detail_route, list_route, permission_classes
from rest_framework.response import Response
from reversion.views import RevisionMixin

from domain.exceptions import InvalidRequestError
from domain.maps import Maps
from domain.serializers import ObtainExpirableTokenSerializer
from domain.tasks import send_push_notification
from domain.utils import RequestLogViewMixin, authenticate_user, authenticate_user_by_prescription, \
    remove_milliseconds_from_timestamp
from patient_api.serializers.v3 import *
from patient_api.serializers.v4 import *
from patient_api.serializers.v5 import *
from patient_api.utils import get_address_component
from patient_api.validators import validate_geolocation_query_string

log = logging.getLogger(__name__)


class LaboratoryViewSet(RequestLogViewMixin,
                        mixins.ListModelMixin,
                        mixins.RetrieveModelMixin,
                        viewsets.GenericViewSet):
    """
    A viewset for viewing Laboratory instances.
    """
    serializer_class = LaboratorySerializer
    pagination_class = None

    def get_serializer_class(self):
        if self.request.version in ('v3', 'v4', 'v5'):
            return LaboratorySerializer

    def list(self, request, *args, **kwargs):
        """
        Overwrites list method in order to handle InvalidRequestError.
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        try:
            # return super(LaboratoryViewSet, self).list(request, *args, **kwargs)
            queryset = self.filter_queryset(self.get_queryset())

            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, many=True)
            return Response({"results": serializer.data})
        except InvalidRequestError as exc:
            return Response({"detail": "{0}: {1}".format(exc.message, exc.errors),
                             "status_code": status.HTTP_400_BAD_REQUEST},
                            status=status.HTTP_400_BAD_REQUEST)

    def get_queryset(self):
        """
        Returns queryset dynamically according to action.
        If it's not defined, returns default.
        :return:
        """
        try:
            return getattr(self, "queryset_{0}".format(self.action))
        except AttributeError:
            return self.queryset_default

    @property
    def queryset_default(self):
        """
        Returns queryset for default action.
        :return:
        """
        return Laboratory.objects.filter(is_active=True)

    @property
    @validate_geolocation_query_string
    def queryset_list(self):
        """
        Returns queryset for list action.
        :return:
        """
        query_string = self.request.query_params

        if not query_string:
            return Laboratory.objects.filter(is_active=True)

        # Geolocation
        address = getattr(self, "address", None)
        if address:
            # an address has been given
            maps = Maps()
            geocode = maps.client.geocode(address)
            location = geocode[0]['geometry']['location']
            patient_location = Point(location['lng'], location['lat'])
        else:
            # a lat/lng point has been given
            patient_location = Point(self.lng, self.lat)

        # Radius
        desired_radius = {'m': self.radius}

        query_filter = {
            'is_active': True,
            'point__distance_lte': (patient_location, D(**desired_radius)),
        }

        # Brand
        if self.brand:
            if type(self.brand) is int:
                query_filter.update({'brand': self.brand})
            else:  # list
                query_filter.update({'brand__in': self.brand})

        return Laboratory.objects.filter(**query_filter) \
                   .distance(patient_location) \
                   .order_by('distance')[:settings.LABORATORY_LIST_LIMIT]


class LaboratoryBrandViewSet(RequestLogViewMixin,
                             viewsets.ReadOnlyModelViewSet):
    """
    A viewset for viewing Laboratory Brand instances.
    """
    queryset = LaboratoryBrand.objects.filter(is_active=True)

    def get_serializer_class(self):
        if self.request.version in ('v3', 'v4', 'v5'):
            return LaboratoryBrandSerializer

    @detail_route()
    def laboratories(self, request, *args, **kwargs):
        """
        Retrieves laboratories by brand.
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        brand = self.get_object()
        laboratories = Laboratory.objects.filter(is_active=True, brand=brand.id)
        if not len(laboratories):
            raise Http404()

        return Response({"brand": LaboratoryBrandSerializer(brand).data,
                         "laboratories": LaboratorySerializer(laboratories, many=True).data})


class ExamViewSet(RequestLogViewMixin,
                  viewsets.ReadOnlyModelViewSet):
    """
    A viewset for viewing Exam instances.
    """
    queryset = Exam.objects.all()

    def get_serializer_class(self):
        if self.request.version in ('v3', 'v4', 'v5'):
            return ExamSerializer


class PatientViewSet(RequestLogViewMixin,
                     mixins.CreateModelMixin,
                     mixins.UpdateModelMixin,
                     mixins.RetrieveModelMixin,
                     mixins.ListModelMixin,
                     mixins.DestroyModelMixin,
                     viewsets.GenericViewSet):
    """
    A viewset for viewing and editing Patient instances.
    """
    queryset = Patient.objects.all()
    permission_classes_by_action = {
        'confirmation': [],
        'send_confirmation': [],
        'send_push_notification': [],
    }

    def get_serializer_class(self):
        """
        Defines serializer class dynamically.
        :return:
        """
        if self.request.version in ('v3', 'v4', 'v5'):
            if self.action == 'update':
                return PatientUpdateSerializer

            if self.action == 'create':
                return PatientCreateSerializer

            return PatientSerializer

    def list(self, request, *args, **kwargs):
        """
        Overwrites list method in order to handle query string params.
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        email = request.query_params.get("email", None)
        if email:
            try:
                patient = Patient.objects.get(user__email=email)
                return Response(PatientSerializer(patient, context={"request": request}).data)

            except ObjectDoesNotExist:
                raise Http404()

        return super(PatientViewSet, self).list(request, *args, **kwargs)

    @authenticate_user
    def retrieve(self, request, *args, **kwargs):
        """
        Overwrites retrieve method in order to add annotation @authenticate_user.
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        return super(PatientViewSet, self).retrieve(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        """
        Overwrites create method in order to handle IntegrityError and ObjectDoesNotExist.
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        try:
            return super(PatientViewSet, self).create(request, context={"request": request})
        except IntegrityError:
            return Response({"detail": "This username already exists.",
                             "status_code": status.HTTP_400_BAD_REQUEST},
                            status=status.HTTP_400_BAD_REQUEST)
        except (ObjectDoesNotExist, RuntimeError) as exc:
            return Response({"detail": str(exc),
                             "status_code": status.HTTP_400_BAD_REQUEST},
                            status=status.HTTP_400_BAD_REQUEST)

    @authenticate_user
    def update(self, request, *args, **kwargs):
        """
        Overwrites update method in order to handle ObjectDoesNotExist and AuthenticationFailed.
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        try:
            return super(PatientViewSet, self).update(request, *args, **kwargs)
        except ObjectDoesNotExist as exc:
            return Response({"detail": str(exc),
                             "status_code": status.HTTP_400_BAD_REQUEST},
                            status=status.HTTP_400_BAD_REQUEST)

    @authenticate_user
    def destroy(self, request, *args, **kwargs):
        """
        Overwrites destroy method applying annotation.
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        try:
            patient = self.get_object()
            user = patient.user
            result = super(PatientViewSet, self).destroy(request, *args, **kwargs)
            user.delete()

            return result
        except ObjectDoesNotExist as exc:
            return Response({"detail": str(exc),
                             "status_code": status.HTTP_400_BAD_REQUEST},
                            status=status.HTTP_400_BAD_REQUEST)

    @detail_route()
    @authenticate_user
    def prescriptions(self, request, *args, **kwargs):
        """
        Retrieves medical prescriptions by patient.
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        patient = self.get_object()
        prescriptions = MedicalPrescription.objects.filter(patient=patient.user.id).order_by('created')
        if not len(prescriptions):
            raise Http404()

        if self.request.version == 'v4':
            prescription_serializer = MedicalPrescriptionByPatientV4Serializer
        elif self.request.version == 'v5':
            prescription_serializer = MedicalPrescriptionByPatientV5Serializer
        else:
            prescription_serializer = MedicalPrescriptionByPatientSerializer

        return Response({"patient": PatientSerializer(patient, context={"request": request}).data,
                         "prescriptions": prescription_serializer(prescriptions, many=True,
                                                                  context={"request": request}).data})

    @detail_route(url_path="preferred-labs")
    @authenticate_user
    def preferred_labs(self, request, *args, **kwargs):
        """
        Retrieves preferred labs of a given patient.
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        patient = self.get_object()
        labs = patient.preferred_laboratories.all()
        if not len(labs):
            raise Http404()

        return Response({"preferred_laboratories": LaboratorySerializer(labs, many=True).data})

    @list_route()
    def current(self, request, *args, **kwargs):
        """
        Retrieves current patient instance.
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        try:
            patient = Patient.objects.get(pk=self.request.user.id)
            return Response(PatientSerializer(patient, context={"request": request}).data)
        except ObjectDoesNotExist:
            raise Http404()

    @list_route(url_path="current/prescriptions")
    def prescriptions_from_current(self, request, *args, **kwargs):
        """
        Retrieves current patient's prescriptions.
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        try:
            patient = Patient.objects.get(pk=self.request.user.id)
            prescriptions = MedicalPrescription.objects.filter(patient=patient.user.id).order_by('created')
            if not len(prescriptions):
                raise Http404()

            if self.request.version == 'v4':
                prescription_serializer = MedicalPrescriptionByPatientV4Serializer
            elif self.request.version == 'v5':
                prescription_serializer = MedicalPrescriptionByPatientV5Serializer
            else:
                prescription_serializer = MedicalPrescriptionByPatientSerializer
            return Response({"patient": PatientSerializer(patient, context={"request": request}).data,
                             "prescriptions": prescription_serializer(prescriptions, many=True,
                                                                      context={"request": request}).data})
        except ObjectDoesNotExist:
            raise Http404()

    @list_route(url_path="confirmation")
    def confirmation(self, request, *args, **kwargs):
        """
        Confirms e-mail used by a Patient and mark current patient as confirmed
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        try:
            token = request.query_params["token"]
            patient = Patient.objects.get(hash=token)
            device_type = request.query_params.get(settings.DEVICE_TYPE_HEADERS, None)

            # TODO: Build an HTML page redirecting to Google Play/Apple Store
            if patient.is_confirmed:
                if device_type == settings.IOS:
                    return self.__get_custom_redirect("userAlreadyConfirmed", patient)

                return HttpResponse(
                    "Este email já foi confirmado! Clique, pelo seu celular, neste link e marque seus exames agora mesmo. Nos vemos em breve. Sara")

            patient.is_confirmed = True
            patient.save()

            ObtainExpirableTokenSerializer.get_new_token(user=patient.user, key=token)

            if device_type == settings.IOS:
                return self.__get_custom_redirect("userConfirmation", patient)

            return HttpResponse(
                "Email confirmado! Clique, pelo seu celular, neste link e marque seus exames agora mesmo. Nos vemos em breve. Sara")

        except ObjectDoesNotExist:
            raise Http404("Could not activate this user.")
        except KeyError:
            raise Http404("Token not found.")

    @list_route(url_path="send-confirmation")
    def send_confirmation(self, request, *args, **kwargs):
        """
        Sends confirmation e-mail for a patient in case he/she didn't receive the first email
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        email = request.query_params.get("email", None)
        if not email:
            return Response({"detail": "You must send email parameter in querystring",
                             "status_code": status.HTTP_400_BAD_REQUEST},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            patient = Patient.objects.get(user__email=email)
        except ObjectDoesNotExist:
            raise Http404("Email account not found.")

        try:
            device_type = request.META.get(settings.DEVICE_TYPE_HEADERS, None)
            PatientCreateSerializer.send_confirmation_email(patient, device_type)
            return Response({}, status=status.HTTP_200_OK)

        except RuntimeError:
            return Response({"detail": "Could not send email. Try again later.",
                             "status_code": status.HTTP_400_BAD_REQUEST},
                            status=status.HTTP_400_BAD_REQUEST)

    @detail_route(url_path="push-notification", methods=["POST"])
    def send_push_notification(self, request, *args, **kwargs):
        """
        Sends a push notification to the current Patient (test purposes only)
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        patient = self.get_object()
        request_data = request.data

        if not patient.token:
            Response({"detail": "Could not send notification. "
                                "There's no device token registered for this user.",
                      "status_code": status.HTTP_400_BAD_REQUEST},
                     status=status.HTTP_400_BAD_REQUEST)

        subject = request_data.get("subject", None)
        message = request_data.get("message", None)
        data = request_data.get("data", None)
        eta = request_data.get("eta", None)

        if None in (subject, message):
            return Response({"detail": "Could not send notification. "
                                       "The following fields are mandatory: [subject, message].",
                             "status_code": status.HTTP_400_BAD_REQUEST}, status=status.HTTP_400_BAD_REQUEST)
        if data and type(data) is not dict:
            return Response({"detail": "Could not send notification. The following field must be a json: [data].",
                             "status_code": status.HTTP_400_BAD_REQUEST}, status=status.HTTP_400_BAD_REQUEST)
        if eta:
            try:
                eta = remove_milliseconds_from_timestamp(eta)
                eta = datetime.datetime.fromtimestamp(eta)

                send_push_notification.apply_async(
                    args=[patient.token, subject, message, data],
                    eta=eta,
                )
                return Response({}, status=status.HTTP_202_ACCEPTED)

            except:
                return Response({"detail": "Could not send notification. "
                                           "The following field must be a valid timestamp: [eta].",
                                 "status_code": status.HTTP_400_BAD_REQUEST}, status=status.HTTP_400_BAD_REQUEST)

        send_push_notification.apply_async(args=[patient.token, subject, message, data], )

        return Response({}, status=status.HTTP_202_ACCEPTED)

    def get_permissions(self):
        """
        Rewrites get_permissions method in order to dynamically gets permissions depending on the action
        :return:
        """
        try:
            return [permission() for permission in self.permission_classes_by_action[self.action]]
        except KeyError:
            # action is not set, return default permission_classes
            return [permission() for permission in self.permission_classes]

    @staticmethod
    def __get_custom_redirect(path, patient):
        custom_schema_url = "{0}{1}/{2}".format(settings.CUSTOM_SCHEMA, path, patient.hash)
        response = HttpResponse("", status=302)
        response['Location'] = custom_schema_url

        return response

    @list_route(url_path="grouped-prescriptions")
    def grouped_prescriptions(self, request, *args, **kwargs):
        """
        Retrieves current patient instance.
        :param request:
        :param args:
        :param kwargs:
        :return:
        """

        patient = Patient.objects.get(pk=self.request.user.id)
        prescriptions = patient.medicalprescription_set.all()
        prescription_ids = [prescription.pk for prescription in prescriptions]
        exams = ScheduledExam.objects.filter(
            status__in=[
                ScheduledExam.EXAM_TIME_SCHEDULED,
                ScheduledExam.PATIENT_CANCELED,
                ScheduledExam.LAB_RECORD_CANCELED,
                ScheduledExam.LAB_RECORD_OPEN,
                ScheduledExam.EXAM_MISSED,
                ScheduledExam.EXAM_EXPIRED,
            ],
            prescription__pk__in=prescription_ids
        )

        ids_to_exclude = []
        seen = set()
        statuses_dict = {}
        for exam in exams:
            if not (exam.scheduled_time and exam.laboratory):
                continue
            statuses_dict[str(exam.pk)] = exam.status
            group_params = (exam.scheduled_time.day, exam.laboratory.pk, exam.status, exam.prescription.pk)
            if group_params not in seen:
                seen.add(group_params)
            else:
                ids_to_exclude.append(exam.pk)

        final_exams = exams.exclude(pk__in=ids_to_exclude).order_by('scheduled_time')
        return Response(GroupedScheduledExamSerializer(final_exams, many=True, context={
            "request": request,
            "statuses": statuses_dict}).data)

    @list_route(url_path="crawler_share", methods=["POST"])
    def crawler_share(self, request, *args, **kwargs):
        """
        Share patient's exam results with a doctor
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        log.info("[sharedoctor] Incoming request data {!r}".format(request.data))
        patient = Patient.objects.get(pk=self.request.user.id)
        doctor_email = request.data.get('email')

        if not doctor_email:
            return Response({'error': 'Non data'}, status=400)

        clinic_core_sharedoctor_endpoint = settings.SARA_CLINIC.get('crawler_sharedoctor_endpoint')
        clinic_core_token = settings.SARA_CLINIC.get('token')
        request_headers = {
            "Authorization": clinic_core_token,
            "Content-Type": "application/json"
        }

        try:
            request_data = {
                "patient_id": {"id": patient.user.id,
                               "email": patient.user.email,
                               "name": patient.full_name
                               },
                "email": doctor_email
            }
            log.info("[sharedoctor] Outgoing request data {!r}".format(request_data))
            r = requests.post(clinic_core_sharedoctor_endpoint,
                              data=json.dumps(request_data),
                              headers=request_headers)

            if r.status_code not in [200, 201, 202]:
                log.error(r.text)
                return Response({"detail": 'Erro ao compartilhar os resultados.',
                                 "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            log.info("{!r}".format(e))
            return Response(data={'error': e.__str__()}, status=500)

        return Response({}, status.HTTP_202_ACCEPTED)

    @list_route(url_path="crawler_results", methods=["GET"])
    def crawler_results(self, request, *args, **kwargs):
        """
        Adds, updates and removes crawler data from patient models
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        patient = Patient.objects.get(pk=self.request.user.id)

        try:
            headers = None
            if settings.SARA_CLINIC.get('token', None):
                headers = {'Authorization': settings.SARA_CLINIC.get('token')}

            clinic = requests.get(settings.SARA_CLINIC.get('crawler_results_endpoint').format(patient.user.id), headers=headers)

            if clinic.status_code in [200, 201, 202]:
                res = clinic.json()
                if res:
                    return Response(res, 200)
            return Response({}, status.HTTP_404_NOT_FOUND)

        except Exception as e:
            print(e)
            return Response(data={'error': e.__str__()}, status=500)

    @list_route(url_path="crawler_social_sharing", methods=["POST"])
    def crawler_social_sharing(self, request, *args, **kwargs):
        """
        Returns crawler social sharing link
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        log.info("[crawler_social_sharing] Incoming request data {!r}".format(request.data))
        patient = Patient.objects.get(pk=self.request.user.id)
        patient_phone = request.data.get('phone')

        if not patient_phone:
            return Response({'error': 'Non data'}, status=400)

        clinic_core_social_sharing_endpoint = settings.SARA_CLINIC.get('crawler_social_sharing')
        clinic_core_token = settings.SARA_CLINIC.get('token')
        request_headers = {
            "Authorization": clinic_core_token,
            "Content-Type": "application/json"
        }

        try:
            request_data = {
                "patient_id": {"id": patient.user.id,
                               "email": patient.user.email,
                               "name": patient.full_name
                               },
                "phone": patient_phone
            }
            log.info("[crawler_social_sharing] Outgoing request data {!r}".format(request_data))
            r = requests.post(clinic_core_social_sharing_endpoint,
                              data=json.dumps(request_data),
                              headers=request_headers)

            if r.status_code not in [200, 201, 202]:
                log.error(r.text)
                return Response({"detail": 'Erro ao compartilhar os resultados.',
                                 "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            log.info("{!r}".format(e))
            return Response(data={'error': e.__str__()}, status=500)

        return Response(r.json(), status.HTTP_202_ACCEPTED)

    @list_route(url_path="crawler_labs", methods=["POST", "PUT", "DELETE"])
    def crawler_labs(self, request, *args, **kwargs):
        """
        Adds, updates and removes crawler data from patient models
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        patient = Patient.objects.get(pk=self.request.user.id)
        request_data = request.data

        if request.method in ['PUT', 'POST']:
            try:
                clinic_core_crawler_endpoint = settings.SARA_CLINIC.get('crawler_endpoint')
                clinic_core_token = settings.SARA_CLINIC.get('token')
                request_headers = {
                    "Authorization": clinic_core_token,
                    "Content-Type": "application/json"
                }

                patient_credentials = {
                    "patient_id": {"id": patient.user.id,
                                   "email": patient.user.email,
                                   "name": patient.full_name}
                }

                for k, v in request_data.items():
                    lab_username = v.get('username', '')
                    lab_password = v.get('password', '')
                    setattr(patient, '{}_user'.format(k), lab_username)
                    setattr(patient, '{}_pass'.format(k), lab_password)

                    patient_credentials.update({
                        k: {"username": lab_username,
                            "password": lab_password}
                    })
                patient.save()

                clinic = requests.post(clinic_core_crawler_endpoint,
                                       json=patient_credentials,
                                       headers=request_headers)

                if clinic.status_code not in [200, 201, 202]:
                    print(clinic.text)
                    return Response({"detail": 'Erro ao iniciar processo de captura de resultados',
                                     "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR},
                                    status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                return Response({}, status.HTTP_202_ACCEPTED)
            except Exception as e:
                print(e)
                return Response({"detail": str(e),
                                 "status_code": status.HTTP_400_BAD_REQUEST},
                                status=status.HTTP_400_BAD_REQUEST)
        if request.method == 'DELETE':
            patient.einstein_pass = ''
            patient.einstein_user = ''
            patient.lavoisier_pass = ''
            patient.lavoisier_user = ''
            patient.save()
            return Response({}, status.HTTP_202_ACCEPTED)

        return Response({}, status.HTTP_204_NO_CONTENT)


class MedicalPrescriptionViewSet(RevisionMixin,
                                 RequestLogViewMixin,
                                 mixins.RetrieveModelMixin,
                                 mixins.UpdateModelMixin,
                                 mixins.CreateModelMixin,
                                 viewsets.GenericViewSet):
    """
    A viewset for viewing and editing Medical Prescription instances.
    """
    queryset = MedicalPrescription.objects.all()

    def get_serializer_class(self):
        """
        Defines serializer class dynamically.
        :return:
        """
        if self.request.version == 'v3':
            if self.action == 'retrieve':
                return MedicalPrescriptionRetrieveSerializer

            if self.action == 'update':
                return MedicalPrescriptionUpdateSerializer

            if self.action == 'create':
                return MedicalPrescriptionCreateSerializer

        if self.request.version == 'v4':
            if self.action == 'retrieve':
                return MedicalPrescriptionRetrieveV4Serializer

            if self.action == 'update':
                return MedicalPrescriptionUpdateV4Serializer

            if self.action == 'create':
                return MedicalPrescriptionCreateV4Serializer

        if self.request.version == 'v5':
            if self.action == 'retrieve':
                return MedicalPrescriptionRetrieveV5Serializer

            if self.action == 'update':
                return MedicalPrescriptionUpdateV4Serializer

            if self.action == 'create':
                return MedicalPrescriptionCreateV4Serializer

    def create(self, request, *args, **kwargs):
        """
        Overwrites create method.
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        try:
            serializer = self.get_serializer_class()(data=request.data, context={"request": request})
            serializer.set_latest_prescription()
            serializer.is_valid(raise_exception=True)
            prescription = serializer.save()

            if self.request.version == 'v4':
                response_serializer = MedicalPrescriptionRetrieveV4Serializer
            elif self.request.version == 'v5':
                response_serializer = MedicalPrescriptionRetrieveV5Serializer
            else:
                response_serializer = MedicalPrescriptionRetrieveSerializer

            return Response(response_serializer(prescription, context={"request": request}).data,
                            status=status.HTTP_201_CREATED)
        except ObjectDoesNotExist as exc:
            return Response({"detail": str(exc),
                             "status_code": status.HTTP_400_BAD_REQUEST},
                            status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        """
        Overwrites update method in order to handle ObjectDoesNotExist.
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        try:
            partial = kwargs.pop('partial', False)
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)

            self.perform_update(serializer)

            if self.request.version == 'v4':
                response_serializer = MedicalPrescriptionRetrieveV4Serializer
            elif self.request.version == 'v5':
                response_serializer = MedicalPrescriptionRetrieveV5Serializer
            else:
                response_serializer = MedicalPrescriptionRetrieveSerializer
            return Response(response_serializer(instance, context={"request": request}).data,
                            status=status.HTTP_200_OK)
            # return super(MedicalPrescriptionViewSet, self).update(request, *args, **kwargs)
        except ObjectDoesNotExist as exc:
            return Response({"detail": str(exc),
                             "status_code": status.HTTP_400_BAD_REQUEST},
                            status=status.HTTP_400_BAD_REQUEST)

    @detail_route(url_path="preparation-steps")
    @authenticate_user_by_prescription
    def preparation_steps(self, request, *args, **kwargs):
        """
        Retrieves all preparations steps which belong to exams within medical prescription.
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        prescription = self.get_object()
        scheduled_exams = ScheduledExam.objects.filter(prescription=prescription.id)
        if not len(scheduled_exams):
            raise Http404()

        preparation_steps = []
        for scheduled_exam in scheduled_exams:
            if not scheduled_exam.laboratory:
                continue
            preparation_step_objs = PreparationStep.objects.filter(exam=scheduled_exam.exam.id,
                                                                   laboratory=scheduled_exam.laboratory.id)

            if not preparation_step_objs:
                preparation_step_objs = PreparationStep.objects.filter(exam=scheduled_exam.exam.id, laboratory__brand_id=scheduled_exam.laboratory.brand.id).order_by('id').last()

            if preparation_step_objs:
                preparation_steps.append(PreparationStepSerializer(preparation_step_objs, many=True).data)

        if not len(preparation_steps):
            raise Http404()

        return Response(preparation_steps)

    @detail_route(url_path="exams-result")
    @authenticate_user_by_prescription
    def exams_result(self, request, *args, **kwargs):
        """
        Retrieves all exams result within a medical prescription.
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        prescription = self.get_object()

        scheduled_exams = ScheduledExam.objects.filter(prescription=prescription.id)
        if not len(scheduled_exams):
            raise Http404()

        # scheduled_exams_ids = [scheduled_exam.id for scheduled_exam in scheduled_exams]
        # exams_result = ExamResult.objects.filter(scheduled_exam__in=scheduled_exams_ids)
        # if not len(exams_result):
        #     raise Http404()

        content = self.assert_results(
            ExamResultSerializer(scheduled_exams, many=True, context={"request": request}).data)

        return Response(content)

    def assert_results(self, data):
        newData = []

        for item in data:
            if item.get('file_url'):
                if len(item.get('file_url')) == 1:
                    newData.append({'exam_id': item.get('exam_id'),
                                    'file_url': item.get('file_url')[0],
                                    'exam_result_details': {}})
                else:
                    for i in item.get('file_url'):
                        newData.append({'exam_id': item.get('exam_id'),
                                        'file_url': i,
                                        'exam_result_details': {}})
        return newData

    @detail_route(url_path="scheduled-exams")
    @authenticate_user_by_prescription
    def scheduled_exams(self, request, *args, **kwargs):
        """
        Retrieves all scheduled exams within a medical prescription.
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        prescription = self.get_object()
        scheduled_exams = ScheduledExam.objects.filter(prescription=prescription.id)
        if not len(scheduled_exams):
            raise Http404()
        from patient_api.serializers.v3 import ScheduledExamSerializer
        return Response(ScheduledExamSerializer(scheduled_exams, many=True, context={"request": request}).data)


class ScheduledExamViewSet(RequestLogViewMixin,
                           RevisionMixin,
                           mixins.RetrieveModelMixin,
                           mixins.UpdateModelMixin,
                           viewsets.GenericViewSet):
    queryset = ScheduledExam.objects.all()

    def get_serializer_class(self):
        if self.request.version in ('v3', 'v4', 'v5'):
            return ScheduledExamRetrieveSerializer

    def update(self, request, *args, **kwargs):
        """
        Overwrites update method in order to handle ObjectDoesNotExist.
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        try:
            return super(ScheduledExamViewSet, self).update(request, *args, **kwargs, context={"request": request})
        except (ObjectDoesNotExist, ValueError) as exc:
            return Response({"detail": str(exc),
                             "status_code": status.HTTP_400_BAD_REQUEST},
                            status=status.HTTP_400_BAD_REQUEST)

    @detail_route(methods=["PUT", "PATCH"])
    def cancel(self, request, *args, **kwargs):
        """
        Sets ScheduledExam status to "PATIENT_CANCELED" in order to cancel current exam
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        scheduled_exam = self.get_object()
        try:
            scheduled_exam.status = ScheduledExam.PATIENT_CANCELED
            scheduled_exam.modified_by = self.request.user
            scheduled_exam.save()

            return Response({}, status=status.HTTP_200_OK)
        except:
            return Response({"detail": "Couldn't save current scheduled exam status",
                             "status_code": status.HTTP_400_BAD_REQUEST}, status=status.HTTP_400_BAD_REQUEST)

    @detail_route(methods=["POST", ])
    def retry(self, request, *args, **kwargs):
        """
        Sets ScheduledExam status to "EXAM_IDENTIFIED" in order to retry current denied exam
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        scheduled_exam = self.get_object()
        try:
            scheduled_exam.status = ScheduledExam.EXAM_IDENTIFIED
            scheduled_exam.modified_by = self.request.user
            scheduled_exam.lab_file_code = None
            scheduled_exam.save()

            prescription = scheduled_exam.prescription
            prescription.status = MedicalPrescription.EXAMS_IDENTIFIED
            prescription.modified_by = self.request.user
            prescription.save()

            return Response({}, status=status.HTTP_200_OK)
        except:
            return Response({"detail": "Couldn't save current scheduled exam status",
                             "status_code": status.HTTP_400_BAD_REQUEST}, status=status.HTTP_400_BAD_REQUEST)

    @list_route(methods=["PUT"])
    def batch(self, request, *args, **kwargs):
        """
        Updates ScheduledExam(s) in batch all at once in order to save HTTP requests when scheduling Exams packages
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        try:
            serializer = self.get_serializer()
            response = serializer.batch_update(request.data, request.user)
            return Response(ScheduledExamRetrieveSerializer(response, many=True).data, status=status.HTTP_200_OK)
        except (ObjectDoesNotExist, ValueError) as exc:
            return Response({"detail": str(exc),
                             "status_code": status.HTTP_400_BAD_REQUEST},
                            status=status.HTTP_400_BAD_REQUEST)


class ScheduledExamPhoneCallViewSet(RequestLogViewMixin,
                                    mixins.UpdateModelMixin,
                                    mixins.CreateModelMixin,
                                    viewsets.GenericViewSet):
    queryset = ScheduledExamPhoneCall.objects.all()

    def get_serializer_class(self):
        """
        Defines serializer class dynamically.
        :return:
        """
        if self.request.version in ('v3', 'v4', 'v5'):
            if self.action == 'update':
                return ScheduledExamPhoneCallUpdateSerializer

            if self.action == 'create':
                return ScheduledExamPhoneCallCreateSerializer

            if self.action == 'batch':
                return ScheduledExamPhoneCallBatchSerializer

    def create(self, request, *args, **kwargs):
        """
        Overwrites create method in order to handle IntegrityError and ObjectDoesNotExist.
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        try:
            return super(ScheduledExamPhoneCallViewSet, self).create(request, *args, **kwargs)
        except IntegrityError:
            return Response({"detail": "This exam already has a phone call scheduled.",
                             "status_code": status.HTTP_400_BAD_REQUEST},
                            status=status.HTTP_400_BAD_REQUEST)
        except (ObjectDoesNotExist, ValueError) as exc:
            return Response({"detail": str(exc),
                             "status_code": status.HTTP_400_BAD_REQUEST},
                            status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        """
        Overwrites update method in order to handle ObjectDoesNotExist.
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        try:
            return super(ScheduledExamPhoneCallViewSet, self).update(request, *args, **kwargs)
        except (ObjectDoesNotExist, ValueError) as exc:
            return Response({"detail": str(exc),
                             "status_code": status.HTTP_400_BAD_REQUEST},
                            status=status.HTTP_400_BAD_REQUEST)

    @list_route(methods=["POST", "PUT"])
    def batch(self, request, *args, **kwargs):
        """
        Updates ScheduledExamPhoneCall(s) in batch all at once in order to save HTTP requests
        when scheduling Exams packages
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        try:
            response = ScheduledExamPhoneCallBatchSerializer(context={"request": request}).batch_update(
                data=request.data)
            return Response(ScheduledExamPhoneCallBatchSerializer(response, many=True).data, status=status.HTTP_200_OK)
        except ObjectDoesNotExist as exc:
            return Response({"detail": str(exc),
                             "status_code": status.HTTP_404_NOT_FOUND},
                            status=status.HTTP_404_NOT_FOUND)
        except ValueError as ve:
            return Response({"detail": str(ve),
                             "status_code": status.HTTP_400_BAD_REQUEST},
                            status=status.HTTP_400_BAD_REQUEST)
        except IntegrityError as ie:
            return Response({"detail": "Phone call already created for one of the exams in the list",
                             "status_code": status.HTTP_400_BAD_REQUEST},
                            status=status.HTTP_400_BAD_REQUEST)


class HolidayViewSet(RequestLogViewMixin,
                     mixins.ListModelMixin,
                     viewsets.GenericViewSet):
    serializer_class = HolidaySerializer
    queryset = Holiday.objects.all()

    def get_serializer_context(self):
        """
        Overwrites get_serializer_context method in order to add custom queryset.
        """
        return {
            'request': self.request,
            'format': self.format_kwarg,
            'view': self,
            'queryset': self.get_queryset()
        }

    def get_queryset(self):
        """
        Overwrites get_queryset method.
        """
        queryset = super(HolidayViewSet, self).get_queryset()
        query_params = self.request.query_params
        year = query_params.get("year", None)
        lab_id = query_params.get("lab_id", None)
        lat = query_params.get("lat", None)
        lng = query_params.get("lng", None)
        if lat and lng:
            maps = Maps()
            geocode = maps.client.reverse_geocode((lat, lng))
            address_components = geocode[0]['address_components']

            country = get_address_component(address_components, "country")
            state = get_address_component(address_components, "administrative_area_level_1")
            city = get_address_component(address_components, "administrative_area_level_2")
        elif lab_id:
            try:
                laboratory = Laboratory.objects.get(pk=lab_id)
                country = laboratory.country
                state = laboratory.state
                city = laboratory.city
            except Laboratory.DoesNotExist:
                raise Http404()
        else:
            country = query_params.get("country", None)
            state = query_params.get("state", None)
            city = query_params.get("city", None)

        if year:
            queryset = queryset.filter(date__year=year)
        country_queryset = Holiday.objects.none()
        if country:
            country_queryset = queryset.filter(
                Q(country__iexact=country) &
                (Q(state__isnull=True) | Q(state='')) &
                (Q(city__isnull=True, ) | Q(city=''))
            )
            # country_queryset = queryset.filter(country__iexact=country)
        state_queryset = Holiday.objects.none()
        if country and state:
            state_queryset = queryset.filter(
                Q(country__iexact=country) &
                Q(state__iexact=state) &
                (Q(city__isnull=True) | Q(city=''))
            )
        city_queryset = Holiday.objects.none()
        if country and state and city:
            city_queryset = queryset.filter(
                country__iexact=country,
                state__iexact=state,
                city__iexact=city

            )
        queryset = list(chain(country_queryset, state_queryset, city_queryset))
        return queryset

    def list(self, request, *args, **kwargs):
        """
        Overwrites list method in order to have custom response.
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)
