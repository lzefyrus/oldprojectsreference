"""
Partner services
"""

from __future__ import absolute_import
from application.src.celeryapp import CeleryApp, Configs
from celery.exceptions import MaxRetriesExceededError
from lxml import etree
import requests
import time
import application.settings as settings

# Celery App
celery = CeleryApp.get_instance()

# Settings
partner_name = 'algar'
api_version = 'v1'
LOG_HASH = settings.LOG_HASHES[partner_name]


##########Notification##########
################################
@celery.task(base=Configs, name="algar.v1.partner.send_notification")
def notify(configs, headers, body, type):
    """
    Task which sends signature/authentication notification request to backend.

    :param configs: cached configs for notification on application.settings['config'] object
    :param headers: headers request
    :param body: json body request
    :return: None
    """

    # URL
    request_url = "{0}/{1}".format(configs["host"], configs["url"])

    # Notification Hash Code for log identification
    NOTIFICATION_HASH = LOG_HASH["{0}_notification".format(type)]

    response = None
    try:
        response = requests.post(request_url, headers=headers, json=body)
        notify.log.info("Notification request sent to backend. "
                        "Request URL: {0}."
                        "Request body: {1}."
                        "Request headers: {2}."
                        "Response body: {3}."
                        "Response code: {4}."
                        "Operation Hash: {5}."
                        .format(request_url, str(body).replace("\n", ""), headers, str(response.text).replace("\n", ""), response.status_code, NOTIFICATION_HASH))
    except Exception as e:
        response_text = None if response is None else str(response.text).replace("\n", "")
        response_code = None if response is None else response.status_code
        notify.log.error("Could not send Notification request to backend. "
                         "Request URL: {0}."
                         "Request body: {1}."
                         "Request headers: {2}."
                         "Response body: {3}."
                         "Response code: {4}."
                         "Error: {5}"
                         "Operation Hash: {6}."
                         .format(request_url, str(body).replace("\n", ""), headers, response_text, response_code, e, NOTIFICATION_HASH))
        try:
            notify.retry()
        except MaxRetriesExceededError:
            notify.apply_async(args=[configs, headers, body], queue='algar.v1.partner.send_notification.error')


def get_signature_configs(settings):
    """
    Gets cached configs for signature notification on application.settings['config'] object

    :param settings: Cache object application.settings['config']
    :return: json
    """

    return {
        'host': settings['config']['algar/v1/backend/host']['value'],
        'url': settings['config']['algar/v1/backend/url/notification/signature']['value'],
        'description_text': settings['config']['algar/v1/backend/notification/message']['value'],
        'description_error_text': settings['config']['algar/v1/backend/notification/error/message']['value'],
    }


def get_cancellation_configs(settings):
    """
    Gets cached configs for cancellation notification on application.settings['config'] object

    :param settings: Cache object application.settings['config']
    :return: json
    """

    return {
        'host': settings['config']['algar/v1/backend/host']['value'],
        'url': settings['config']['algar/v1/backend/url/notification/cancellation']['value'],
        'description_text': settings['config']['algar/v1/backend/notification/message']['value'],
        'description_error_text': settings['config']['algar/v1/backend/notification/error/message']['value'],
    }


def get_authentication_configs(settings):
    """
    Gets cached configs for authentication notification on application.settings['config'] object

    :param settings: Cache object application.settings['config']
    :return: json
    """

    return {
        'host': settings['config']['algar/v1/backend/host']['value'],
        'url': settings['config']['algar/v1/backend/url/notification/authentication']['value'],
        'description_text': settings['config']['algar/v1/backend/notification/message']['value'],
        'description_error_text': settings['config']['algar/v1/backend/notification/error/message']['value'],
    }


def get_notification_body(xml):
    """
    Parses xml body request to json

    :param xml: xml body received from algar
    :return: json
    """
    return {
        "status": xml.get("status"),
        "application_id": xml.get("application_id"),
        "dispatcher_id": xml.find('dispatcher_id').text,
        "message_id": xml.find('message_id').text,
        "smsc_message_id": xml.find('smsc_message_id').text,
        "source": xml.find('source').text,
        "destination": xml.find('destination').text,
        "request_datetime": xml.find('request_datetime').text,
        "notification_datetime": xml.find('notification_datetime').text,
        "app_specific_id": xml.find('app_specific_id').text,
        "description": xml.find('description').text
    }


def get_notification_response(text, json, ack, status_code):
    """
    Parses json to xml in order to respond algar's request

    :param text: description text
    :param json: json sent to backend
    :param ack: message's arrival acknowledgement
    :param status_code: request status code
    :return: xml
    """

    body = etree.Element('notification_response', ack=str(ack), version="1")
    message_id = etree.SubElement(body, "message_id")
    message_id.text = json['message_id']
    description = etree.SubElement(body, "description", code=str(status_code))
    description.text = str(text)

    return etree.tounicode(body)


def get_notification_error_response(text, ack, status_code):
    """
    Builds xml return in case of error (status_code <> 200)

    :param text: error description
    :param ack: message's arrival acknowledgement
    :param status_code: request status code
    :return: xml
    """

    body = etree.Element('notification_response', ack=str(ack), version="1")
    message_id = etree.SubElement(body, "message_id")
    description = etree.SubElement(body, "description", code=str(status_code))
    description.text = str(text)

    return etree.tounicode(body)


