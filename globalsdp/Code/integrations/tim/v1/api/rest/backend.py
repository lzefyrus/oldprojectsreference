# -*- encoding: utf-8 -*-

import logging
import json
import tornado.gen
from tornado.httpclient import AsyncHTTPClient
from tornado.escape import json_decode
from tornado.httpclient import HTTPError
from application.src.rewrites import APIHandler
from application.src.auth import authenticate
from application.src.request import request
from application.src import databases, utils
from application import settings
from integrations.tim.v1.utils.prebilling import prebilling
from integrations.tim.v1.services import backend as BackendService
from integrations.tim.v1.validators.backend import validate_cancellation, validate_mt, validate_billing, \
    validate_billing_status, validate_migration


# Settings
partner_name = 'tim'
api_version = 'v1'

# Logging handler
log = logging.getLogger(__name__)
LOG_HASH = settings.LOG_HASHES[partner_name]
LOG_HASH_CANCELLATION = settings.LOG_HASHES[partner_name]["cancellation"]
LOG_HASH_MT = settings.LOG_HASHES[partner_name]["mt"]
LOG_HASH_BILLING = settings.LOG_HASHES[partner_name]["billing"]
LOG_HASH_BILLING_STATUS = settings.LOG_HASHES[partner_name]["billing-status"]
LOG_HASH_MIGRATION = settings.LOG_HASHES[partner_name]["migration"]


class CancellationHandler(APIHandler):
    """
    Receives cancellation requests from backend.
    """

    __urls__ = [r"/{0}/{1}/backend/cancellation(?:/)?".format(partner_name, api_version)]

    # Service
    service = BackendService.CancellationService

    @tornado.gen.coroutine
    @request
    @authenticate
    @validate_cancellation
    def post(self):
        """
        Receives post requests.
        :return:
        """

        # Getting body
        request_body = json_decode(self.request.body)

        try:
            subscription_id = request_body['subscription_id']

            # Getting configs
            configs = self.service.get_configs(self.application.settings)

            # Getting access token
            token = self.service.get_token(configs, subscription_id)

            # Building request object
            request_url = self.service.get_url(configs, subscription_id)
            request_header = self.service.get_header(token)
            request_object = self.service.get_request(request_url, request_header)

        except Exception as e:
            # Log
            log.error("Could not send Cancellation request to partner. "
                      "Error: {0}. "
                      "Request body: {1}. "
                      "Operation Hash: {2}. "
                      .format(e, request_body, LOG_HASH_CANCELLATION))

            # Return error
            return self.error({"message": "Internal Server Error", "success": 0}, 500)

        # Sending request to TIM
        try:
            response = yield AsyncHTTPClient().fetch(request_object, raise_error=False)

        except Exception as e:
            # Log
            log.error("Could not send Cancellation request to partner. "
                      "Request URL: {0}. "
                      "Request body: {1}. "
                      "Request headers: {2}. "
                      "Error: {3}. "
                      "Operation Hash: {4}. "
                      .format(request_url, request_body, request_header, e, LOG_HASH_CANCELLATION))

            # Return error
            return self.error({"success": 0, "message": "Could not send request"}, 500)

        # Handling response
        try:
            if response.code == 204:
                # Log
                log.info("Cancellation request sent to partner. "
                         "Request URL: {0}. "
                         "Request body: {1}. "
                         "Request headers: {2} "
                         "Response body: {3}. "
                         "Response code: {4}. "
                         "Operation Hash: {5}. "
                         .format(request_url, request_body, request_header, response.body, response.code,
                                 LOG_HASH_CANCELLATION))

                # Return error
                return self.success({"success": 1, 'message': 'Cancellation successfully done'})

            if response.code == 401:
                # Log
                log.error("Could not cancel: unauthorized. "
                          "Request URL: {0}. "
                          "Request body: {1}. "
                          "Request headers: {2}. "
                          "Response body: {3}. "
                          "Response code: {4}. "
                          "Operation Hash: {5}. "
                          .format(request_url, request_body, request_header, response.body, response.code,
                                  LOG_HASH_CANCELLATION))

                # Return error
                return self.error({"success": 0, "message": "Could not cancel"}, response.code)

            # Log
            log.error("Could not cancel: an unexpected error occurred. "
                      "Request URL: {0}. "
                      "Request body: {1}. "
                      "Request headers: {2}. "
                      "Response body: {3}. "
                      "Response code: {4}. "
                      "Operation Hash: {5}. "
                      .format(request_url, request_body, request_header, response.body, response.code,
                              LOG_HASH_CANCELLATION))

            # Return error
            return self.error({"success": 0, "message": "Could not cancel"})

        except Exception as e:
            # Log
            log.error("Cancellation request sent to partner. But could not read response. "
                      "Request URL: {0}. "
                      "Request body: {1}. "
                      "Request headers: {2}. "
                      "Error: {3}. "
                      "Operation Hash: {4}. "
                      .format(request_url, request_body, request_header, e, LOG_HASH_CANCELLATION))

            # Return error
            return self.error({"success": 0, "message": "Could not read response"}, 500)


