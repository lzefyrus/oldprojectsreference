import datetime

from django.conf import settings

import pytz

from django.contrib.auth.models import User as AuthUser
from django.db import transaction
from zenpy import Zenpy
from zenpy.lib.api_objects import Ticket, User, Comment, CustomField, UserField

from concierge.models import Operator
from domain import models as domain_models
from domain.models import *
from m2m.models import ZendeskTicket, ZendeskASFTicket
from pybrdst.pybrdst import PyBrDST
from domain.firebaser import FirebaseCloudMessaging


def exam_import():
    lab_ids = [i.id for i in Laboratory.objects.all()]
    old_exams = Exam.objects.all()
    old_exam_dict = {}
    for i in old_exams:
        old_exam_dict[i.name.upper()] = i.pk

    old_exam_keys = old_exam_dict.keys()

    with open(
            '{}/data/general_exams.csv'.format(settings.BASE_DIR),
            encoding='utf-8',
            errors='ignore') as file:
        for line in file.readlines():
            try:
                data = line.split(';')
                isphone = True if data[4].lower() == 'yes' else False
                if data[1].upper() in old_exam_keys:
                    exam = Exam.objects.get(
                        id=old_exam_dict.get(data[1].upper()))
                    exam.description = data[2]
                    exam.save()
                else:
                    exam = Exam.objects.create(
                        name=data[1],
                        description=data[2],
                        exam_type=data[3],
                        is_scheduled_by_phone=isphone)
                if len(data[5]) > 5:
                    if data[1].upper() in old_exam_keys:
                        update_preparation(exam.id, data[5])
                    else:
                        preps = []
                        for l in lab_ids:
                            preps.append(
                                PreparationStep(
                                    title="Preparos para o exame",
                                    description=data[5],
                                    is_mandatory=True,
                                    exam=exam,
                                    laboratory_id=l))
                        PreparationStep.objects.bulk_create(preps)

            except Exception as e:
                print(e)


def update_preparation(id, text):
    preps = PreparationStep.objects.filter(exam_id=id)
    for i in preps:
        with transaction.atomic():
            cont = i
            cont.description = text
            cont.save()


def create_users():
    with open(
            '{}/data/concierge_users.csv'.format(settings.BASE_DIR),
            encoding='utf-8',
            errors='ignore') as file:
        for line in file.readlines():
            try:
                data = line.split(',')
                cuser = AuthUser.objects.create_user(
                    username=data[1].strip(),
                    password=data[2].strip(),
                    first_name=data[0].split()[0],
                    last_name=' '.join(data[0].split()[1:]))
                op = Operator(user=cuser)
                op.save()

            except Exception as e:
                print(e)


def insurance_plans():
    import pyrebase
    insplan = 'insurances'
    ipex = 'insurance_labs'
    firebase = pyrebase.initialize_app(settings.FB_CONFIG)
    db = firebase.database()

    plans = {}
    insurances = HealthInsurance.objects.filter(is_active=True)

    total = insurances.count()

    initial = 2500

    for i in insurances[:initial]:
        plans[i.external_id] = {'id': i.pk, 'name': i.description}

    print(plans)

    from pprint import pprint

    db.child(insplan).set(plans)

    for r in range(initial, total, initial):

        tmp = {}
        for i in insurances[r:2500 + initial]:
            plans[i.external_id] = {'id': i.pk, 'name': i.description}
            tmp[i.external_id] = plans[i.external_id]

        pprint(tmp, None, 4)
        db.child(insplan).update(tmp)
        initial += 2500
    ll = 0
    plans = {}

    laboratories_lavo = [
        70, 27, 39, 41, 42, 43, 44, 46, 51, 52, 53, 54, 55, 57, 58, 64, 65, 66,
        69, 71, 4, 78, 72, 74, 75, 77, 79, 80, 81, 82, 84, 85, 89, 90, 6, 108,
        120, 93, 94, 96, 97, 98, 99, 100, 101, 102, 103, 105, 106, 107, 109,
        112, 114, 117, 119, 122, 177, 166, 153, 140, 141, 142, 143, 154, 156,
        157, 160, 161, 168, 170, 171, 176, 178, 179, 180, 181, 182, 184, 200,
        197, 193, 40, 91, 92, 110, 126, 162, 5, 188, 187, 190, 191, 195, 196,
        198, 199, 203
    ]
    with open(
            '{}/data/lavo.csv'.format(settings.BASE_DIR),
            encoding='utf-8',
            errors='ignore') as file:
        for line in file.readlines():
            ll += 1
            try:
                data = line.split(';')
                tmp = {data[0]: laboratories_lavo}
                if not data[1] in plans.keys():
                    plans[data[1]] = {}
                plans[data[1]].update(tmp)
            except Exception as e:
                print(e)
    db.child(ipex).set(plans)


