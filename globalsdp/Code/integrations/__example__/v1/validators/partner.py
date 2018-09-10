from functools import wraps
from tornado.escape import json_decode
import logging

# Logging handler
log = logging.getLogger(__name__)


def validate_signature(func):
    """
    Validates signature request
    """
    @wraps(func)
    def with_register(self):
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

        return func(self)
    return with_register


def validate_mo(func):
    """
    Validates mo request
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

        return func(self)
    return with_mo
