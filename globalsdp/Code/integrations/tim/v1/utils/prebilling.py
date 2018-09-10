# -*- encoding: utf-8 -*-

import logging
from functools import wraps
from tornado.escape import json_decode
from application import settings
from application.src import databases
from integrations.tim.v1.services import backend as BackendService


# Settings
partner_name = 'tim'

# Logging handler
log = logging.getLogger(__name__)
LOG_HASH = settings.LOG_HASHES[partner_name]
LOG_HASH_BILLING = settings.LOG_HASHES[partner_name]["billing"]


def prebilling(func):
    """
    Makes the double-check for billing operations. It avoids duplicate charges.
    """
    @wraps(func)
    def with_requests(self, *args):

        def finish_billing(self, service):
            service.add_to_file(self.application.settings, json_decode(self.request.body), 0)
            service.add_to_stream(self.application.settings, json_decode(self.request.body), 0)

        # Service
        service = BackendService.BillingService

        # Getting body
        body = json_decode(self.request.body)

        try:
            redis = databases.Redis.get_instance("redis-prebilling")

        except Exception as e:
            finish_billing(self, service)

            log.error("Could not send Billing request to partner. "
                      "Error: Can't connect to Redis."
                      "Exception: {0}. "
                      "Request body: {1}. "
                      "Operation Hash: {2}. "
                      .format(e, body, LOG_HASH_BILLING))

            return self.error({"success": 0, "message": "Could not make double-check (pre-billing). Request aborted."},
                              500)

        try:
            subscription_id = body['subscription_id']

            if redis.get(subscription_id):
                finish_billing(self, service)

                log.error("Could not send Billing request to partner. "
                          "Error: duplicated operation. "
                          "Request body: {0}. "
                          "Operation Hash: {1}. "
                          .format(body, LOG_HASH_BILLING))

                return self.error({"success": 0, "message": "Could not bill: duplicated operation."})

            prebilling = self.application.settings["prebilling"]["tim"]
            product = body["product_id"]
            periodicity = prebilling[product]
            redis.setex(subscription_id, 0, periodicity)

        except KeyError as ke:
            finish_billing(self, service)

            log.error("Could not send Billing request to partner. "
                      "Error: Could not find product {0} inside prebilling settings. "
                      "Request body: {1}. "
                      "Operation Hash: {2}. "
                      .format(body["product_id"], body, LOG_HASH_BILLING))

            return self.error({"success": 0, "message": "Could not make double-check (pre-billing). Request aborted."},
                              500)

        except Exception as e:
            finish_billing(self, service)

            log.error("Could not send Billing request to partner. "
                      "Error: Could not make double-check (pre-billing). "
                      "Exception: {0}. "
                      "Request body: {1}. "
                      "Operation Hash: {2}. "
                      .format(e, body, LOG_HASH_BILLING))

            return self.error({"success": 0, "message": "Could not make double-check (pre-billing). Request aborted."},
                              500)

        return func(self, *args)
    return with_requests