class MtHandler(APIHandler):
    """
    Receives MT requests from backend.
    """

    __urls__ = [r"/{0}/{1}/backend/mt(?:/)?".format(partner_name, api_version)]

    # Service
    service = BackendService.MtService

    @tornado.gen.coroutine
    @request
    @authenticate
    @validate_mt
    def post(self):
        """
        Receives post requests.
        :return:
        """

        # Getting body
        body = json_decode(self.request.body)

        try:
            # Getting mandatory parameters
            msisdn = body['msisdn']
            la = self.service.replace_la(body['la'])
            message = body['message']
            subscription_id = body['subscription_id']

            # Getting optional parameters
            client_correlator = utils.get_optional_key(body, 'clientCorrelator')

            # Getting configs
            configs = self.service.get_configs(self.application.settings)

            # Getting access token
            token = self.service.get_token(configs, subscription_id, client_correlator)

            # Building request object
            request_url = self.service.get_url(configs, la)
            request_body = self.service.get_body(msisdn, la, message, client_correlator)
            request_header = self.service.get_header(token)
            request_object = self.service.get_request(request_url, request_body, request_header)

        except Exception as e:
            # Log
            log.error("Could not send MT request to partner. "
                      "Error: {0}. "
                      "Request body: {1}. "
                      "Operation Hash: {2}. "
                      .format(e, body, LOG_HASH_MT))

            # Return error
            return self.error({"message": "Internal Server Error", "success": 0}, 500)

        # Sending request to TIM
        try:
            response = yield AsyncHTTPClient().fetch(request_object)

        except HTTPError as httpe:
            try:
                response_code = httpe.response.code
            except:
                response_code = 500

            # Log
            log.error("Could not send MT. "
                      "Request URL: {0}. "
                      "Request body: {1}. "
                      "Request headers: {2}. "
                      "Error: {3}. "
                      "Response code: {4}. "
                      "Operation Hash: {5}. "
                      .format(request_url, request_body, request_header, httpe, response_code, LOG_HASH_MT))

            # Return error
            return self.error({"message": "Could not send MT", "success": 0}, response_code)

        except Exception as e:
            # Log
            log.error("Could not send MT. "
                      "Request URL: {0}. "
                      "Request body: {1}. "
                      "Request headers: {2}. "
                      "Error: {3}. "
                      "Operation Hash: {4}. "
                      .format(request_url, request_body, request_header, e, LOG_HASH_MT))

            # Return error
            return self.error({"message": "Could not send MT", "success": 0}, 500)

        # Handling response
        try:
            json_response = json.loads(response.body.decode('utf-8'))

            # Log
            log.info("MT sent. "
                     "Request URL: {0}. "
                     "Request body: {1}. "
                     "Request headers: {2}. "
                     "Response body: {3}. "
                     "Response code: {4}. "
                     "Operation Hash: {5}. "
                     .format(request_url, request_body, request_header, json_response, response.code, LOG_HASH_MT))

            # Return success
            return self.success({"success": 1, 'message': json_response})

        except Exception as e:
            # Log
            log.info("MT sent, but could not read response. "
                     "Request URL: {0}. "
                     "Request body: {1}. "
                     "Request headers: {2}. "
                     "Response body: {3}. "
                     "Response code: {4}. "
                     "Error: {5}. "
                     "Operation Hash: {6}. "
                     .format(request_url, request_body, request_header, response.body, response.code, e, LOG_HASH_MT))

            # Return success
            return self.success({"success": 1, "message": "MT sent, but could not read response"})


