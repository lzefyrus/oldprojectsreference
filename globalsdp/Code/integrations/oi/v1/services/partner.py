"""
Partner services
"""

from __future__ import absolute_import
from application.src.celeryapp import CeleryApp, Configs
from urllib.parse import quote_plus
from celery.exceptions import MaxRetriesExceededError
import application.settings as settings
import requests
import json
import datetime
import time

# Celery App
celery = CeleryApp.get_instance()
LOG_HASH = settings.LOG_HASHES["oi"]


@celery.task(base=Configs, name="oi.v1.partner.send_mo_async")
def send_mo(configs, from_, to, text, mo_id, date):
    """
    Task which sends MO request to backend.

    :param configs: cached configs for notification on application.settings['config'] object
    :param from_: msisdn (telephone number)
    :param to: Large Account number (LA)
    :param text: Message text
    :param mo_id: Message Id
    :param date: Message date
    :return: None
    """

    send_mo.log.info("MO request INIT inside worker. "
                     "From: {0}. "
                     "To: {1}. "
                     "Text: {2}. "
                     "MO_ID: {3}. "
                     "MO_Date: {4}. "
                     .format(from_, to, text, mo_id, date).replace('\n',' '))

    # MO Hash Code for log identification
    MO_HASH = None
    try:
        MO_HASH = LOG_HASH["mo"]
    except:
        pass

    try:
        # Configs
        las_fs_entertainment = json.loads(configs['las_fs_entertainment'])
        is_entertainment = int(to) in las_fs_entertainment
        host = configs['host_fs_entertainment'] if is_entertainment else configs['host_fs']
        url = configs['url_fs_entertainment'] if is_entertainment else configs['url_fs']

        # Requested URL
        url = "{0}/{1}/?".format(host, url)
        parameters = "from={0}&to={1}&text={2}&mo_id={3}&date={4}".format(
            quote_plus(from_.encode('utf-8')),
            quote_plus(to.encode('utf-8')),
            quote_plus(text.encode('utf-8')),
            quote_plus(mo_id.encode('utf-8')),
            quote_plus(date.encode('utf-8'))
        )
        request_url = url + parameters

        now = time.time()
        try:
            # 10s of timeout requested By Bruno From Sorte7
            response = requests.get(request_url, timeout=10)

            status_code = None
            if response and response.status_code:
                status_code = response.status_code

            response_text = None
            if response and response.text:
                response_text = response.text

            if status_code == 200:
                return send_mo.log.info("MO request sent to backend. "
                                        "Request URL: {0}. "
                                        "Response code: {1}. "
                                        "Response body: {2}. "
                                        "Response time: {3}. "
                                        "Operation Hash: {4}"
                                        .format(request_url, status_code, response_text, time.time() - now, MO_HASH).replace('\n',' '))

            send_mo.log.error("Could not send MO. "
                              "Request URL: {0}. "
                              "Response code: {1}. "
                              "Response body: {2}. "
                              "Response time: {3}. "
                              "Operation Hash: {4}"
                              .format(request_url, status_code, response_text, time.time() - now, MO_HASH).replace('\n',' '))

        except Exception as e:
            send_mo.log.error("Could not send MO. "
                              "Request URL: {0}. "
                              "Error: {1}. "
                              "Response time: {2}. "
                              "Operation Hash: {3}"
                              .format(request_url, e, time.time() - now, MO_HASH).replace('\n',' '))
            requeue(send_mo, configs, from_, to, text, mo_id, date)

    except Exception as e:
        send_mo.log.error("Could not send MO. "
                          "From: {0}. "
                          "To: {1}. "
                          "Text: {2}. "
                          "Error: {3}. "
                          "Operation Hash: {4}"
                          .format(str(from_), str(to), str(text), e, MO_HASH).replace('\n',' '))

        requeue(send_mo, configs, from_, to, text, mo_id, date)


def requeue(task, configs, from_, to, text, mo_id, date):
    """
    Retry task execution. If MaxRetriesExceededError, then send task to an error queue

    :param task:
    :param configs: cached configs for notification on application.settings['config'] object
    :param from_: msisdn (telephone number)
    :param to: Large Account number (LA)
    :param text: Message text
    :param mo_id: Message Id
    :param date: Message date
    :return: None
    """

    try:
        task.retry()

    except MaxRetriesExceededError:
        # Current date sample: 2016-01-26
        current_date = str(datetime.datetime.now()).split(' ')[0]

        task.apply_async(
            args=[configs, from_, to, text, mo_id, date],
            queue='{0}_oi_mo_error'.format(current_date),
            serializer=settings.CELERY_SERIALIZATION)


def get_configs(settings):
    """
    Gets cached configs for MO on application.settings['config'] object

    :param settings: Cache object application.settings['config']
    :return: json
    """
    return {
            'host_fs_entertainment': settings['config']['oi/v1/backend/host/fs-entertainment']['value'],
            'url_fs_entertainment': settings['config']['oi/v1/backend/mo/url/fs-entertainment']['value'],
            'las_fs_entertainment': settings['config']['oi/v1/fs-entertainment/las']['value'],
            'host_fs': settings['config']['oi/v1/backend/host/fs']['value'],
            'url_fs': settings['config']['oi/v1/backend/mo/url/fs']['value'],
        }
