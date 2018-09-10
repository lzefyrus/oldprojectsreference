# encode: utf-8

import json

import pyrebase
from django.conf import settings
from django.shortcuts import render
from django.template.exceptions import TemplateDoesNotExist
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from rest_framework.response import Response

from domain import models as domain_models
from domain.tasks import send_push_notification
from domain.tasks import update_results, zendesk_adf
from general_utils.utils import close_ticket, get_utc_from_bz, close_adf_ticket
from . import models as m2m_models
from .serializers import *


@api_view(['POST'])
def results(self, *args, **kwargs):
    """
    Retrieves current operator instance.
    :param request:
    :param args:
    :param kwargs:
    :return:
    """
    try:
        if self.data:
            update_results.apply_async(args=[self.data])
            return Response({})
        return Response(data={'error': "No data received"}, status=400)

    except Exception as e:
        print(e)
        return Response(data={'error': e.__str__()}, status=500)


@api_view(['POST'])
def ticket(self, *args, **kwargs):
    """
    Retrieves current operator instance.
    :param request:
    :param args:
    :param kwargs:
    :return:
    """
    try:
        # zendesk/prescription
        if self.data:
            data = self.data
            if type(data) is str:
                data = json.loads(data)

            print(data)

            if data.get('status').upper() == domain_models.MedicalPrescription.PATIENT_REQUESTED:
                return Response({})

            mp = domain_models.MedicalPrescription.objects.filter(zendeskticket__external_id=data.get('id', 0)).first()
            print(mp)

            if mp and mp.status not in domain_models.MedicalPrescription.CANCEL_STATUS:
                mp.status = data.get('status').upper()
                if mp.status not in domain_models.MedicalPrescription.CANCEL_STATUS:
                    mp.status = domain_models.MedicalPrescription.NOT_A_PRESCRIPTION
                mp.save()
                if mp.status != domain_models.MedicalPrescription.PATIENT_REQUESTED:
                    try:
                        # force item removal from FB
                        firebase = pyrebase.initialize_app(settings.FB_CONFIG)
                        db = firebase.database()
                        db.child('prescriptions').child(mp.pk).remove()
                    except Exception as e:
                        print(e)
                return Response({})
            return Response(data={'error': "Status must be PATIENT_REQUESTED EXAMS_ANALYZED PATIENT_REQUESTED"},
                            status=400)
        return Response(data={'error': "No data received"}, status=400)

    except Exception as e:
        print(e)
        return Response(data={'error': e.__str__()}, status=500)


@csrf_exempt
@xframe_options_exempt
@api_view(['POST'])
def update_prescription(request):
    try:
        rdata = request.data
        instance = domain_models.MedicalPrescription.objects.filter(
            zendeskticket__external_id=rdata.get('ticket', None)).first()

        if not instance or instance.status != domain_models.MedicalPrescription.PATIENT_REQUESTED:
            raise Exception('Esta precricão já foi atualizada ou não foi encontrada')

        #IMPORTANT, on zendek all will be UTC - MUST ALSO UPDATE THE APP
        grouped = [{'lab': int(rdata.get('laboratory{}_id'.format(i), 0)),
                    'date': get_utc_from_bz(
                        datetime.datetime.strptime(rdata.get('date{}'.format(i), None), '%d/%m/%Y %H:%M')),
                    'exams': rdata.get('exams{}_id'.format(i)).split(',')} for i in range(1, 10) if
                   rdata.get('laboratory{}_id'.format(i), None)]

        with transaction.atomic():
            instance.status = domain_models.MedicalPrescription.EXAMS_ANALYZED
            ppiece = instance.pieces.all().first()
            for item in grouped:
                if item.get('lab', None) and item.get('date', None) and item.get('exams', None):
                    exams = domain_models.Exam.objects.filter(pk__in=item.get('exams', None)).all()
                    group = []
                    for exam in exams:
                        scheduled_exam = domain_models.ScheduledExam(
                            exam=exam,
                            prescription=instance,
                            prescription_piece=ppiece,
                            laboratory_id=item['lab'],
                            scheduled_time=item['date'],
                            status=domain_models.ScheduledExam.EXAM_TIME_SCHEDULED
                        )
                        scheduled_exam.save()
                        group.append(scheduled_exam.id)
                        print(group)
                    if group:
                        print("Creating adf for {}".format(','.join(str(i) for i in group)))
                        zendesk_adf.apply_async(args=[group])

        instance.save()
        try:
            # force item removal from FB
            firebase = pyrebase.initialize_app(settings.FB_CONFIG)
            db = firebase.database()
            db.child('prescriptions').child(instance.pk).remove()
        except Exception as e:
            print(e)

        # closes zendesk ticket
        close_ticket(instance)

        return Response({}, 200)
    except Exception as e:
        return Response({'detail': str(e)}, 400)