def add_brands():
    import pyrebase
    firebase = pyrebase.initialize_app(settings.FB_CONFIG)
    db = firebase.database()

    brands = {
        str(i.get('id')): i.get('name')
        for i in LaboratoryBrand.objects.filter(
            is_active=True).values('id', 'name')
    }

    print(brands)

    db.child('configs').child('brands').update(brands)


def movedata():
    objs = domain_models.MedicalPrescription.objects.filter(
        id__in=[
            2591, 2599, 2602, 2616, 2629, 2637, 2638, 2641, 2652, 2664, 2678,
            2680, 2686, 2689, 2692, 2709, 2712, 2713, 2716, 2718, 2720, 2721,
            2723, 2727, 2728, 2731
        ])

    for instance in objs:
        try:
            do_schedule(instance)
        except Exception as e:
            print('{}: {}'.format(instance.id, e))


def do_schedule(instance):
    """
    Skip the prescription to phone call for all exams
    must update all schedule_exams also
    :param instance:
    :return: instance
    """

    if instance.status == domain_models.MedicalPrescription.EXAMS_ANALYZED:
        return instance

    sc_status = domain_models.ScheduledExam.PHONE_CALL_SCHEDULED
    mp_status = domain_models.MedicalPrescription.EXAMS_ANALYZED

    now = datetime.datetime.now()
    phone = instance.patient.phone

    sc_pieces = instance.scheduledexam_set.all()

    with transaction.atomic():

        for scp in sc_pieces:
            scp.status = sc_status
            scp.scheduled_time = now
            # if not domain_models.ScheduledExamPhoneCall.objects.filter(scheduled_exam=instance):
            ss = domain_models.ScheduledExamPhoneCall(
                scheduled_exam=scp,
                phone=phone,
                call_time=now,
                is_canceled=False,
                attempt=0)
            ss.save()
            scp.save()

        instance.status = mp_status
        instance.save()

        # try:
        #     PrescriptionUpdateSerializer.send_one_notification(instance, now, sc_pieces)
        # except Exception as e:
        #     print("Could not send the notification to user. Traceback: {}".format(e))

    return instance


def migrate_exams():
    """
    migrate all exams to firebase
    :return:
    """
    import pyrebase
    firebase = pyrebase.initialize_app(settings.FB_CONFIG)
    db = firebase.database()
    exams = Exam.objects.all().values('id', 'external_id', 'name',
                                      'description', 'synonymy', 'exam_type',
                                      'is_scheduled_by_phone')

    fexams = {}
    for i, exam in enumerate(exams):
        fexams[exam['id']] = {k: v for k, v in exam.items() if k != 'id'}
        fexams[exam['id']]['external_id'] = exam['id']
        # fexams[exam['id']]['search'] = '{} {}'.format(exam.get('name'), exam.get('description').lower())
        fexams[exam['id']]['search'] = exam.get('description').lower()
        if i % 150 == 0:
            db.child('exams').update(fexams)
            fexams = {}
    if len(fexams) > 0:
        db.child('exams').update(fexams)

    return True