class BillingHandler(APIHandler):
    """
    Receives billing requests from backend.
    """

    __urls__ = [r"/{0}/{1}/backend/billing(?:/)?".format(partner_name, api_version)]

    # Service
    service = BackendService.BillingService

    @tornado.gen.coroutine
    @request
    @authenticate
    @validate_billing
    @prebilling
    def post(self):
        """
        Receives post requests.
        :return:
        """

        def finish_billing(self, subscription_id, status):
            if status == 0:
                redis = databases.Redis.get_instance("redis-prebilling")
                redis.delete(subscription_id)
            self.service.add_to_file(self.application.settings, json_decode(self.request.body), status)
            self.service.add_to_stream(self.application.settings, json_decode(self.request.body), status)

        # Getting body
        body = json_decode(self.request.body)
        subscription_id = body['subscription_id']

        try:
            # Getting mandatory parameters
            amount = body['amount']
            code = body['code']
            msisdn = body['msisdn']
            mandate_id = body['mandate_id']
            product_id = body['product_id']
            reference_code = body['reference_code']
            service_id = body['service_id']
            tax_amount = body['tax_amount']
            transaction_status = body['transaction_status']

            # Getting optional parameter
            description = utils.get_optional_key(body, 'description')

            # Getting configs
            configs = self.service.get_configs(self.application.settings)

            # Getting access token
            token = self.service.get_token(configs, subscription_id)

            # Building request object
            request_url = self.service.get_url(configs, msisdn)
            request_header = self.service.get_header(token)
            request_body = self.service.get_body(msisdn, description, amount, code, tax_amount, mandate_id,
                                                 service_id, product_id, transaction_status, reference_code)
            request_object = self.service.get_request(request_url, request_body, request_header)

        except Exception as e:
            finish_billing(self, subscription_id, 0)

            # Log
            log.error("Could not send Billing request to partner. "
                      "Error: {0}. "
                      "Request body: {1}. "
                      "Operation Hash: {2}. "
                      .format(e, body, LOG_HASH_BILLING))

            # Return error
            return self.error({"message": "Internal Server Error", "success": 0}, 500)

        # Sending request to TIM
        try:
            response = yield AsyncHTTPClient().fetch(request_object, raise_error=False)

        except Exception as e:
            finish_billing(self, subscription_id, 0)

            # Log
            log.error("Could not send Billing request to partner. "
                      "Request URL: {0}. "
                      "Request body: {1}. "
                      "Request headers: {2}. "
                      "Error: {3}. "
                      "Operation Hash: {4}. "
                      .format(request_url, request_body, request_header, e, LOG_HASH_BILLING))

            # Return error
            return self.error({"success": 0, "message": "Could not send request"}, 500)

        # Handling response
        try:
            # Success
            if response.code == 201:
                finish_billing(self, subscription_id, 1)

                # Log
                log.info("Billing request sent to partner. "
                         "Request URL: {0}. "
                         "Request body: {1}. "
                         "Request headers: {2} "
                         "Response body: {3}. "
                         "Response code: {4}. "
                         "Operation Hash: {5}. "
                         .format(request_url, request_body, request_header, response.body, response.code,
                                 LOG_HASH_BILLING))

                # Return success
                return self.success({
                    "success": 1,
                    "account_type": self.service.get_account_type(response.headers),
                    "url": self.service.get_resource_url(json.loads(response.body.decode('utf-8')))
                })

            # Unauthorized
            if response.code == 401:
                finish_billing(self, subscription_id, 0)

                # Log
                log.error("Could not bill: unauthorized. "
                          "Request URL: {0}. "
                          "Request body: {1}. "
                          "Request headers: {2}. "
                          "Response body: {3}. "
                          "Response code: {4}. "
                          "Operation Hash: {5}. "
                          .format(request_url, request_body, request_header, response.body, response.code,
                                  LOG_HASH_BILLING))

                # Return error
                return self.error({"success": 0, 'message': "Unauthorized"}, response.code)

            # Bad Request
            if response.code == 400:
                finish_billing(self, subscription_id, 0)

                # Log
                log.error("Could not bill: bad request. "
                          "Request URL: {0}. "
                          "Request body: {1}. "
                          "Request headers: {2}. "
                          "Response body: {3}. "
                          "Response code: {4}. "
                          "Operation Hash: {5}. "
                          .format(request_url, request_body, request_header, response.body, response.code,
                                  LOG_HASH_BILLING))

                # Return error
                return self.error({
                    "success": 0, 
                    "code": self.service.get_code(json.loads(response.body.decode('utf-8')))
                })
            
            # Internal Error
            finish_billing(self, subscription_id, 0)

            # Log
            log.error("Could not bill. "
                      "Request URL: {0}. "
                      "Request body: {1}. "
                      "Request headers: {2}. "
                      "Response body: {3}. "
                      "Response code: {4}. "
                      "Operation Hash: {5}. "
                      .format(request_url, request_body, request_header, response.body, response.code,
                              LOG_HASH_BILLING))

            # Return error
            return self.error({
                "success": 0,
                "code": "IE",
                "message": "Internal error"
            }, 500)

        except Exception as e:
            finish_billing(self, subscription_id, 0)

            # Log
            log.error("Could not bill. "
                      "Request URL: {0}. "
                      "Request body: {1}. "
                      "Request headers: {2}. "
                      "Response body: {3}. "
                      "Response code: {4}. "
                      "Error: {5}. "
                      "Operation Hash: {6}. "
                      .format(request_url, request_body, request_header, response.body, response.code, e,
                              LOG_HASH_BILLING))

            # Return error
            return self.error({"success": 0, "message": "Could not bill"}, response.code)


