"""
Partner services
"""

from __future__ import absolute_import
from application.src.celeryapp import CeleryApp, Configs
from celery.exceptions import MaxRetriesExceededError
import application.settings as settings
import requests


# Celery App
celery = CeleryApp.get_instance()
# Settings
partner_name = 'claro'
api_version = 'v1'
LOG_HASH = settings.LOG_HASHES[partner_name]


##########MT Notification##########
###################################
@celery.task(base=Configs, name="claro.v1.partner.send_mt_notification")
def notify_mt(configs, headers, body):
    # URL
    request_url = "{0}/{1}".format(configs["host"], configs["url"])

    # MT Notification Hash Code for log identification
    MT_NOTIFICATION_HASH = LOG_HASH["mt_notification"]

    try:
        response = requests.post(request_url, headers=headers, data=body)
        notify_mt.log.info("MT Notification request sent to backend. "
                           "Request URL: {0}."
                           "Request body: {1}."
                           "Request headers: {2}."
                           "Response body: {3}."
                           "Response code: {4}."
                           "Operation Hash: {5}."
                           .format(request_url, body, headers, response.text,
                                   response.status_code, MT_NOTIFICATION_HASH))
    except Exception as e:
        notify_mt.log.error("Could not send MT Notification request to backend. "
                            "Request URL: {0}."
                            "Request body: {1}."
                            "Error: {2}."
                            "Operation Hash: {3}."
                            .format(request_url, body, e, MT_NOTIFICATION_HASH))
        try:
            notify_mt.retry()
        except MaxRetriesExceededError:
            notify_mt.apply_async(args=[configs, headers, body], queue='claro.v1.partner.send_mt_notification.error')


def get_mt_notification_configs(settings):
    return {
        "host": settings['config']['claro/v1/backend/host']['value'],
        "url": settings['config']['claro/v1/backend/notification/mt/url']['value']
    }


##########MMS MT Notification##########
#######################################
@celery.task(base=Configs, name="claro.v1.partner.send_mms_mt_notification")
def notify_mms_mt(configs, headers, body):
    # URL
    request_url = "{0}/{1}".format(configs["host"], configs["url"])

    # MMS MT Notification Hash Code for log identification
    MMS_MT_NOTIFICATION_HASH = LOG_HASH["mms_mt_notification"]

    try:
        response = requests.post(request_url, headers=headers, data=body)
        notify_mms_mt.log.info("MMS Notification request sent to backend. "
                               "Request URL: {0}."
                               "Request body: {1}."
                               "Request headers: {2}."
                               "Response body: {3}."
                               "Response code: {4}."
                               "Operation Hash: {5}."
                               .format(request_url, body, headers, response.text,
                                       response.status_code, MMS_MT_NOTIFICATION_HASH))
    except Exception as e:
        notify_mms_mt.log.error("Could not send MMS Notification request to backend. "
                                "Request URL: {0}."
                                "Request body: {1}."
                                "Error: {2}."
                                "Operation Hash: {3}."
                                .format(request_url, body, e, MMS_MT_NOTIFICATION_HASH))
        try:
            notify_mms_mt.retry()
        except MaxRetriesExceededError:
            notify_mms_mt.apply_async(args=[configs, headers, body], queue='claro.v1.partner.send_mms_mt_notification.error')


def get_mms_mt_notification_configs(settings):
    return {
        "host": settings['config']['claro/v1/backend/host']['value'],
        "url": settings['config']['claro/v1/backend/notification/mms/url']['value']
    }


##########WAP MT Notification######
###################################
@celery.task(base=Configs, name="claro.v1.partner.send_wap_mt_notification")
def notify_wap_mt(configs, headers, body):
    # URL
    request_url = "{0}/{1}".format(configs["host"], configs["url"])

    # WAP MT Notification Hash Code for log identification
    WAP_MT_NOTIFICATION_HASH = LOG_HASH["wap_mt_notification"]

    try:
        response = requests.post(request_url, headers=headers, data=body)
        notify_wap_mt.log.info("WAP Notification request sent to backend. "
                               "Request URL: {0}."
                               "Request body: {1}."
                               "Request headers: {2}."
                               "Response body: {3}."
                               "Response code: {4}."
                               "Operation Hash: {5}."
                               .format(request_url, body, headers, response.text,
                                       response.status_code, WAP_MT_NOTIFICATION_HASH))
    except Exception as e:
        notify_wap_mt.log.error("Could not send WAP Notification request to backend. "
                                "Request URL: {0}."
                                "Request body: {1}."
                                "Error: {2}."
                                "Operation Hash: {3}."
                                .format(request_url, body, e, WAP_MT_NOTIFICATION_HASH))
        try:
            notify_wap_mt.retry()
        except MaxRetriesExceededError:
            notify_wap_mt.apply_async(args=[configs, headers, body], queue='claro.v1.partner.send_wap_mt_notification.error')


def get_wap_mt_notification_configs(settings):
    return {
        "host": settings['config']['claro/v1/backend/host']['value'],
        "url": settings['config']['claro/v1/backend/notification/wap/url']['value']
    }