def migrate_labs():
    """
    migrate all exams to firebase
    :return:
    """
    import pyrebase
    firebase = pyrebase.initialize_app(settings.FB_CONFIG)
    db = firebase.database()
    labs = Laboratory.objects.filter(is_active=True).values(
        'id', 'brand', 'description', 'district', 'city', 'state')

    flabs = {}
    for i, lab in enumerate(labs):
        flabs[lab['id']] = {k: v for k, v in lab.items() if k != 'id'}
        flabs[lab['id']]['external_id'] = lab['id']
        flabs[lab['id']]['search'] = lab.get('description').lower()
        if i % 150 == 0:
            db.child('labs').update(flabs)
            flabs = {}
    if len(flabs) > 0:
        db.child('labs').update(flabs)

    return True


def cleanup_calls():
    import pyrebase
    firebase = pyrebase.initialize_app(settings.FB_CONFIG)
    db = firebase.database()

    data = db.child('calls').get().val()
    for k, v in data.items():
        if len(v.keys()) == 1:
            db.child('calls').child(k).remove()


def update_adf(exams):
    pass


def create_zendesk_ticket(instance):
    try:

        zenpy_client = Zenpy(**settings.ZENDESK)

        if type(instance) in [str, int]:
            instance = domain_models.MedicalPrescription.objects.filter(
                id=int(instance)).first()
        desc = ""

        if instance.period_info:
            desc = "Última menstruação: {}".format(instance.period_info)

        desc = """{}
Informações Adicionais: {}""".format(desc, instance.additional_info
                                     or "Nenhuma")

        try:
            if instance.preferred_laboratory:
                desc = """{}
        Laboratório preferido: {}""".format(
                    desc, instance.preferred_laboratory.description or "Nenhuma")
        except Exception:
            print (instance.preferred_laboratory)

        try:
            if instance.preferred_date_to_schedule:
                desc = """{}
        Data preferida: {}""".format(desc,
                                    instance.preferred_date_to_schedule.strftime(
                                    "%Y-%m-%d %H:%M:%S") or "Nenhuma")
        except Exception:
            print(instance.preferred_date_to_schedule)
        selfie = ''
        if instance.patient.selfie_uploadcare:
            selfie = instance.patient.selfie_uploadcare.url
        elif instance.patient.selfie:
            selfie = instance.patient.selfie.url

        ticket = zenpy_client.tickets.create(
            Ticket(
                subject='Prescrição para: {}'.format(
                    instance.patient.full_name),
                requester=User(
                    name=instance.patient.full_name,
                    external_id=instance.patient.user.id,
                    email=instance.patient.user.email,
                    remote_photo_url=selfie,
                    user_fields=UserField(
                        gender=instance.patient.gender,
                        phone=str(instance.patient.phone))),
                type='task',
                priority='normal',
                custom_fields=[
                    CustomField(id=114103586991, value='patient_requested'),
                    CustomField(id=114103769352, value=instance.patient.phone),
                    CustomField(
                        id=114103769652, value=instance.patient.gender)
                ],
                description=desc))

        # a = MedicalPrescription.objects.all().last()
        # from general_utils.utils import create_zendesk_ticket
        # create_zendesk_ticket(a)
        et = ticket.ticket

        tdata = et.to_dict()
        del (tdata['via'])

        print(tdata)

        try:
            print('###')
            zticket = ZendeskTicket.objects.create(
                external_id=et.id, prescription=instance, content=tdata)
        except Exception:
            print('***')
            zticket = ZendeskTicket.objects.filter(
                prescription=instance).first()
            zticket.external_id = et.id
            zticket.content = tdata
            zticket.save()

        print(zticket)

        et.external_id = zticket.id
        et.tags.extend([u'prescrição', u'saracare'])
        #
        # from general_utils.utils import create_zendesk_ticket
        # p = MedicalPrescription.objects.all().last()
        # create_zendesk_ticket(p)

        ppieces = []

        for ppiece in instance.pieces.all():
            if ppiece.picture:
                ppieces.append(("Precrição", ppiece.picture.file))

        for name, file in [
            ("RG frente", instance.picture_id_front_uploadcare.file
             if instance.picture_id_front_uploadcare else None),
            ("RG verso", instance.picture_id_back_uploadcare.file
             if instance.picture_id_back_uploadcare else None),
            ("Plano frente",
             instance.picture_insurance_card_front_uploadcare.file
             if instance.picture_insurance_card_front_uploadcare else None),
            ("Plano verso",
             instance.picture_insurance_card_back_uploadcare.file
             if instance.picture_insurance_card_back_uploadcare else None)
        ] + ppieces:

            if file:
                upload_instance = zenpy_client.attachments.upload(file)
                et.comment = Comment(
                    body=name, uploads=[upload_instance.token])
                zenpy_client.tickets.update(et)

        zenpy_client.tickets.update(et)
    except Exception as e:
        print("Creation Error: {}".format(e))