class BillingStatusHandler(APIHandler):
    """
    Receives billing status requests from backend.
    """

    __urls__ = [r"/{0}/{1}/backend/billing/status(?:/)?".format(partner_name, api_version)]

    # Service
    service = BackendService.BillingStatusService

    @tornado.gen.coroutine
    @request
    @authenticate
    @validate_billing_status
    def post(self):
        """
        Receives post requests.
        :return:
        """

        # Getting body
        request_body = json_decode(self.request.body)

        try:
            msisdn = request_body['msisdn']
            transaction_id = request_body['transaction_id']

            # Getting configs
            configs = self.service.get_configs(self.application.settings)

            # Building request object
            request_url = self.service.get_url(configs, msisdn, transaction_id)
            request_header = self.service.get_header()
            request_object = self.service.get_request(request_url, request_header)

        except Exception as e:
            # Log
            log.error("Could not send BillingStatus request to partner. "
                      "Error: {0}. "
                      "Request body: {1}. "
                      "Operation Hash: {2}. "
                      .format(e, request_body, LOG_HASH_BILLING_STATUS))

            # Return error
            return self.error({"message": "Internal Server Error", "success": 0}, 500)

        # Sending request to TIM
        try:
            response = yield AsyncHTTPClient().fetch(request_object)

        except HTTPError as httpe:
            try:
                response_code = httpe.response.code
            except:
                response_code = 500

            # Log
            log.error("Could not check BillingStatus. "
                      "Request URL: {0}. "
                      "Request body: {1}. "
                      "Request headers: {2}. "
                      "Error: {3}. "
                      "Operation Hash: {4}. "
                      .format(request_url, request_body, request_header, httpe, LOG_HASH_BILLING_STATUS))

            # Return error
            return self.error({"message": "Could not check billing status.", "success": 0}, response_code)

        except Exception as e:
            # Log
            log.error("Could not send BillingStatus request to partner. "
                      "Request URL: {0}. "
                      "Request body: {1}. "
                      "Request headers: {2}. "
                      "Error: {3}. "
                      "Operation Hash: {4}. "
                      .format(request_url, request_body, request_header, e, LOG_HASH_BILLING_STATUS))

            # Return error
            return self.error({"message": "Could not check billing status.", "success": 0}, 500)

        # Handling response
        try:
            json_response = json.loads(response.body.decode('utf-8'))

            # Log
            log.info("BillingStatus checked. "
                     "Request URL: {0}. "
                     "Request body: {1}. "
                     "Request headers: {2}. "
                     "Response body: {3}. "
                     "Response code: {4}. "
                     "Operation Hash: {5}. "
                     .format(request_url, request_body, request_header, json_response, response.code,
                             LOG_HASH_BILLING_STATUS))

            # Return success
            return self.success({"success": 1, 'message': json_response})

        except Exception as e:
            # Log
            log.error("Could not check BillingStatus. "
                      "Request URL: {0}. "
                      "Request body: {1}. "
                      "Request headers: {2}. "
                      "Response body: {3}. "
                      "Response code: {4}. "
                      "Error: {5}. "
                      "Operation Hash: {6}. "
                      .format(request_url, request_body, request_header, response.body, response.code, e,
                              LOG_HASH_BILLING_STATUS))

            # Return error
            return self.error({"success": 0, "message": "Could not check billing status."}, response.code)


