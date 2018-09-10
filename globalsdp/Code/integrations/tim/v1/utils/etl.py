from functools import wraps
from application.src.celeryapp import CeleryApp, Configs
from application.src import databases
from application.src.models import EtlTimV1Recharge as Recharge
from lxml import etree
from datetime import datetime
from celery.exceptions import MaxRetriesExceededError
import application.settings as settings
import requests
import logging

# DB
db = databases.DB().get_instance()

# Logging handler
log = logging.getLogger(__name__)

# Celery App
celery = CeleryApp.get_instance()


def etl(func):
    """
    Saves incoming recharge requests as columns to database.
    """
    @wraps(func)
    def with_requests(self, *args):
        try:
            etl_recharge_async.apply_async(
                args=[args, datetime.now()],
                queue=settings.CELERY_ROUTES['integrations.tim.v1.utils.etl.recharge.async']['queue'],
                serializer=settings.CELERY_SERIALIZATION
            )
        except Exception as e:
            log.error(e)

        return func(self, *args)
    return with_requests


@celery.task(base=Configs, name="integrations.tim.v1.utils.etl.recharge.async")
def etl_recharge_async(args, date):
    """
    Saves incoming recharge requests as columns asynchronously.
    This feature uses pymysql due to performance.
    :param args:
    :param date:
    :return:
    """
    try:
        #  REMOVE AFTER ERROR QUEUE CONSUMED
        if isinstance(args, str):
            # XML
            body = args
            body = body.\
                    replace('soapenv:', '').\
                    replace('xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"', "").\
                    replace('xmlns="http://webservices.accenture.com/wsnotificacaorecarga/entities"', "").\
                    encode('utf-8')

            xml = etree.XML(bytes(body))
            body = xml.find('Body')
            params = body.find('data')

            # Recharge
            recharge = Recharge(
                event_id=params.find('event-id').text,
                msisdn=params.find('msisdn').text,
                partner_id=params.find('partner-id').text,
                value=params.find('value').text,
                date=params.find('date').text,
                time=params.find('time').text,
                tariff_id=params.find('tariff-id').text,
                subsys=params.find('subsys').text,
            )
        #  REMOVE AFTER ERROR QUEUE CONSUMED
        else:
            # Recharge
            recharge = Recharge(
                event_id=args[0],
                msisdn=args[1],
                partner_id=args[2],
                value=args[3],
                date=args[4],
                time=args[5],
                tariff_id=args[6],
                subsys=args[7],
            )

        # Request to MT API
        try:
            """
                Workaround: hard coded requested by Sandro.
            """
            requests.post(
                url="http://10.170.224.99/tim",
                data={
                    "price": recharge.value,
                    "phone": recharge.msisdn
                }
            )
        except Exception as e:
            pass

        # Save to database
        with etl_recharge_async.pymysql.cursor() as cursor:
            insert = "INSERT INTO etl_tim_v1_recharge (event_id, msisdn, partner_id, value, date, time, tariff_id," \
                     "subsys, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
            values = (recharge.event_id, recharge.msisdn, recharge.partner_id, recharge.value, recharge.date,
                      recharge.time, recharge.tariff_id, recharge.subsys, date)
            cursor.execute(insert, values)

    except Exception as e:
        log.error('Error on saving recharge ETL request: {0}'.format(e))
        try:
            etl_recharge_async.retry()
        except MaxRetriesExceededError:
            etl_recharge_async.apply_async(
                args=[args, date],
                queue='integrations.tim.v1.utils.etl.recharge.async.error'
            )