@csrf_exempt
@xframe_options_exempt
@api_view(['POST'])
def do_adf(request):
    try:
        rdata = request.data
        instance = m2m_models.ZendeskASFTicket.objects.filter(external_id=rdata.get('ticket', None)).first()

        if len(rdata.get('fap')) <=4:
            return Response({'detail': 'FAP não pode ser menor que 4 dígitos'}, 400)

        if not instance:
            raise Exception('Exames para a abertura de ficha não encontrados')

        with transaction.atomic():
            sexams = instance.scheduledexam_set.all()
            ids = [i.get('id') for i in sexams.values('id') if i.get('id') not in ['fap']]
            for item in sexams:
                item.status = domain_models.ScheduledExam.LAB_RECORD_OPEN
                if item.id not in ids:
                    item.status = domain_models.ScheduledExam.LAB_RECORD_CANCELED

                item.save()

        # closes zendesk ticket
        close_adf_ticket(instance)

        return Response({}, 200)
    except Exception as e:
        return Response({'detail': str(e)}, 400)


@csrf_exempt
@xframe_options_exempt
def index(request):
    """
    Displays home page
    :param request:
    :return:
    """
    try:
        ticket = request.GET.get('ticket_id', None)

        adfticket = m2m_models.ZendeskASFTicket.objects.filter(external_id=str(ticket))

        if adfticket:
            sexans = domain_models.ScheduledExam.objects.filter(zendesk_adf_ticket=adfticket.first())
            print(sexans)
            return render(request, 'domain/scheduling_adf_zendesk.html', {'ticket': ticket,
                                                                          'sexams': sexans,
                                                                          'fb_settings': settings.FB_CONFIG})

        return render(request, 'domain/scheduling_zendesk.html', {'ticket': ticket,
                                                                  'fb_settings': settings.FB_CONFIG})
    except TemplateDoesNotExist as e:
        return render(request, 'domain/index.html')


@csrf_exempt
@api_view(['POST'])
def crawler_push(request):
    """
    :param request:
        {
            "patient_id": PATIENT_ID,
            "einstein": {"complete": true}
        }
        {
            "patient_id": PATIENT_ID,
            "fleury": {"complete": false, "detail": "error_reason"}
        }
    :return: 200, 500
    """
    patient_id = request.data.get('patient_id', 0)
    try:
        patient = domain_models.Patient.objects.get(pk=patient_id)
        send_push_notification.apply_async(args=[patient.token,
                                                 "Laboratório conectado",
                                                 "A conexão com o laboratório",
                                                 request.data])
    except Exception as e:
        print(e)
        return Response({'detail': str(e)}, 500)
    return Response({}, 200)


@csrf_exempt
@api_view(['GET'])
def check_adf(request):
    """
    """
    ticket_id = request.query_params.get('ticket_id', None)
    if not ticket_id:
        return Response({}, 404)
    try:
        adftc = m2m_models.ZendeskASFTicket.objects.filter(external_id=ticket_id)
        if not adftc:
            return Response({}, 404)

    except Exception as e:
        print(e)
        return Response({'detail': str(e)}, 500)
    return Response({}, 200)