##########WIB PUSH Notification######
#####################################
@celery.task(base=Configs, name="claro.v1.partner.send_wib_push_notification")
def notify_wib_push(configs, headers, body):
    # URL
    request_url = "{0}/{1}".format(configs["host"], configs["url"])

    # Wib Push Notification Hash Code for log identification
    WIB_PUSH_NOTIFICATION_HASH = LOG_HASH["wib_push_notification"]

    try:
        response = requests.post(request_url, headers=headers, data=body)
        notify_wib_push.log.info("WIB PUSH Notification request sent to backend. "
                                 "Request URL: {0}."
                                 "Request body: {1}."
                                 "Request headers: {2}."
                                 "Response body: {3}."
                                 "Response code: {4}."
                                 "Operation Hash: {5}."
                                 .format(request_url, body, headers, response.text,
                                         response.status_code, WIB_PUSH_NOTIFICATION_HASH))
    except Exception as e:
        notify_wib_push.log.error("Could not send WIB PUSH Notification request to backend. "
                                  "Request URL: {0}."
                                  "Request body: {1}."
                                  "Error: {2}."
                                  "Operation Hash: {3}."
                                  .format(request_url, body, e, WIB_PUSH_NOTIFICATION_HASH))
        try:
            notify_wib_push.retry()
        except MaxRetriesExceededError:
            notify_wib_push.apply_async(args=[configs, headers, body], queue='claro.v1.partner.send_wib_push_notification.error')


def get_wib_push_notification_configs(settings):
    return {
        "host": settings['config']['claro/v1/backend/host']['value'],
        "url": settings['config']['claro/v1/backend/notification/wib-push/url']['value']
    }


##########MO######
##################
@celery.task(base=Configs, name="claro.v1.partner.send_mo")
def send_mo(configs, headers, body):
    # URL
    request_url = "{0}/{1}".format(configs["host"], configs["url"])

    # MO Hash Code for log identification
    MO_HASH = LOG_HASH["mo"]

    try:
        response = requests.post(request_url, headers=headers, data=body)
        send_mo.log.info("MO request sent to backend. "
                         "Request URL: {0}."
                         "Request body: {1}."
                         "Request headers: {2}."
                         "Response body: {3}."
                         "Response code: {4}."
                         "Operation Hash: {5}."
                         .format(request_url, body, headers, response.text,
                                 response.status_code, MO_HASH))
    except Exception as e:
        send_mo.log.error("Could not send MO request to backend. "
                          "Request URL: {0}."
                          "Request body: {1}."
                          "Error: {2}."
                          "Operation Hash: {3}."
                          .format(request_url, body, e, MO_HASH))
        try:
            send_mo.retry()
        except MaxRetriesExceededError:
            send_mo.apply_async(args=[configs, headers, body], queue='claro.v1.partner.send_mo.error')


def get_mo_configs(settings):
    return {
        "host": settings['config']['claro/v1/backend/host']['value'],
        "url": settings['config']['claro/v1/backend/mo/url']['value']
    }


def get_mo_body(text, id, msisdn, la):
    return {
        "text": text,
        "transaction_id": id,
        "msisdn": msisdn,
        "la": la
    }


##########MMS MO######
######################
@celery.task(base=Configs, name="claro.v1.partner.send_mms_mo")
def send_mms_mo(configs, headers, body):
    # URL
    request_url = "{0}/{1}".format(configs["host"], configs["url"])

    # MO Hash Code for log identification
    MMS_MO_HASH = LOG_HASH["mms_mo"]

    try:
        response = requests.post(request_url, headers=headers, data=body)
        send_mms_mo.log.info("MMS MO request sent to backend. "
                             "Request URL: {0}."
                             "Request body: {1}."
                             "Request headers: {2}."
                             "Response body: {3}."
                             "Response code: {4}."
                             "Operation Hash: {5}."
                             .format(request_url, body, headers, response.text,
                                     response.status_code, MMS_MO_HASH))
    except Exception as e:
        send_mms_mo.log.error("Could not send MMS MO request to backend. "
                              "Request URL: {0}."
                              "Request body: {1}."
                              "Error: {2}."
                              "Operation Hash: {3}."
                              .format(request_url, body, e, MMS_MO_HASH))
        try:
            send_mms_mo.retry()
        except MaxRetriesExceededError:
            send_mms_mo.apply_async(args=[configs, headers, body], queue='claro.v1.partner.send_mms_mo.error')


def get_mms_mo_configs(settings):
    return {
        "host": settings['config']['claro/v1/backend/host']['value'],
        "url": settings['config']['claro/v1/backend/mo/mms/url']['value']
    }


def get_mms_mo_body(xml_response):
    return {
        "transaction_id": xml_response.find("MSG").get('MSG_ID'),
        "msisdn": xml_response.find("ANUM").text,
        "la": xml_response.find("BNUM").text,
        "mms": xml_response.find("MMS").text
    }
