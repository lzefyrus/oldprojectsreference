from application.src.rewrites import APIHandler
from tornado.escape import json_decode
from integrations.tim.v1.services import partner as PartnerService
from integrations.tim.v1.validators.partner import validate_notification, validate_mo
from application.src.request import request
from application.src import utils
import application.settings as settings
import logging

partner_name = 'tim'
api_version = 'v1'

# Logging handler
log = logging.getLogger(__name__)


class NotificationHandler(APIHandler):
    __urls__ = [r"/{0}/{1}/notification".format(partner_name, api_version),
                r"/{0}/{1}/notification/".format(partner_name, api_version)]

    @request
    @validate_notification
    def post(self):
        # Getting body
        body = json_decode(self.request.body)
        subscription = body['subscriptionNotification']
        subscription_id = subscription['subscriptionId']
        application_name = subscription['applicationName']
        subscriber_address = subscription['subscriberAddress']

        # Getting headers
        try:
            headers = utils.get_headers(self.request.headers, filter=['Content-Type', 'Clientcorrelator'])
        except:
            headers = None

        # Getting clientCorrelator
        try:
            client_correlator = headers["Clientcorrelator"]
        except:
            client_correlator = None

        # Getting configs
        configs = {
            'host': self.application.settings['config']['tim/v1/backend/host']['value'],
            'url': self.application.settings['config']['tim/v1/backend/notification/url']['value'],
        }

        # Processing request asynchronously
        try:
            # PartnerService.send_notification.delay(configs, headers, self.request.body, client_correlator)
            task = PartnerService.send_notification.apply_async(
                args=[configs, headers, self.request.body, client_correlator],
                queue=settings.CELERY_ROUTES['tim.v1.partner.send_notification']['queue'],
                serializer=settings.CELERY_SERIALIZATION
            )

            log.info("Notification request successfully queued: "
                     "Headers: {0}. "
                     "Body: {1}. "
                     "ClientCorrelator: {2}. "
                     "Task Id: {3}. "
                     "Task Name: {4}. "
                     .format(headers, self.request.body, client_correlator, task.task_id, task.task_name)
                     )

            return self.success({"status": "OK", "message": "Unsubscribe {0} successfully queued."
                                .format(subscription_id)})
        except Exception as e:
            return self.error({"status": "NOK", "message": "Could not send request. Internal error."}, 500)


class MoHandler(APIHandler):
    __urls__ = [r"/{0}/{1}/mo".format(partner_name, api_version),
                r"/{0}/{1}/mo/".format(partner_name, api_version)]

    @request
    @validate_mo
    def post(self):
        # Getting body
        body = json_decode(self.request.body)
        help_notification = body['helpNotification']
        subscriber = help_notification['subscriber']
        subscriber_message = help_notification['subscriberMessage']
        short_code = help_notification['shortCode']

        # Getting headers
        try:
            headers = utils.get_headers(self.request.headers, filter=['Content-Type', 'Clientcorrelator'])
        except:
            headers = None

        # Getting clientCorrelator
        try:
            client_correlator = headers["Clientcorrelator"]
        except:
            client_correlator = None

        # Getting configs
        configs = {
            'host': self.application.settings['config']['tim/v1/backend/host']['value'],
            'url': self.application.settings['config']['tim/v1/backend/mo/url']['value'],
        }

        # Processing request asynchronously
        try:
            # PartnerService.send_mo.delay(configs, headers, self.request.body, client_correlator)
            task = PartnerService.send_mo.apply_async(
                args=[configs, headers, self.request.body, client_correlator],
                queue=settings.CELERY_ROUTES['tim.v1.partner.send_mo']['queue'],
                serializer=settings.CELERY_SERIALIZATION
            )

            log.info("MO request successfully queued: "
                     "Headers: {0}. "
                     "Body: {1}. "
                     "ClientCorrelator: {2}. "
                     "Task Id: {3}. "
                     "Task Name: {4}. "
                     .format(headers, self.request.body, client_correlator, task.task_id, task.task_name)
                     )
            return self.success({"status": "OK", "message": "Help '{0}' successfully sent to {1}."
                                .format(subscriber_message, subscriber)})
        except Exception as e:
            return self.error({"status": "NOK", "message": "Could not send request. Internal error."}, 500)