def get_prescription_from_ticket(data):
    ticket = ZendeskTicket.objects.filter(
        external_id=data.get('ticket', '')).first()
    if not ticket:
        return None
    return ticket.prescription


def close_zendesk_ticket(instance):
    mticket = ZendeskTicket.objects.filter(prescription=instance).first()
    zenpy_client = Zenpy(**settings.ZENDESK)

    if not mticket:
        return False

    ticket = zenpy_client.tickets(id=mticket.external_id)

    ticket.status = 'solved'

    if instance.status in domain_models.MedicalPrescription.STATUS_CHOICES:
        new_cf = []
        for cf in ticket.custom_fields:
            if cf.get('id', None) == 114103846891:
                new_cf.append({
                    'id': 114103846891,
                    'value': instance.status.lower()
                })
            new_cf.append(cf)

        ticket.custom_fields = new_cf

    ticket_audit = zenpy_client.tickets.update(ticket)

    if ticket_audit:
        return True
    return False


def close_ticket(prescription):
    if not isinstance(prescription, MedicalPrescription):
        return False

    mticket = ZendeskTicket.objects.filter(prescription=prescription).first()
    zenpy_client = Zenpy(**settings.ZENDESK)

    if not mticket:
        return False

    ticket = zenpy_client.tickets(id=mticket.external_id)

    ticket.status = 'solved'

    if prescription.status in domain_models.MedicalPrescription.STATUS_CHOICES:
        new_cf = []
        for cf in ticket.custom_fields:
            if cf.get('id', None) == 114103846891:
                new_cf.append({
                    'id': 114103846891,
                    'value': prescription.status.lower()
                })
            new_cf.append(cf)

        ticket.custom_fields = new_cf

    ticket_audit = zenpy_client.tickets.update(ticket)

    if ticket_audit:
        return True
    return False


def close_adf_ticket(ticket):
    if not isinstance(ticket, ZendeskASFTicket):
        return False

    zenpy_client = Zenpy(**settings.ZENDESK)

    ticket = zenpy_client.tickets(id=ticket.external_id)

    ticket.status = 'solved'

    ticket_audit = zenpy_client.tickets.update(ticket)

    if ticket_audit:
        return True
    return False


def send_reports():
    from domain.tasks import send_kpis_per_day_report, send_general_kpi, send_kpi_prescription_call, \
        send_users_orders_report, send_users_report
    send_kpis_per_day_report()
    send_general_kpi()
    send_kpi_prescription_call()
    send_users_orders_report()
    send_users_report()


def delete_all_tickets():
    zenpy_client = Zenpy(**settings.ZENDESK)

    for ticket in zenpy_client.search(status="new"):
        zenpy_client.tickets.delete(ticket)

    for ticket in zenpy_client.search(status="open"):
        zenpy_client.tickets.delete(ticket)


def create_tickets():
    a = domain_models.MedicalPrescription.objects.filter(
        status=domain_models.MedicalPrescription.PATIENT_REQUESTED)

    for i in a:
        create_zendesk_ticket(i)
        print(i.id)


def recreate_tickets():
    delete_all_tickets()
    create_tickets()


