# -*- encoding: utf-8 -*-

import logging
from functools import wraps
from tornado.escape import json_decode
from application import settings


# Settings
partner_name = 'tim'

# Logging handler
log = logging.getLogger(__name__)
LOG_HASH = settings.LOG_HASHES[partner_name]
LOG_HASH_CANCELLATION = settings.LOG_HASHES[partner_name]["cancellation"]
LOG_HASH_MT = settings.LOG_HASHES[partner_name]["mt"]
LOG_HASH_BILLING = settings.LOG_HASHES[partner_name]["billing"]
LOG_HASH_BILLING_STATUS = settings.LOG_HASHES[partner_name]["billing-status"]
LOG_HASH_MIGRATION = settings.LOG_HASHES[partner_name]["migration"]


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
            log.error("Could not cancel. "
                      "Error: Invalid JSON object. "
                      "JSON: {0}. "
                      "Operation Hash: {1}. "
                      .format(self.request.body, LOG_HASH_CANCELLATION))
            return self.error({"message": "Invalid JSON object", "success": 0})

        # Validating subscription_id
        try:
            subscription_id = body['subscription_id']

        except KeyError:
            log.error("Could not cancel. "
                      "Error: Missing subscription_id inside body. "
                      "Operation Hash: {0}. "
                      .format(LOG_HASH_CANCELLATION))
            return self.error({"message": "Missing subscription_id inside body", "success": 0})

        # Validating bearer_token
        try:
            bearer_token = '{0} {1}'.format(self.application.settings['config']['tim/v1/bearertoken'], subscription_id)

        except KeyError:
            log.error("Could not cancel. "
                      "Error: Can't find Bearer token 'tim/v1/bearertoken'. "
                      "Operation Hash: {0}. "
                      .format(LOG_HASH_CANCELLATION))
            return self.error({"message": "Could not find Bearer token config", "success": 0})

        # Validating access configs:
        try:
            configs = {
                'host': self.application.settings['config']['tim/v1/host'],
                'url': self.application.settings['config']['tim/v1/cancellation/url'],
            }

        except KeyError:
            log.error("Could not cancel. "
                      "Error: Can't find access configs. "
                      "Operation Hash: {0}. "
                      .format(LOG_HASH_CANCELLATION))
            return self.error({"message": "Could not find access configs", "success": 0})

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
            log.error("Could not send MT. "
                      "Error: Invalid JSON object. "
                      "JSON: {0}. "
                      "Operation Hash: {1}. "
                      .format(self.request.body, LOG_HASH_MT))
            return self.error({"message": "Invalid JSON object", "success": 0})

        error_list = []
        try:
            msisdn = body['msisdn']
        except KeyError:
            error_list.append('msisdn')
        try:
            la = body['la']
        except KeyError:
            error_list.append('la')
        try:
            message = body['message']
        except KeyError:
            error_list.append('message')
        try:
            subscription_id = body['subscription_id']
        except KeyError:
            error_list.append('subscription_id')

        if error_list:
            log.error("Could not send MT. "
                      "Error: Missing mandatory parameters inside body: {0}. "
                      "Operation Hash: {1}. "
                      .format(error_list, LOG_HASH_MT))
            return self.error({"status": "NOK", "message": "Missing mandatory parameters inside body: {0}"
                              .format(error_list)})

        # Validating access token
        try:
            client_correlator = body['clientCorrelator']
        except KeyError:
            client_correlator = None

        if not client_correlator:
            # Mandatory Bearer access token
            try:
                token = '{0} {1}'.format(self.application.settings['config']['tim/v1/bearertoken'], subscription_id)
            except KeyError:
                log.error("Could not send MT. "
                          "Error: Can't find Bearer token 'tim/v1/bearertoken'. "
                          "Operation Hash: {0}. "
                          .format(LOG_HASH_MT))
                return self.error({"message": "Could not find Bearer token config", "success": 0})
        else:
            # Mandatory Basic access token
            try:
                token = '{0} {1}'.format(self.application.settings['config']['tim/v1/basictoken'], client_correlator)
            except KeyError:
                log.error("Could not send MT. "
                          "Error: Can't find Basic token 'tim/v1/basictoken'. "
                          "Operation Hash: {0}. "
                          .format(LOG_HASH_MT))
                return self.error({"message": "Could not find Basic token config", "success": 0})

        # Validating Tim access configs:
        try:
            configs = {
                'host': self.application.settings['config']['tim/v1/host']['value'],
                'url': self.application.settings['config']['tim/v1/mt/url']['value'],
                'bearertoken': self.application.settings['config']['tim/v1/bearertoken']['value'],
                'basictoken': self.application.settings['config']['tim/v1/basictoken']['value'],
                'user': self.application.settings['config']['tim/v1/user']['value'],
                'password': self.application.settings['config']['tim/v1/password']['value'],
            }
        except KeyError:
            log.error("Could not send MT. "
                      "Error: Can't find access configs. "
                      "Operation Hash: {0}. "
                      .format(LOG_HASH_MT))
            return self.error({"message": "Could not find access configs", "success": 0})

        return func(self)
    return with_mt


