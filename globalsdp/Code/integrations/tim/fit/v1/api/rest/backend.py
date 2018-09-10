from application.src.rewrites import APIHandler
from application.src.auth import authenticate
from application.src.auth_la import authenticate_la
from application.src.request import request
from application.src.prebilling import prebilling
from tornado.escape import json_decode
from integrations.tim.fit.v1.services import backend as BackendService
from integrations.tim.fit.v1.validators.backend import validate_billing, validate_mt
from integrations.tim.fit.v1.utils.auth_la import get_la_func
import logging
import application.settings as settings
from application.src.exceptions import UnexpectedResponse


# Settings
partner_name = 'tim/fit'
api_version = 'v1'

# Logging
log = logging.getLogger(__name__)
LOG_HASH_BILLING = settings.LOG_HASHES[partner_name]["billing"]
LOG_HASH_MT = settings.LOG_HASHES[partner_name]["mt"]


class BillingHandler(APIHandler):
    __urls__ = [r"/{0}/{1}/billing".format(partner_name, api_version),
                r"/{0}/{1}/billing/".format(partner_name, api_version)]

    # Service
    service = BackendService.BillingService()

    @request
    @authenticate
    @validate_billing
    @prebilling(partner=partner_name, service=service, keys=['msisdn', 'contract_id'], product_field='contract_id')
    def post(self):

        try:
            settings = self.application.settings
            body = json_decode(self.request.body)
            billing_key = self.service.get_billing_key(body)

        except Exception as e:
            log.error("Could not send Billing request to partner. "
                      "Error: can't get billing key. "
                      "Exception: {0}. "
                      "Operation Hash: {1}."
                      .format(e, LOG_HASH_BILLING))
            return self.error({"success": 0, "message": "Could not bill"}, 500)

        try:
            # Getting configs
            configs = self.service.get_configs(self.application.settings)

            # Getting request data
            xml = self.service.get_request(body)
            wsdl = configs["wsdl"]

            # Doing billing
            result = self.service.bill(xml, wsdl)

            # Returns SUCCESS
            if result["success"]:
                self.service.finish(settings, body, billing_key, 1)

                log.info("Billing request sent to partner. "
                         "Request WSDL: {0}. "
                         "Request XML: {1}. "
                         "Response: {2}. "
                         "Operation Hash: {3}."
                         .format(wsdl, xml, result, LOG_HASH_BILLING))

                return self.success(result)

            # Returns ERROR
            self.service.finish(settings, body, billing_key, 0)

            log.error("Could not bill. "
                      "Request WSDL: {0}. "
                      "Request XML: {1}. "
                      "Response: {2}. "
                      "Operation Hash: {3}."
                      .format(wsdl, xml, result, LOG_HASH_BILLING))

            return self.error(result)

        except UnexpectedResponse as ur:
            self.service.finish(settings, body, billing_key, 0)

            log.error("Could not bill. "
                      "Error: {0}. "
                      "Operation Hash: {1}."
                      .format(ur, LOG_HASH_BILLING))
            return self.error({"success": 0, "message": "Could not bill"}, 400)

        except Exception as e:
            self.service.finish(settings, body, billing_key, 0)

            log.error("Could not send Billing request to partner. "
                      "Error: An unexpected error occurred. "
                      "Exception: {0}. "
                      "Operation Hash: {1}."
                      .format(e, LOG_HASH_BILLING))
            return self.error({"success": 0, "message": "Could not bill"}, 500)


class MtHandler(APIHandler):
    __urls__ = [r"/{0}/{1}/mt".format(partner_name, api_version),
                r"/{0}/{1}/mt/".format(partner_name, api_version)]

    # Service
    service = BackendService.MtService()

    # Priority
    DEFAULT_PRIORITY = 0

    @request
    @authenticate
    @validate_mt
    @authenticate_la(get_la_func, LOG_HASH_MT)
    def post(self):

        try:
            # Getting body
            body = json_decode(self.request.body)

            # Getting mandatory parameters
            msisdn = str(body['msisdn'])
            la = str(body['la'])
            message = str(body['message'])

            # Getting optional parameters
            try:
                priority = int(body['priority'])
            except KeyError:
                priority = self.DEFAULT_PRIORITY

            # Getting configs
            configs = self.service.get_configs(self.application.settings)

            # Sending (async)
            try:
                queue = self.service.choose_queue(configs["queues"], priority)
                self.service.send.apply_async(args=[configs, body, msisdn, la, message], queue=queue)
                return self.success({"success": 1, "message": "OK"})

            except Exception as e:
                log.error("Could not send MT request to partner. "
                          "Request body: {0}. "
                          "Error: send method did not work properly. "
                          "Exception: {1}. "
                          "Operation Hash: {2}."
                          .format(body, e, LOG_HASH_MT))
                return self.error({"success": 0, "message": "Could not send MT"}, 500)

        except Exception as e:
            log.error("Could not send MT request to partner. "
                      "Error: An unexpected error occurred. "
                      "Exception: {0}. "
                      "Operation Hash: {1}."
                      .format(e, LOG_HASH_MT))
            return self.error({"success": 0, "message": "Could not send MT"}, 500)
