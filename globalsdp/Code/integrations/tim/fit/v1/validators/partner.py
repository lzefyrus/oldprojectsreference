from functools import wraps
from tornado.escape import json_decode
import logging

# Logging handler
log = logging.getLogger(__name__)


def validate_notification(func):
    """
    Validates Tim notification (Subscribe/ Unsubscribe) request (mandatory params only)
    """
    @wraps(func)
    def with_notification(self):
        # Validating body
        try:
            body = json_decode(self.request.body)
        except Exception as e:
            log.error("Invalid JSON object: {0}".format(e))
            return self.error({"status": "NOK", "message": "Invalid JSON object"})

        error_list = []
        try:
            subscription = body['subscriptionNotification']
        except KeyError:
            log.error("Missing mandatory parameter: subscriptionNotification")
            return self.error({"status": "NOK", "message": "Missing mandatory parameter: subscriptionNotification"})
        try:
            subscription_id = subscription['subscriptionId']
        except KeyError:
            error_list.append('subscriptionId')
        try:
            application_name = subscription['applicationName']
        except KeyError:
            error_list.append('applicationName')
        try:
            subscriber_address = subscription['subscriberAddress']
        except KeyError:
            error_list.append('subscriberAddress')
        try:
            operation = subscription['operation'].lower()
        except KeyError:
            error_list.append('operation')

        if error_list:
            log.error("Missing mandatory parameters inside subscriptionNotification: {0}".format(error_list))
            return self.error({"status": "NOK", "message": "Missing mandatory parameters inside subscriptionNotification: {0}"
                              .format(error_list)})

        # Validating operation
        if operation != 'subscribe' and operation != 'unsubscribe':
            log.error("Unknown operation for this route.")
            return self.error({"status": "NOK", "message": "Unknown operation for this route"})

        # Validating backend access configs:
        try:
            configs = {
                'host': self.application.settings['config']['tim/v1/backend/host'],
                'url': self.application.settings['config']['tim/v1/backend/notification/url'],
            }
        except KeyError:
            message = "Could not find access configs for TIM: tim/v1/backend/host | tim/v1/backend/mo/url"
            log.error(message)
            return self.error({"status": "NOK", "message": message})

        return func(self)
    return with_notification


def validate_mo(func):
    """
    Validates Tim MO request (mandatory params only)
    """
    @wraps(func)
    def with_mo(self):
        # Validating body
        try:
            body = json_decode(self.request.body)
        except Exception as e:
            log.error("Invalid JSON object: {0}".format(e))
            return self.error({"status": "NOK", "message": "Invalid JSON object"})

        error_list = []
        try:
            help_notification = body['helpNotification']
        except KeyError:
            log.error("Missing mandatory parameter: helpNotification")
            return self.error({"status": "NOK", "message": "Missing mandatory parameter: helpNotification"})

        try:
            subscriber = help_notification['subscriber']
        except KeyError:
            error_list.append('subscriber')
        try:
            subscriber_message = help_notification['subscriberMessage']
        except KeyError:
            error_list.append('subscriberMessage')
        try:
            short_code = help_notification['shortCode']
        except KeyError:
            error_list.append('shortCode')

        if error_list:
            log.error("Missing mandatory parameters inside body: {0}".format(error_list))
            return self.error({"status": "NOK", "message": "Missing mandatory parameters inside helpNotification: {0}"
                              .format(error_list)})

        # Validating backend access configs:
        try:
            configs = {
                'host': self.application.settings['config']['tim/v1/backend/host'],
                'url': self.application.settings['config']['tim/v1/backend/mo/url'],
            }
        except KeyError:
            message = "Could not find access configs for TIM: tim/v1/backend/host | tim/v1/backend/mo/url"
            log.error(message)
            return self.error({"status": "NOK", "message": message})

        return func(self)
    return with_mo
