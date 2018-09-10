from functools import wraps
from tornado.escape import json_decode
import logging

# Logging handler
log = logging.getLogger(__name__)

def validate_mt(func):
    """
    Validates Claro MT request (mandatory params only)
    """
    @wraps(func)
    def with_mt(self):
        # Validating body
        try:
            body = json_decode(self.request.body)
        except Exception as e:
            log.error("Invalid JSON object: {0}".format(e))
            return self.error({"success": 0, "message": "Invalid JSON object"})

        error_list = []
        try:
            message = body['message']
        except KeyError:
            error_list.append('message')

        try:
            msisdn = body['msisdn']
        except KeyError:
            error_list.append('msisdn')

        try:
            mode = body['mode']
            if mode.lower() not in ("assync-oneway", "assync-delivery", "sync"):
                log.error("Mode parameter must be: 'assync-oneway','assync-delivery' or 'sync'")
                return self.error({"success": 0,
                               "message": "Mode parameter must be: 'assync-oneway', 'assync-delivery' or 'sync'"})
        except KeyError:
            error_list.append('mode')

        if error_list:
            log.error("Missing mandatory parameters: {0}".format(error_list))
            return self.error({"success": 0,
                               "message": "Missing mandatory parameters: {0}".format(error_list)})

        # Validating access configs:
        try:
            configs = {
                'host': self.application.settings['config']['claro/v1/host'],
                'url': self.application.settings['config']['claro/v1/mt/url'],
                'user': self.application.settings['config']['claro/v1/backend/user'],
                'password': self.application.settings['config']['claro/v1/backend/password'],
            }
        except KeyError:
            log.error("Could not find Claro configs on database")
            return self.error({"message": "Could not find Claro configs on database"})

        return func(self)
    return with_mt


def validate_mms_mt(func):
    """
    Validates Claro MMS MT request (mandatory params only)
    """
    @wraps(func)
    def with_mms_mt(self):
        # Validating body
        try:
            body = json_decode(self.request.body)
        except Exception as e:
            log.error("Invalid JSON object: {0}".format(e))
            return self.error({"success": 0, "message": "Invalid JSON object"})

        error_list = []
        try:
            message = body['message']
        except KeyError:
            error_list.append('message')

        if 'message' not in error_list:
            try:
                message = message.decode('ISO-8859-1')
            except:
                log.error("Message parameter must be encoded as ISO-8859-1")
                return self.error({"success": 0, "message": "Message parameter must be encoded as ISO-8859-1"})

        try:
            msisdn = body['msisdn']
        except KeyError:
            error_list.append('msisdn')
        try:
            mode = body['mode']
            if mode.lower() not in ("assync-oneway", "assync-delivery", "sync"):
                log.error("Mode parameter must be: 'assync-delivery' or 'sync'")
                return self.error({"success": 0,
                               "message": "Mode parameter must be: 'assync-oneway', 'assync-delivery' or 'sync'"})
        except KeyError:
            error_list.append('mode')

        if error_list:
            log.error("Missing mandatory parameters: {0}".format(error_list))
            return self.error({"success": 0,
                               "message": "Missing mandatory parameters: {0}".format(error_list)})

        # Validating access configs:
        try:
            configs = {
                'host': self.application.settings['config']['claro/v1/host'],
                'url': self.application.settings['config']['claro/v1/mmsmt/url'],
                'user': self.application.settings['config']['claro/v1/backend/user'],
                'password': self.application.settings['config']['claro/v1/backend/password'],
            }
        except KeyError:
            log.error("Could not find Claro configs on database")
            return self.error({"message": "Could not find Claro configs on database"})

        return func(self)
    return with_mms_mt


def validate_wap_mt(func):
    """
    Validates Claro WAP MT request (mandatory params only)
    """
    @wraps(func)
    def with_wap_mt(self):
        # Validating body
        try:
            body = json_decode(self.request.body)
        except Exception as e:
            log.error("Invalid JSON object: {0}".format(e))
            return self.error({"success": 0, "message": "Invalid JSON object"})

        error_list = []
        try:
            message = body['message']
        except KeyError:
            error_list.append('message')

        try:
            msisdn = body['msisdn']
        except KeyError:
            error_list.append('msisdn')

        try:
            url = body['url']
        except KeyError:
            error_list.append('url')

        try:
            mode = body['mode']
            if mode.lower() not in ("assync-oneway", "assync-delivery", "sync"):
                log.error("Mode parameter must be: 'assync-delivery' or 'sync'")
                return self.error({"success": 0,
                               "message": "Mode parameter must be: 'assync-oneway', 'assync-delivery' or 'sync'"})
        except KeyError:
            error_list.append('mode')

        if error_list:
            log.error("Missing mandatory parameters: {0}".format(error_list))
            return self.error({"success": 0,
                               "message": "Missing mandatory parameters: {0}".format(error_list)})

        # Validating access configs:
        try:
            configs = {
                'host': self.application.settings['config']['claro/v1/host'],
                'url': self.application.settings['config']['claro/v1/wapmt/url'],
                'user': self.application.settings['config']['claro/v1/backend/user'],
                'password': self.application.settings['config']['claro/v1/backend/password'],
            }
        except KeyError:
            log.error("Could not find Claro configs on database")
            return self.error({"message": "Could not find Claro configs on database"})

        return func(self)
    return with_wap_mt


