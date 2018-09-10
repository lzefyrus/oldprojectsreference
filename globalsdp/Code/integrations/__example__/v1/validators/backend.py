from functools import wraps
from tornado.escape import json_decode
import logging

# Logging handler
log = logging.getLogger(__name__)


def validate_cancellation(func):
    """
    Validates Tim Cancellation request (mandatory params only)
    """
    @wraps(func)
    def with_cancellation(self):
        # Validating body
        try:
            body = json_decode(self.request.body)
        except Exception as e:
            log.error("Invalid JSON object: {0}".format(e))
            return self.error({"status": "NOK", "message": "Invalid JSON object"})

        error_list = []
        try:
            param1 = body['param1']
        except KeyError:
            log.error("Missing mandatory parameter: param1")
            error_list.append('param1')
        try:
            param2 = body['param2']
        except KeyError:
            error_list.append('param2')

        if error_list:
            log.error("Missing mandatory parameters: {0}".format(error_list))
            return self.error({"status": "NOK",
                               "message": "Missing mandatory parameters: {0}".format(error_list)})

        # Validating access configs:
        try:
            configs = {
                'host': self.application.settings['config']['__example__/v1/host'],
                'url': self.application.settings['config']['__example__/v1/cancellation/url'],
            }
        except KeyError:
            log.error("Could not find access configs")
            return self.error({"message": "Could not find access configs"})

        return func(self)
    return with_cancellation


def validate_mt(func):
    """
    Validates Tim MT request (mandatory params only)
    """
    @wraps(func)
    def with_mt(self):
        # Validating body
        try:
            body = json_decode(self.request.body)
        except Exception as e:
            log.error("Invalid JSON object: {0}".format(e))
            return self.error({"status": "NOK", "message": "Invalid JSON object"})

        error_list = []
        try:
            param1 = body['param1']
        except KeyError:
            log.error("Missing mandatory parameter: param1")
            error_list.append('param1')
        try:
            param2 = body['param2']
        except KeyError:
            error_list.append('param2')

        if error_list:
            log.error("Missing mandatory parameters: {0}".format(error_list))
            return self.error({"status": "NOK",
                               "message": "Missing mandatory parameters: {0}".format(error_list)})

        # Validating access configs:
        try:
            configs = {
                'host': self.application.settings['config']['__example__/v1/host'],
                'url': self.application.settings['config']['__example__/v1/cancellation/url'],
            }
        except KeyError:
            log.error("Could not find access configs")
            return self.error({"message": "Could not find access configs"})

        return func(self)
    return with_mt