def validate_billing(func):
    """
    Validates Tim MT request (mandatory params only)
    """
    @wraps(func)
    def with_billing(self):
        # Validating body
        try:
            body = json_decode(self.request.body)

        except Exception as e:
            log.error("Could not send Billing. "
                      "Error: Invalid JSON object. "
                      "JSON: {0}. "
                      "Operation Hash: {1}. "
                      .format(self.request.body, LOG_HASH_BILLING))
            return self.error({"message": "Invalid JSON object", "success": 0})

        error_list = []
        try:
            amount = body['amount']
        except KeyError:
            error_list.append('amount')
        try:
            code = body['code']
        except KeyError:
            error_list.append('code')
        try:
            msisdn = body['msisdn']
        except KeyError:
            error_list.append('msisdn')
        try:
            mandate_id = body['mandate_id']
        except KeyError:
            error_list.append('mandate_id')
        try:
            product_id = body['product_id']
        except KeyError:
            error_list.append('product_id')
        try:
            reference_code = body['reference_code']
        except KeyError:
            error_list.append('reference_code')
        try:
            service_id = body['service_id']
        except KeyError:
            error_list.append('service_id')
        try:
            tax_amount = body['tax_amount']
        except KeyError:
            error_list.append('tax_amount')
        try:
            transaction_status = body['transaction_status']
        except KeyError:
            error_list.append('transaction_status')
        try:
            subscription_id = body['subscription_id']
        except KeyError:
            error_list.append('subscription_id')

        if error_list:
            log.error("Could not send Billing. "
                      "Error: Missing mandatory parameters inside body: {0}. "
                      "Operation Hash: {1}. "
                      .format(error_list, LOG_HASH_BILLING))
            return self.error({"status": "NOK", "message": "Missing mandatory parameters inside body: {0}"
                              .format(error_list)})

        # Validating access token
        try:
            bearer_token = '{0} {1}'.format(self.application.settings['config']['tim/v1/bearertoken'], subscription_id)
        except KeyError:
            log.error("Could not send Billing. "
                      "Error: Can't find Bearer token 'tim/v1/bearertoken'. "
                      "Operation Hash: {0}. "
                      .format(LOG_HASH_BILLING))
            return self.error({"message": "Could not find Bearer token", "success": 0})

        # Validating access configs
        try:
            configs = {
                'host': self.application.settings['config']['tim/v1/host'],
                'url': self.application.settings['config']['tim/v1/billing/url'],
            }
        except KeyError:
            log.error("Could not send Billing. "
                      "Error: Can't find access configs. "
                      "Operation Hash: {0}. "
                      .format(LOG_HASH_BILLING))
            return self.error({"message": "Could not find access configs.", "success": 0})

        return func(self)
    return with_billing


def validate_billing_status(func):
    """
    Validates Tim Billing Status request (mandatory params only)
    """
    @wraps(func)
    def with_mt(self):
        # Validating body
        try:
            body = json_decode(self.request.body)

        except Exception as e:
            log.error("Could not send BillingStatus. "
                      "Error: Invalid JSON object. "
                      "JSON: {0}. "
                      "Operation Hash: {1}. "
                      .format(self.request.body, LOG_HASH_BILLING_STATUS))
            return self.error({"message": "Invalid JSON object", "success": 0})

        error_list = []
        try:
            msisdn = body['msisdn']
        except KeyError:
            error_list.append('msisdn')
        try:
            transaction_id = body['transaction_id']
        except KeyError:
            error_list.append('transaction_id')

        if error_list:
            log.error("Could not send BillingStatus. "
                      "Error: Missing mandatory parameters inside body: {0}. "
                      "Operation Hash: {1}. "
                      .format(error_list, LOG_HASH_BILLING_STATUS))
            return self.error({"status": "NOK", "message": "Missing mandatory parameters inside body: {0}"
                              .format(error_list)})

        # Validating Tim access configs:
        try:
            configs = {
                'host': self.application.settings['config']['tim/v1/host']['value'],
                'url': self.application.settings['config']['tim/v1/billing/status/url']['value'],
            }
        except KeyError:
            log.error("Could not send BillingStatus. "
                      "Error: Can't find access configs. "
                      "Operation Hash: {0}. "
                      .format(LOG_HASH_BILLING_STATUS))
            return self.error({"message": "Could not find access configs", "success": 0})
        return func(self)
    return with_mt


def validate_migration(func):
    """
    Validates Tim Migration request (mandatory params only)
    """
    @wraps(func)
    def with_migration(self):
        # Validating body
        try:
            body = json_decode(self.request.body)

        except Exception as e:
            log.error("Could not send Migration. "
                      "Error: Invalid JSON object. "
                      "JSON: {0}. "
                      "Operation Hash: {1}. "
                      .format(self.request.body, LOG_HASH_MIGRATION))
            return self.error({"message": "Invalid JSON object", "success": 0})

        error_list = []
        try:
            msisdn = body['msisdn']
        except KeyError:
            error_list.append('msisdn')

        try:
            application_id = body['application_id']
        except KeyError:
            error_list.append('application_id')

        if error_list:
            log.error("Could not send Migration. "
                      "Error: Missing mandatory parameters inside body: {0}. "
                      "Operation Hash: {1}. "
                      .format(error_list, LOG_HASH_MIGRATION))
            return self.error({"status": "NOK", "message": "Missing mandatory parameters inside body: {0}"
                              .format(error_list)})

        # Validating Tim access configs:
        try:
            configs = {
                'host': self.application.settings['config']['tim/v1/host'],
                'url': self.application.settings['config']['tim/v1/migration/url'],
                'user': self.application.settings['config']['tim/v1/migration/user']['value'],
                'password': self.application.settings['config']['tim/v1/migration/password']['value'],
            }
        except KeyError:
            log.error("Could not send Migration. "
                      "Error: Can't find access configs. "
                      "Operation Hash: {0}. "
                      .format(LOG_HASH_MIGRATION))
            return self.error({"message": "Could not find access configs", "success": 0})

        # Validating token
        try:
            token = self.application.settings['config']['tim/v1/basictoken']['value']
        except KeyError:
            log.error("Could not send Migration. "
                      "Error: Could not find token: tim/v1/basictoken."
                      "Operation Hash: {0}. "
                      .format(LOG_HASH_MIGRATION))
            return self.error({"message": "Could not find token", "success": 0})

        return func(self)
    return with_migration