def validate_check_credit(func):
    """
    Validates Claro Check Credit request (mandatory params only)
    """
    @wraps(func)
    def with_cc(self):
        # Validating body
        try:
            body = json_decode(self.request.body)
        except Exception as e:
            log.error("Invalid JSON object: {0}".format(e))
            return self.error({"success": 0, "message": "Invalid JSON object"})

        error_list = []
        try:
            amount = body['amount']
        except KeyError:
            error_list.append('amount')
        try:
            msisdn = body['msisdn']
        except KeyError:
            error_list.append('msisdn')

        if error_list:
            log.error("Missing mandatory parameters: {0}".format(error_list))
            return self.error({"success": 0,
                               "message": "Missing mandatory parameters: {0}".format(error_list)})

        # Validating access configs:
        try:
            configs = {
                'host': self.application.settings['config']['claro/v1/host'],
                'url': self.application.settings['config']['claro/v1/checkcredit/url'],
                'user': self.application.settings['config']['claro/v1/backend/user'],
                'password': self.application.settings['config']['claro/v1/backend/password'],
            }
        except KeyError:
            log.error("Could not find Claro configs on database")
            return self.error({"message": "Could not find Claro configs on database"})

        return func(self)
    return with_cc


def validate_billing(func):
    """
    Validates Claro Billing request (mandatory params only)
    """
    @wraps(func)
    def with_billing(self):
        # Validating body
        try:
            body = json_decode(self.request.body)
        except Exception as e:
            log.error("Invalid JSON object: {0}".format(e))
            return self.error({"success": 0, "message": "Invalid JSON object"})

        error_list = []
        try:
            billing_code = body['billing_code']
        except KeyError:
            error_list.append('billing_code')
        try:
            msisdn = body['msisdn']
        except KeyError:
            error_list.append('msisdn')

        if error_list:
            log.error("Missing mandatory parameters: {0}".format(error_list))
            return self.error({"success": 0,
                               "message": "Missing mandatory parameters: {0}".format(error_list)})

        # Validating access configs:
        try:
            configs = {
                'host': self.application.settings['config']['claro/v1/host'],
                'url': self.application.settings['config']['claro/v1/billing/url'],
                'user': self.application.settings['config']['claro/v1/backend/user'],
                'password': self.application.settings['config']['claro/v1/backend/password'],
            }
        except KeyError:
            log.error("Could not find Claro configs on database")
            return self.error({"message": "Could not find Claro configs on database"})

        return func(self)
    return with_billing


def validate_wib_push(func):
    """
    Validates Claro Wib Push request (mandatory params only)
    """
    @wraps(func)
    def with_wib_push(self):
        # Validating body
        try:
            body = json_decode(self.request.body)
        except Exception as e:
            log.error("Invalid JSON object: {0}".format(e))
            return self.error({"success": 0, "message": "Invalid JSON object"})

        error_list = []
        try:
            wml_push_code = body['wml_push_code']
        except KeyError:
            error_list.append('wml_push_code')
        try:
            msisdn = body['msisdn']
        except KeyError:
            error_list.append('msisdn')

        try:
            mode = body['mode']
            if mode.lower() not in ("assync-oneway", "assync-delivery", "sync"):
                log.error("Mode parameter must be: 'assync-delivery' or 'sync'")
                return self.error({"success": 0,
                               "message": "Mode parameter must be: 'assync-oneway', 'assync-delivery' or 'sync'"})
        except KeyError:
            error_list.append('mode')

        if error_list:
            log.error("Missing mandatory parameters: {0}".format(error_list))
            return self.error({"success": 0,
                               "message": "Missing mandatory parameters: {0}".format(error_list)})

        # Validating access configs:
        try:
            configs = {
                'host': self.application.settings['config']['claro/v1/host'],
                'url': self.application.settings['config']['claro/v1/wibpush/url'],
                'user': self.application.settings['config']['claro/v1/backend/user'],
                'password': self.application.settings['config']['claro/v1/backend/password'],
            }
        except KeyError:
            log.error("Could not find Claro configs on database")
            return self.error({"message": "Could not find Claro configs on database"})

        return func(self)
    return with_wib_push
