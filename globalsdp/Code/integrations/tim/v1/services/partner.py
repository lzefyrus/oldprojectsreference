"""
Partner services
"""

from __future__ import absolute_import
from tornado.escape import json_decode, json_encode
import requests
import os
from application.src.celeryapp import CeleryApp, Configs
from celery.exceptions import MaxRetriesExceededError

# Celery App
celery = CeleryApp.get_instance()


@celery.task(base=Configs, name="tim.v1.partner.send_notification")
def send_notification(configs, headers, body, client_correlator=None):
    try:
        request_url = "{0}/{1}".format(configs["host"], configs["url"])

        # Injecting client_correlator inside the body
        body = json_decode(body)
        body['subscriptionNotification']['clientCorrelator'] = client_correlator
        body = json_encode(body)

        response = requests.post(request_url, body, headers=headers, verify=False)

        if response.status_code == 200 or response.status_code == 201:
            return send_notification.log.info("Notification request sent to backend. "
                                              "Request URL: {0}. Request body: {1}. Request headers: {2}. "
                                              "Response body: {3}. Response code: {4}. "
                                              .format(request_url, body, headers, response.text, response.status_code))

        send_notification.log.error("Error on send Notification request to backend. "
                                    "Request URL: {0}. Request body: {1}. Request headers: {2}. "
                                    "Response body: {3}. Response code: {4}. "
                                    .format(request_url, body, headers, response.text, response.status_code))

    except Exception as e:
        send_notification.log.error("Could not send Notification request to backend. "
                                    "Request URL: {0}. Request body: {1}. Request headers: {2}. "
                                    "Error: {3}. "
                                    .format(request_url, body, headers, e))

        # Retry in case of error
        try:
            send_notification.retry()
        except MaxRetriesExceededError:
            send_notification.apply_async(
                args=[configs, headers, body, client_correlator],
                queue='tim.v1.partner.send_notification.error'
            )


@celery.task(base=Configs, name="tim.v1.partner.send_mo")
def send_mo(configs, headers, body, client_correlator=None):
    try:
        request_url = "{0}/{1}".format(configs["host"], configs["url"])
        body = _replace_la(body)

        # Injecting client_correlator inside the body
        body = json_decode(body)
        body['helpNotification']['clientCorrelator'] = client_correlator
        body = json_encode(body)

        response = requests.post(request_url, body, headers=headers, verify=False)

        if response.status_code == 200 or response.status_code == 201:
            return send_mo.log.info("MO request sent to backend. "
                                    "Request URL: {0}. Request body: {1}. Request headers: {2} "
                                    "Response body: {3}. Response code: {4}"
                                    .format(request_url, body, headers, response.text, response.status_code))

        send_mo.log.error("Error on send MO to backend. "
                          "Request URL: {0}. Request body: {1}. Request headers: {2} "
                          "Response body: {3}. Response code: {4}"
                          .format(request_url, body, headers, response.text, response.status_code))

    except Exception as e:
        send_mo.log.error("Could not send MO request to backend. "
                          "Request URL: {0}. Request body: {1}. Request headers: {2} "
                          "Error: {3}"
                          .format(request_url, body, headers, e))

        # Retry in case of error
        try:
            send_mo.retry()
        except MaxRetriesExceededError:
            send_mo.apply_async(
                args=[configs, headers, body, client_correlator],
                queue='tim.v1.partner.send_mo.error'
            )


def _replace_la(body):
    if os.environ['GATEWAY_ENV'] == 'prod':
        return body

    body = json_decode(body)

    if body['helpNotification']['shortCode'] == '323':

        body['helpNotification']['shortCode'] = '5511'
        # body['helpNotification']['shortCode'] = '5512'
        # body['helpNotification']['shortCode'] = '5515'

    if body['helpNotification']['shortCode'] == '324':
        body['helpNotification']['shortCode'] = '5503'

    return json_encode(body)