##########MO##########
######################
@celery.task(base=Configs, name="algar.v1.partner.send_mo")
def send_mo(configs, headers, body):
    """
    Task which sends MO request to backend.

    :param configs: cached configs for MO on application.settings['config'] object
    :param headers: headers request
    :param body: json body request
    :return: None
    """

    # URL
    request_url = "{0}/{1}".format(configs["host"], configs["url"])

    # MO Hash Code for log identification
    MO_HASH = LOG_HASH["mo"]

    response = None
    try:
        response = requests.post(request_url, headers=headers, json=body)
        send_mo.log.info("MO request sent to backend. "
                         "Request URL: {0}."
                         "Request body: {1}."
                         "Request headers: {2}."
                         "Response body: {3}."
                         "Response code: {4}."
                         "Operation Hash: {5}."
                         .format(request_url, str(body).replace("\n", ""), headers, str(response.text).replace("\n", ""), response.status_code, MO_HASH))
    except Exception as e:
        response_text = None if response is None else str(response.text).replace("\n", "")
        response_code = None if response is None else response.status_code
        send_mo.log.error("Could not send MO request to backend. "
                          "Request URL: {0}."
                          "Request body: {1}."
                          "Request headers: {2}."
                          "Response body: {3}."
                          "Response code: {4}."
                          "Error: {5}"
                          "Operation Hash: {6}."
                          .format(request_url, str(body).replace("\n", ""), headers, response_text, response_code, e, MO_HASH))
        try:
            send_mo.retry()
        except MaxRetriesExceededError:
            send_mo.apply_async(args=[configs, headers, body], queue='algar.v1.partner.send_mo.error')


def get_mo_configs(settings):
    """
    Gets cached configs for MO on application.settings['config'] object

    :param settings: Cache object application.settings['config']
    :return: json
    """
    return {
        'host': settings['config']['algar/v1/backend/host']['value'],
        'url': settings['config']['algar/v1/backend/mo/url']['value'],
        'ack': settings['config']['algar/v1/mo/ack']['value'],
        'is_billing': settings['config']['algar/v1/mo/is_billing']['value'],
        'keep_session': settings['config']['algar/v1/mo/keep_session']['value'],
        'description_code': settings['config']['algar/v1/mo/description/code']['value'],
        'description_text': settings['config']['algar/v1/mo/description/text']['value'],
        'fail_description_text': settings['config']['algar/v1/mo/fail/description/text']['value'],
    }


def get_mo_body(xml):
    """
    Parses xml body request to json

    :param xml: xml body received from algar
    :return: json
    """
    return {
        "company_id": xml.get('company_id'),
        "service_id": xml.get('service_id'),
        "carrier_id": xml.find('carrier_id').text,
        "dispatcher_id": xml.find('dispatcher_id').text,
        "message_id": xml.find('message_id').text,
        "application_id": xml.find('application_id').text,
        "large_account": xml.find('large_account').text,
        "source": xml.find('source').text,
        "request_datetime": xml.find('request_datetime').text,
        "text": xml.find('text').text
    }


def get_mo_response(configs, json):
    """
    Parses json to xml in order to respond algar's request

    :param configs: cached configs for MO on application.settings['config'] object
    :param json: json sent to backend
    :return: xml
    """
    
    body = etree.Element('smsmo_response', ack=str(configs['ack']), billing=str(configs['is_billing']),
                         keep_session=str(configs['keep_session']))
    message_id = etree.SubElement(body, "message_id")
    message_id.text = json['message_id']
    source = etree.SubElement(body, "source")
    source.text = json['source']
    large_account = etree.SubElement(body, "large_account")
    large_account.text = json['large_account']
    response_datetime = etree.SubElement(body, "request_datetime")
    response_datetime.text = str(int(time.time()))
    send = etree.SubElement(body, 'send')
    text = etree.SubElement(send, 'text')
    text.text = json['text']
    description = etree.SubElement(body, "description", code=str(configs['description_code']))
    description.text = str(configs['description_text'])

    return etree.tounicode(body)


def get_mo_fail_response(text, ack, status_code):
    """
    Builds xml return in case of error (status_code <> 200)

    :param text: error description
    :param ack: message's arrival acknowledgement
    :param status_code: request status code
    :return: xml
    """
    
    body = etree.Element('smsmo_response', ack=str(ack))
    message_id = etree.SubElement(body, "message_id")
    source = etree.SubElement(body, "source")
    large_account = etree.SubElement(body, "large_account")
    response_datetime = etree.SubElement(body, "request_datetime")
    description = etree.SubElement(body, "description", code=str(status_code))
    description.text = str(text)

    return etree.tounicode(body)


##########GENERAL#####
######################
def prepare_xml(xml):
    return xml.replace("\n", "")\
              .replace("""<?xml version="1.0" encoding="UTF-8"?>""", "")\
              .replace("""<?xml version="1.0" encoding="ISO-8859-1"?>""", "")