def get_utc_from_bz(schedule):
    dst = PyBrDST()
    start, end = dst.get_dst(datetime.datetime.now().year)
    if start > schedule:
        start, end = dst.get_dst(datetime.datetime.now().year - 1)

    bz = pytz.timezone('America/Sao_Paulo')
    bt = datetime.datetime(*schedule.timetuple()[0:6], tzinfo=bz)
    fixed = pytz.utc.normalize(bt, True)

    #fix bug on pytz lib that is addind 6 minutes on the localization
    fixed = fixed - datetime.timedelta(minutes=6)

    print(fixed)

    if schedule > start and schedule < end:
        fixed = fixed - datetime.timedelta(hours=1)

    return datetime.datetime(*fixed.timetuple()[0:6])


def test_push(token):
    firebase = FirebaseCloudMessaging()
    response = firebase.send_push_notification(
        token, 'TESTE DE ENVIO', 'simples teste de envio {}'.format(
            datetime.datetime.now()), {'aaa': 'bbb'})
    print(response)


def create_adf_zendesk_tickets(instances):
    try:

        print('init adf creation')

        zenpy_client = Zenpy(**settings.ZENDESK)

        scs = ScheduledExam.objects.filter(id__in=instances)

        if not scs:
            print("No adf tickets to create")
            return

        onesc = scs.first()
        mp = onesc.prescription

        desc = """Data de abertura: {}
        Laboratório:{}
        Exames: {}
        """
        lab_name = onesc.laboratory.description if onesc.laboratory else ''
        print(desc)

        ticket = zenpy_client.tickets.create(
            Ticket(
                subject='Abertura de ficha para: {} no laboratório: {}'.format(
                    mp.patient.full_name, lab_name),
                requester=User(
                    name=mp.patient.full_name,
                    external_id=mp.patient.user.id,
                    email=mp.patient.user.email),
                type='task',
                status='open',
                priority='normal',
                due_at=onesc.scheduled_time,
                custom_fields=[
                    CustomField(id=114103586991, value='patient_requested'),
                    CustomField(id=114103769352, value=mp.patient.phone),
                    CustomField(id=114103769652, value=mp.patient.gender),
                    CustomField(
                        id=360002412071, value=onesc.scheduled_time.date())
                ],
                description=desc.format(
                    onesc.scheduled_time.strftime('%d/%m/%Y %H:%M'),
                    onesc.laboratory.description, ', '.join(
                        [i.exam.name for i in scs]))))

        et = ticket.ticket

        tdata = et.to_dict()
        del (tdata['via'])

        print(tdata)

        try:
            zticket = ZendeskASFTicket.objects.create(
                external_id=et.id, content=tdata)
        except Exception as e:
            print('*** {} ***'.format(e))
            print("Ticket for exams: {} already created".format(
                scs.values('id')))
            zticket = ZendeskASFTicket.objects.filter(
                external_id=et.id).first()
        print(zticket)

        et.external_id = zticket.id
        et.tags.extend([u'saracare', u'aberturadeficha'])

        ppieces = []

        for name, file in [
            ("RG frente", mp.picture_id_front_uploadcare.file
             if mp.picture_id_front_uploadcare else None),
            ("RG verso", mp.picture_id_back_uploadcare.file
             if mp.picture_id_back_uploadcare else None),
            ("Plano frente", mp.picture_insurance_card_front_uploadcare.file
             if mp.picture_insurance_card_front_uploadcare else None),
            ("Plano verso", mp.picture_insurance_card_back_uploadcare.file
             if mp.picture_insurance_card_back_uploadcare else None)
        ] + ppieces:

            if file:
                upload_instance = zenpy_client.attachments.upload(file)
                et.comment = Comment(
                    body=name, uploads=[upload_instance.token])
                zenpy_client.tickets.update(et)

        zenpy_client.tickets.update(et)
        scs.update(zendesk_adf_ticket=zticket)
    except Exception as e:
        print("Creation Error: {}".format(e))


