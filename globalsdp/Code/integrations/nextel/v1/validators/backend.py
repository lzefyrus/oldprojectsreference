from functools import wraps
from tornado.escape import json_decode
import logging

# Logging handler
log = logging.getLogger(__name__)


def validate_signature(func):
    """
    Validates Nextel Signature request (mandatory params only)
    """
    @wraps(func)
    def with_signature(self):
        # Validating body
        try:
            body = json_decode(self.request.body)
        except Exception as e:
            log.error("Invalid JSON object: {0}".format(e))
            return self.error({"success": 0, "message": "Invalid JSON object"})

        error_list = []
        try:
            channel_id = body['channel_id']
        except KeyError:
            error_list.append('channel_id')
        try:
            la = body['la']
        except KeyError:
            error_list.append('la')
        try:
            msisdn = body['msisdn']
        except KeyError:
            error_list.append('msisdn')

        try:
            double_option = body['double-option']
        except KeyError:
            error_list.append('double-option')

        if error_list:
            log.error("Missing mandatory parameters: {0}".format(error_list))
            return self.error({"status": "NOK",
                               "message": "Missing mandatory parameters: {0}".format(error_list)})

        # Validating access configs:
        try:
            configs = {
                'host': self.application.settings['config']['nextel/v1/host'],
                'url': self.application.settings['config']['nextel/v1/signature/url'],
                'company_id': self.application.settings['config']['nextel/v1/company/id'],
                'operation_code': self.application.settings['config']['nextel/v1/signature/code'],
                'operation_description': self.application.settings['config']['nextel/v1/signature/description'],
                'auth_type': self.application.settings['config']['nextel/v1/signature/auth/type'],
                'notification_type': self.application.settings['config']['nextel/v1/signature/notification/type'],
                'notification_calltype': self.application.settings['config']['nextel/v1/signature/notification/calltype'],
                'notification_callback': self.application.settings['config']['nextel/v1/signature/notification/callback'],
            }
        except KeyError:
            log.error("Could not find Nextel configs on database")
            return self.error({"message": "Could not find Nextel configs on database"})

        # Validating configs by LA:
        try:
            configs_by_la = {
                'user': self.application.settings['config']['nextel/v1/{0}/user'.format(la)],
                'password': self.application.settings['config']['nextel/v1/{0}/password'.format(la)],
                'service_id': self.application.settings['config']['nextel/v1/{0}/service-id'.format(la)],
            }
        except KeyError:
            message = "Could not find Nextel configs on database for LA {0}".format(la)
            log.error(message)
            return self.error({"message": message})

        return func(self)
    return with_signature


def validate_cancellation(func):
    """
    Validates Nextel Cancellation request (mandatory params only)
    """
    @wraps(func)
    def with_cancellation(self):
        # Validating body
        try:
            body = json_decode(self.request.body)
        except Exception as e:
            log.error("Invalid JSON object: {0}".format(e))
            return self.error({"success": 0, "message": "Invalid JSON object"})

        error_list = []
        try:
            channel_id = body['channel_id']
        except KeyError:
            error_list.append('channel_id')
        try:
            msisdn = body['msisdn']
        except KeyError:
            error_list.append('msisdn')
        try:
            la = body['la']
        except KeyError:
            error_list.append('la')

        if error_list:
            log.error("Missing mandatory parameters: {0}".format(error_list))
            return self.error({"success": 0,
                               "message": "Missing mandatory parameters: {0}".format(error_list)})

        # Validating access configs:
        try:
            configs = {
                'host': self.application.settings['config']['nextel/v1/host'],
                'url': self.application.settings['config']['nextel/v1/cancellation/url'],
                'company_id': self.application.settings['config']['nextel/v1/company/id'],
                'operation_code': self.application.settings['config']['nextel/v1/cancellation/code'],
                'operation_description': self.application.settings['config']['nextel/v1/cancellation/description'],
                'notification_type': self.application.settings['config']['nextel/v1/cancellation/notification/type'],
                'notification_calltype': self.application.settings['config']['nextel/v1/cancellation/notification/calltype'],
                'notification_callback': self.application.settings['config']['nextel/v1/cancellation/notification/callback'],
            }
        except KeyError:
            log.error("Could not find Nextel configs on database")
            return self.error({"message": "Could not find Nextel configs on database"})

        # Validating configs by LA:
        try:
            configs_by_la = {
                'user': self.application.settings['config']['nextel/v1/{0}/user'.format(la)],
                'password': self.application.settings['config']['nextel/v1/{0}/password'.format(la)],
                'service_id': self.application.settings['config']['nextel/v1/{0}/service-id'.format(la)],
            }
        except KeyError:
            message = "Could not find Nextel configs on database for LA {0}".format(la)
            log.error(message)
            return self.error({"message": message})

        return func(self)
    return with_cancellation