class MigrationHandler(APIHandler):
    """
    Receives migration requests from backend.
    """

    __urls__ = [r"/{0}/{1}/backend/migration(?:/)?".format(partner_name, api_version)]

    # Service
    service = BackendService.MigrationService

    @tornado.gen.coroutine
    @request
    @authenticate
    @validate_migration
    def post(self):
        """
        Receives post requests.
        :return:
        """

        # Getting body
        body = json_decode(self.request.body)

        try:
            msisdn = body['msisdn']
            application_id = body['application_id']

            # Getting configs
            configs = self.service.get_configs(self.application.settings)

            # Getting token
            token = self.service.get_token(configs)

            # Building request object
            request_url = self.service.get_url(configs)
            request_body = self.service.get_body(msisdn, application_id)
            request_header = self.service.get_header(token)
            request_object = self.service.get_request(request_url, request_body, request_header)

        except Exception as e:
            # Log
            log.error("Could not send Migration request to partner. "
                      "Error: {0}. "
                      "Request body: {1}. "
                      "Operation Hash: {2}. "
                      .format(e, body, LOG_HASH_MIGRATION))

            # Return error
            return self.error({"message": "Internal Server Error", "success": 0}, 500)

        # Sending request to TIM
        try:
            response = yield AsyncHTTPClient().fetch(request_object)

            # Log
            log.info("Migration done. "
                     "Request URL: {0}. "
                     "Request body: {1}. "
                     "Request headers: {2}. "
                     "Response body: {3}. "
                     "Response code: {4}. "
                     "Operation Hash: {5}. "
                     .format(request_url, request_body, request_header, "OK", response.code, LOG_HASH_MIGRATION))

            # Return success
            return self.success({"success": 1, 'message': 'OK'})

        except HTTPError as httpe:
            try:
                response_code = httpe.response.code
            except:
                response_code = 500

            # Log
            log.error("Could not migrate. "
                      "Request URL: {0}. "
                      "Request body: {1}. "
                      "Request headers: {2}. "
                      "Error: {3}. "
                      "Operation Hash: {4}. "
                      .format(request_url, request_body, request_header, httpe, LOG_HASH_MIGRATION))

            # Return error
            return self.error({"message": "Could not migrate", "success": 0}, response_code)

        except Exception as e:
            # Log
            log.error("Could not migrate. "
                      "Request URL: {0}. "
                      "Request body: {1}. "
                      "Request headers: {2}. "
                      "Error: {3}. "
                      "Operation Hash: {4}. "
                      .format(request_url, request_body, request_header, e, LOG_HASH_MIGRATION))

            # Return error
            return self.error({"message": "Could not migrate", "success": 0}, 500)
