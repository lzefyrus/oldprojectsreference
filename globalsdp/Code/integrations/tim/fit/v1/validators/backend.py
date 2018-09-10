from functools import wraps
from tornado.escape import json_decode
import logging
import application.settings as settings

# Settings
partner_name = 'tim/fit'
api_version = 'v1'

# Logging handler
log = logging.getLogger(__name__)
LOG_HASH_BILLING = settings.LOG_HASHES[partner_name]["billing"]
LOG_HASH_MT = settings.LOG_HASHES[partner_name]["mt"]

def validate_billing(func):
    """
    Validates billing request: mandatory parameters and configs.
    """
    @wraps(func)
    def with_billing(self):

        MSISDN_MIN_LEN = 10
        MSISDN_MAX_LEN = 13

        #################
        # Validating body
        #################
        try:
            body = json_decode(self.request.body)
        except Exception:
            log.error("Could not send Billing request to partner. "
                      "Error: Invalid JSON. "
                      "Operation Hash: {0}."
                      .format(LOG_HASH_BILLING))
            return self.error({"success": 0, "message": "Invalid JSON"})

        #################################
        # Validating mandatory parameters
        #################################
        error_list = []
        try:
            msisdn = str(body['msisdn'])
        except KeyError:
            error_list.append('msisdn')
        try:
            body['application_id']
        except KeyError:
            error_list.append('application_id')
        try:
            body['contract_id']
        except KeyError:
            error_list.append('contract_id')
        try:
            body['service_provider_id']
        except KeyError:
            error_list.append('service_provider_id')

        if error_list:
            log.error("Could not send Billing request to partner. "
                      "Error: Missing mandatory parameters inside body: {0}. "
                      "Operation Hash: {1}."
                      .format(error_list, LOG_HASH_BILLING))
            return self.error({"success": 0, "message": "Missing mandatory parameters inside body: {0}"
                              .format(error_list)})

        ##############################
        # Validating parameters values
        ##############################
        msisdn_len = len(msisdn)
        if msisdn_len < MSISDN_MIN_LEN or msisdn_len > MSISDN_MAX_LEN:
            log.error("Could not send Billing request to partner. "
                      "Error: Invalid MSISDN {0} with {1} characters (Min: {2}. Max: {3}). "
                      "Operation Hash: {4}."
                      .format(msisdn, msisdn_len, MSISDN_MIN_LEN, MSISDN_MAX_LEN, LOG_HASH_BILLING))
            return self.error({"success": 0, "message": "Invalid MSISDN {0} with {1} characters (Min: {2}. Max: {3})."
                              .format(msisdn, msisdn_len, MSISDN_MIN_LEN, MSISDN_MAX_LEN)})

        ####################
        # Validating configs
        ####################
        try:
            config = self.application.settings['config']
            __ = config['tim/fit/v1/billing/wsdl']["value"]
            __ = config["tim/fit/v1/billing/kinesis/aws_access_key_id"]["value"]
            __ = config["tim/fit/v1/billing/kinesis/aws_secret_access_key"]["value"]
            __ = config["tim/fit/v1/billing/kinesis/region_name"]["value"]
            __ = config["tim/fit/v1/billing/kinesis/stream"]["value"]
            __ = config["tim/fit/v1/billing/kinesis/shard"]["value"]
            __ = config["tim/fit/v1/billing/kinesis/iterator"]["value"]
            __ = config["tim/fit/v1/billing/file/path"]["value"]

        except KeyError:
            log.error("Could not send Billing request to partner. "
                      "Error: Missing mandatory configs. "
                      "Operation Hash: {0}."
                      .format(LOG_HASH_BILLING))
            return self.error({"success": 0, "message": "Internal Error: missing mandatory configs"}, 500)

        return func(self)
    return with_billing


def validate_mt(func):
    """
    Validates MT request: mandatory parameters and configs.
    """
    @wraps(func)
    def with_mt(self):

        MSISDN_MAX_LEN = 13
        MESSAGE_MAX_LEN = 160
        MIN_PRIORITY = 0
        MAX_PRIORITY = 3

        #################
        # Validating body
        #################
        try:
            body = json_decode(self.request.body)
        except Exception:
            log.error("Could not send MT request to partner. "
                      "Error: Invalid JSON. "
                      "Operation Hash: {0}."
                      .format(LOG_HASH_MT))
            return self.error({"success": 0, "message": "Invalid JSON"})

        #################################
        # Validating mandatory parameters
        #################################
        error_list = []
        try:
            msisdn = str(body['msisdn'])
        except KeyError:
            error_list.append('msisdn')
        try:
            body['la']
        except KeyError:
            error_list.append('la')
        try:
            message = str(body['message'])
        except KeyError:
            error_list.append('message')

        if error_list:
            log.error("Could not send MT request to partner. "
                      "Error: Missing mandatory parameters inside body: {0}. "
                      "Operation Hash: {1}."
                      .format(error_list, LOG_HASH_MT))
            return self.error({"success": 0, "message": "Missing mandatory parameters inside body: {0}"
                              .format(error_list)})

        ##############################
        # Validating parameters values
        ##############################
        msisdn_len = len(msisdn)
        if msisdn_len > MSISDN_MAX_LEN:
            log.error("Could not send MT request to partner. "
                      "Error: Invalid MSISDN {0} with {1} characters (max {2}). "
                      "Operation Hash: {3}."
                      .format(msisdn, msisdn_len, MSISDN_MAX_LEN, LOG_HASH_MT))
            return self.error({"success": 0, "message": "Invalid MSISDN {0} with {1} characters (max {2})."
                              .format(msisdn, msisdn_len, MSISDN_MAX_LEN)})

        message_len = len(message)
        if message_len > MESSAGE_MAX_LEN:
            log.error("Could not send MT request to partner. "
                      "Error: Invalid message with {0} characters (max {1}). "
                      "Operation Hash: {2}."
                      .format(message_len, MESSAGE_MAX_LEN, LOG_HASH_MT))
            return self.error({"success": 0, "message": "Invalid message with {0} characters (max {1})."
                              .format(message_len, MESSAGE_MAX_LEN)})

        if 'priority' in body:
            priority = int(body['priority'])
            if priority < MIN_PRIORITY or priority > MAX_PRIORITY:
                log.error("Could not send MT request to partner. "
                          "Error: Invalid priority value ({0}). Min={1}. Max={2}. "
                          "Operation Hash: {3}."
                          .format(priority, MIN_PRIORITY, MAX_PRIORITY, LOG_HASH_MT))
                return self.error({"success": 0, "message": "Invalid priority value ({0}). Min={1}. Max={2}."
                                  .format(priority, MIN_PRIORITY, MAX_PRIORITY)})

        ####################
        # Validating configs
        ####################
        try:
            config = self.application.settings['config']
            __ = config["tim/fit/v1/smpp/host/1"]["value"]
            __ = config["tim/fit/v1/smpp/host/2"]["value"]
            __ = config["tim/fit/v1/smpp/port"]["value"]
            __ = config["tim/fit/v1/smpp/login"]["value"]
            __ = config["tim/fit/v1/smpp/password"]["value"]

        except KeyError:
            log.error("Could not send MT request to partner. "
                      "Error: Missing mandatory configs. "
                      "Operation Hash: {0}."
                      .format(LOG_HASH_MT))
            return self.error({"success": 0, "message": "Internal Error: missing mandatory configs"}, 500)

        return func(self)
    return with_mt