def validate_mt(func):
    """
    Validates Nextel MT request (mandatory params only)
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
            la = body['la']
        except KeyError:
            error_list.append('la')
        try:
            msisdns = body['msisdns']
        except KeyError:
            error_list.append('msisdns')
        try:
            channel_id = body['channel_id']
        except KeyError:
            error_list.append('channel_id')
        try:
            message = body['message']
        except KeyError:
            error_list.append('message')

        if error_list:
            log.error("Missing mandatory parameters: {0}".format(error_list))
            return self.error({"success": 0,
                               "message": "Missing mandatory parameters: {0}".format(error_list)})

        # Validating access configs:
        try:
            configs = {
                'host': self.application.settings['config']['nextel/v1/host'],
                'url': self.application.settings['config']['nextel/v1/mt/url'],
                'company_id': self.application.settings['config']['nextel/v1/company/id'],
                'keep_session': self.application.settings['config']['nextel/v1/mt/keepsession'],
                'notification_type': self.application.settings['config']['nextel/v1/mt/notification/type'],
                'notification_calltype': self.application.settings['config']['nextel/v1/mt/notification/calltype'],
                'notification_callback': self.application.settings['config']['nextel/v1/mt/notification/callback'],
            }
        except KeyError:
            log.error("Could not find Nextel configs on database")
            return self.error({"message": "Could not find Nextel configs on database"})

        # Validating configs by LA:
        try:
            configs_by_la = {
                'user': self.application.settings['config']['nextel/v1/{0}/user'.format(la)],
                'password': self.application.settings['config']['nextel/v1/{0}/password'.format(la)],
                'service_id': self.application.settings['config']['nextel/v1/{0}/service-id'.format(la)],
            }
        except KeyError:
            message = "Could not find Nextel configs on database for LA {0}".format(la)
            log.error(message)
            return self.error({"message": message})

        return func(self)
    return with_mt


def validate_billing(func):
    """
    Validates Nextel Billing request (mandatory params only)
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
            channel_id = body['channel_id']
        except KeyError:
            error_list.append('channel_id')

        try:
            la = body['la']
        except KeyError:
            error_list.append('la')

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
                'host': self.application.settings['config']['nextel/v1/host'],
                'url': self.application.settings['config']['nextel/v1/billing/url'],
                'company_id': self.application.settings['config']['nextel/v1/company/id'],
                'operation_code': self.application.settings['config']['nextel/v1/billing/code'],
                'operation_description': self.application.settings['config']['nextel/v1/billing/description'],
                'transaction_type': self.application.settings['config']['nextel/v1/billing/transaction/type'],
                'transaction_description': self.application.settings['config']['nextel/v1/billing/transaction/description'],
            }
        except KeyError:
            log.error("Could not find Nextel configs on database")
            return self.error({"message": "Could not find Nextel configs on database"})

        # Validating configs by LA:
        try:
            configs_by_la = {
                'user': self.application.settings['config']['nextel/v1/{0}/user'.format(la)],
                'password': self.application.settings['config']['nextel/v1/{0}/password'.format(la)],
                'service_id': self.application.settings['config']['nextel/v1/{0}/service-id'.format(la)],
            }
        except KeyError:
            message = "Could not find Nextel configs on database for LA {0}".format(la)
            log.error(message)
            return self.error({"message": message})

        return func(self)
    return with_billing