def resend_notifications():
    start = datetime.datetime.strptime('2018-03-29 00:00:00',
                                       '%Y-%m-%d %H:%M:%S')
    zenpy_client = Zenpy(**settings.ZENDESK)

    presc = MedicalPrescription.objects.filter(
        status=MedicalPrescription.PATIENT_REQUESTED, created__gte=start)

    for p in presc:
        try:
            print(p)
            ticket = zenpy_client.tickets(id=p.zendeskticket.external_id)
            if ticket.status == 'solved':
                p.status = [
                    i.get('value') for i in ticket.custom_fields
                    if i.get('id') == 114103586991
                ][0].upper()
                if p.status == 'PATIENT_REQUESTED':
                    p.status = MedicalPrescription.UNREADABLE_PICTURES
                p.save()
                print('{}:{} - {}'.format(p.patient.user.email,
                                          p.patient.full_name, p.status))
        except Exception:
            print(p)


def reschedule_notifications():
    from domain.tasks import send_push_notification
    from domain.utils import grouped_exams_by_lab_date_keygen
    from datetime import timedelta
    
    scheduled_exams = domain_models.ScheduledExam.objects.filter(
        status=ScheduledExam.EXAM_TIME_SCHEDULED,
        scheduled_time__year=2018,
        scheduled_time__month=2
    )
    for instance in scheduled_exams:
        print(instance)
        first_name = instance.prescription.patient.full_name.split(" ")[0]
        exam_name = instance.exam.name
        expiration_date = instance.prescription.expiration_date

        subject, message, data = "", "", None
        scheduled_time = instance.scheduled_time
        if not scheduled_time:
            print('Scheduled time is null')
            return

        data = {"scheduled_exam_id": instance.id, "status": domain_models.ScheduledExam.EXAM_TIME_SCHEDULED,
                "scheduled_time": int(scheduled_time.timestamp()),  "exam_description": instance.exam.description,
                "is_scheduled_by_phone": instance.exam.is_scheduled_by_phone, "user_first_name": first_name}

        # if start_preparation_in_hours:
        # preparation_eta = scheduled_time - timedelta(hours=start_preparation_in_hours) - timedelta(minutes=settings.NOTIFICATION_BEFORE_EXAM_PREPARATION_IN_MINUTES)
        preparation_eta = scheduled_time - timedelta(days=settings.NOTIFICATION_BEFORE_EXAM_PREPARATION_IN_DAYS)
        preparation_eta = preparation_eta.replace(
            hour=settings.NOTIFICATION_EXACT_TIME_HOURS,
            minute=0,
            second=0,
            microsecond=0
        )

        preparation_future_subject = "Hora de começar a se preparar"
        preparation_future_message = "{0}, você precisa se preparar para seu exame. Vamos ver as instruções?".format(first_name)

        send_push_notification.apply_async(
            args=[instance.prescription.patient.token, preparation_future_subject, preparation_future_message, data],
            eta=preparation_eta,
        )

        eta = scheduled_time - timedelta(minutes=settings.NOTIFICATION_BEFORE_EXAM_IN_MINUTES)
        future_subject = "Você fez o preparo para o exame?"
        future_message = "{0}, toque para confirmar o preparo, ou para avisar que não pôde fazê-lo.".format(first_name)

        send_push_notification.apply_async(
            args=[instance.prescription.patient.token, future_subject, future_message, data],
            eta=eta,
        )

        if expiration_date:
            days = settings.NOTIFICATION_BEFORE_PRESCRIPTION_EXPIRES_IN_DAYS
            expiration_eta = expiration_date - timedelta(days=days)
            expiration_future_subject = "Seu pedido expira em {0} dias".format(days)
            expiration_future_message = "O pedido do exame {0} expira em {1} não esqueça de pedir para Sara fazer o agendamento.".format(
                exam_name,
                expiration_date.strftime('%d %B, %Y')
            )
            send_push_notification.apply_async(
                args=[instance.prescription.patient.token, expiration_future_subject, expiration_future_message, data],
                eta=expiration_eta,
            )

        subject = "Seu exame foi agendado"
        message = "{0}, toque para ver detalhes do exame.".format(first_name)
        if data:
            data.update({
                "exam_description": instance.exam.description,
                "is_scheduled_by_phone": instance.exam.is_scheduled_by_phone,
                "user_first_name": first_name
            })


        send_push_notification.apply_async(args=[instance.prescription.patient.token, subject, message, data], )
        print('sent: {}'.format(instance.prescription.patient.full_name))