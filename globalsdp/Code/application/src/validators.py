# -*- encoding: utf-8 -*-

import logging
from functools import wraps
from tornado.escape import json_decode
from application import settings


# Logging handler
log = logging.getLogger(__name__)
LOG_HASH_MT = settings.LOG_HASHES["application"]["mt"]


def validate_mt(func):
    """
    Validates generic MT request.
    """
    @wraps(func)
    def with_mt(self):
        min_priority = 0
        max_priority = 3

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
            text = body['text']
        except KeyError:
            error_list.append('text')
        try:
            carrier = body['carrier']
        except KeyError:
            error_list.append('carrier')

        if "async" in body:
            if type(body["async"]) is not dict:
                error_list.append('async')
            else:
                try:
                    priority = body['async']['priority']

                    if type(priority) is not int:
                        log.error("Could not send MT. "
                                  "Error: Priority must be integer. "
                                  "Operation Hash: {0}. "
                                  .format(LOG_HASH_MT))
                        return self.error({"success": 0, "message": "Priority must be integer"})

                    if priority < min_priority or priority > max_priority:
                        log.error("Could not send MT. "
                                  "Error: Priority must be between {0} and {1}. "
                                  "Operation Hash: {2}. "
                                  .format(min_priority, max_priority, LOG_HASH_MT))
                        return self.error({"success": 0, "message": "Priority must be between {0} and {1}"
                                          .format(min_priority, max_priority)})
                except KeyError:
                    error_list.append('async:priority')
                try:
                    callback = body['async']['callback']
                except KeyError:
                    error_list.append('async:callback')

        if error_list:
            log.error("Could not send MT. "
                      "Error: Missing mandatory parameters inside body: {0}. "
                      "Operation Hash: {1}. "
                      .format(error_list, LOG_HASH_MT))
            return self.error({"success": 0, "message": "Missing mandatory parameters inside body: {0}"
                              .format(error_list)})

        # Validating access configs:
        try:
            configs = {

                # Vivo
                'vivo_host': self.application.settings['config']['vivo/host']['value'],
                'vivo_url': self.application.settings['config']['vivo/mt/url']['value'],
                'vivo_user': self.application.settings['config']['vivo/user']['value'],
                'vivo_password': self.application.settings['config']['vivo/password']['value'],

                # Oi
                "oi_host": self.application.settings['config']['oi/host']['value'],
                "oi_mt_url": self.application.settings['config']['oi/mt/url']['value'],

                # Tim
                "tim_user":  self.application.settings['config']['tim/fit/user']['value'],
                "tim_password":  self.application.settings['config']['tim/fit/password']['value'],
                "tim_host":  self.application.settings['config']['tim/fit/host']['value'],
                "tim_mt_url":  self.application.settings['config']['tim/fit/mt/url']['value'],

                # Nextel
                "nextel_host": self.application.settings['config']['nextel/host']['value'],
                "nextel_mt_url": self.application.settings['config']['nextel/mt/url']['value'],
                "nextel_channel": self.application.settings['config']['nextel/mt/channel']['value'],

                # Algar
                "algar_host": self.application.settings['config']['algar/host']['value'],
                "algar_mt_url": self.application.settings['config']['algar/mt/url']['value'],
                "algar_channel": self.application.settings['config']['algar/mt/channel']['value'],

            }
        except KeyError as key:
            log.error("Could not find access configs for MT API.")
            return self.error({"success": 0, "message": "Could not find access configs for MT API. {0}".format(key)})

        return func(self)
    return with_mt
