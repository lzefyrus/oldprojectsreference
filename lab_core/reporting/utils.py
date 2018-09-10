import datetime
import json
from functools import wraps

from reversion.models import Version

from domain.models import ScheduledExam, MedicalPrescription
from .models import GeneralStatus
from django.contrib.contenttypes.models import ContentType



def status_history():
    def wrapper(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            try:
                model = kwargs.get('sender')
                actual = kwargs.get('instance')
                add_historical_version(actual, model)

            except Exception as e:
                print(actual)

            finally:
                return f(*args, **kwargs)

        return wrapped

    return wrapper


def add_historical_version(actual, model):
    contenttype = 0
    exam = None
    total_time = 0
    pid = None
    MEDICALPRESCRIPTION__ID = ContentType.objects.get(app_label='domain', model='medicalprescription').id
    SCHEDULEDEXAM__ID = ContentType.objects.get(app_label='domain', model='scheduledexam').id


    if isinstance(actual, dict):
        actual_id = actual.get('pk')
        mod = actual.get("modified")
        actual_modified = datetime.datetime.strptime(mod, "%Y-%m-%dT%H:%M:%S.%fZ") if mod[
                                                                                          -1] == 'Z' else datetime.datetime.strptime(
            mod, "%Y-%m-%dT%H:%M:%S.%f")
        actual_status = actual.get('status')
        actual_prescription = actual.get('prescription')
    else:
        actual_id = actual.id
        actual_modified = actual.modified
        actual_status = actual.status
        actual_prescription = actual.prescription.id
        
    if model in [ScheduledExam, SCHEDULEDEXAM__ID]:
        contenttype = SCHEDULEDEXAM__ID
        prescription = actual_prescription
        exam = actual_id
    elif model in [MedicalPrescription, MEDICALPRESCRIPTION__ID]:
        contenttype = MEDICALPRESCRIPTION__ID
        prescription = actual_id

    previous = get_previous_revision(contenttype, actual_prescription, exam)

    if previous:
        total_time = actual_modified - previous.date_set
        total_time = total_time.total_seconds()
        pid = previous.pk

    gs = GeneralStatus(content_type_id=contenttype,
                       date_set=actual_modified,
                       status=actual_status,
                       prescription_id=prescription,
                       exam_id=exam,
                       parent_id=pid,
                       ttl=total_time
                       )
    gs.save()


def get_previous_revision(content_type_id, prescription_id, exam_id):
    """
    Retrieve the previous item of the status revision
    :param content_type_id: int
    :param pk: int
    :return: int
    """

    if not exam_id:
        return GeneralStatus.objects.filter(prescription_id=prescription_id,
                                            exam_id__isnull=True,
                                            content_type_id=content_type_id).order_by("-date_set").last()

    return GeneralStatus.objects.filter(prescription_id=prescription_id,
                                        exam_id=exam_id,
                                        content_type_id=content_type_id).order_by("-date_set").last()



def populate():
    """
    iterate over the revision table and populate GS table
    :return:
    """
    start = datetime.datetime.strptime('2017-07-01T00:00:00', '%Y-%m-%dT%H:%M:%S')

    p_ids = MedicalPrescription.objects.all().only('id')
    s_ids = ScheduledExam.objects.all().only('id')

    import time
    version_items = Version.objects.filter(revision__date_created__gte=start).order_by('id')
    for version_item in version_items:
        try:
            time.sleep(0.1)
            version_item_data = json.loads(version_item.serialized_data)[0]
            fields = version_item_data['fields']
            fields['pk'] = version_item_data['pk']
            add_historical_version(fields, version_item.content_type.pk)
            print(fields['pk'])

        except Exception as e:
            print(e)

    return
