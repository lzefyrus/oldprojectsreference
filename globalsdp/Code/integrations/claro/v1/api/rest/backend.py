from application.src.rewrites import APIHandler
from application.src.auth import authenticate
# from application.src.tps import tps
from application.src.request import request
from tornado.escape import json_decode
from integrations.claro.v1.services import backend as BackendService
from integrations.claro.v1.services.backend import MtService, MmsMtService, WapMtService, CheckCreditService,\
    BillingService, WibPushService
from integrations.claro.v1.validators.backend import validate_mt, validate_mms_mt, validate_wap_mt, \
    validate_check_credit, validate_billing, validate_wib_push
import logging
import tornado.gen
from tornado.httpclient import AsyncHTTPClient
from lxml import etree
from tornado.httpclient import HTTPError
import application.settings as settings

# Logging handler
log = logging.getLogger(__name__)

# Settings
partner_name = 'claro'
api_version = 'v1'
LOG_HASH = settings.LOG_HASHES[partner_name]


# Sends SMS
class MtHandler(APIHandler):
    __urls__ = [r"/{0}/{1}/backend/mt/sms".format(partner_name, api_version),
                r"/{0}/{1}/backend/mt/sms/".format(partner_name, api_version)]
    # Service DI
    service = MtService()

    # MT Hash Code for log identification
    MT_HASH = LOG_HASH["mt"]

    @tornado.gen.coroutine
    @request
    @authenticate
    @validate_mt
    # @tps
    def post(self):
        try:
            # Getting body
            body = json_decode(self.request.body)

            # Getting vars
            message = body['message']
            msisdn = body['msisdn']
            mode = body['mode']

            # Getting optional parameters
            try:
                source = body['source']
            except KeyError:
                source = None
            try:
                expiration = body['expiration']
            except KeyError:
                expiration = None

            # Getting access configs
            configs = self.service.get_configs(self.application.settings)

            # Building request object
            request_url = self.service.get_url(configs, message, msisdn, mode, source, expiration)
            request = self.service.get_request(request_url)

        except Exception as e:
            log.error("Internal Server Error: {0}."
                      "Operation Hash: {1}.".format(e, self.MT_HASH))
            return self.error({"message": "Internal Server Error", "success": 0}, 500)

        # Sending request to Claro asynchronously
        try:
            response = yield AsyncHTTPClient().fetch(request)

        except HTTPError as httpe:
            try:
                response_code = httpe.response.code
            except:
                response_code = 500
            log.error("Could not send MT request to partner. "
                      "Request URL: {0}."
                      "Error: {1}."
                      "Operation Hash: {2}."
                      .format(request_url, httpe, self.MT_HASH))
            return self.error({"message": "Could not access Claro service: {0}".format(httpe), "success": 0}, response_code)

        except Exception as e:
            log.error("Could not send MT request to partner. "
                      "Request URL: {0}."
                      "Error: {1}."
                      "Operation Hash: {2}."
                      .format(request_url, e, self.MT_HASH))
            return self.error({"message": "Could not access Claro service: {0}".format(e), "success": 0}, 500)

        # Get Signature response text and parse it to XML
        try:
            response_xml = etree.XML(response.body)

        except Exception as e:
            log.error("Claro sent an invalid response XML: {0}."
                      "Request URL: {1}."
                      "Error: {2}."
                      "Operation Hash: {3}."
                      .format(response.body, request_url, e, self.MT_HASH))
            return self.error({"message": "Claro sent an invalid response XML: {0}"
                              .format(response.body), "success": 0}, 500)

        # Build json return
        try:
            backend_response = BackendService.parse_response_to_json(response_xml, mode)

        except Exception as e:
            log.error("Could not parse XML Response to Json: {0}. "
                      "Reason: {1}."
                      "Request URL: {2}."
                      "Operation Hash: {3}.".format(response.body, e, request_url, self.MT_HASH))
            return self.error({"message": "Could not parse XML Response to Json", "success": 0}, 500)

        # Sending response
        log.info("MT request sent to partner. "
                 "Mode: {0}."
                 "Request URL: {1}."
                 "Response code: {2}."
                 "Response body: {3}."
                 "Operation Hash: {4}."
                 .format(mode, request_url, response.code, response.body, self.MT_HASH))
        return self.success({"message": backend_response, "success": backend_response["status"]})


# Sends SMS with GIF Image
class MmsMtHandler(APIHandler):
    __urls__ = [r"/{0}/{1}/backend/mt/mms".format(partner_name, api_version),
                r"/{0}/{1}/backend/mt/mms/".format(partner_name, api_version)]
    # Service DI
    service = MmsMtService()

    # MMS MT Hash Code for log identification
    MMS_MT_HASH = LOG_HASH["mms_mt"]

    @tornado.gen.coroutine
    @request
    @authenticate
    @validate_mms_mt
    # @tps
    def post(self):
        try:
            # Getting body
            body = json_decode(self.request.body)

            # Getting vars
            message = body['message']
            msisdn = body['msisdn']
            mode = body['mode']

            # Getting access configs
            configs = self.service.get_configs(self.application.settings)

            # Building request object
            request_url = self.service.get_url(configs, message, msisdn, mode)
            request = self.service.get_request(request_url)

        except Exception as e:
            log.error("Internal Server Error: {0}."
                      "Operation Hash: {1}.".format(e, self.MMS_MT_HASH))
            return self.error({"message": "Internal Server Error", "success": 0}, 500)

        # Sending request to Claro asynchronously
        try:
            response = yield AsyncHTTPClient().fetch(request)

        except HTTPError as httpe:
            try:
                response_code = httpe.response.code
            except:
                response_code = 500
            log.error("Could not send MMS MT request to partner. "
                      "Request URL: {0}."
                      "Error: {1}."
                      "Operation Hash: {2}."
                      .format(request_url, httpe, self.MMS_MT_HASH))
            return self.error({"message": "Could not access Claro service: {0}".format(httpe), "success": 0}, response_code)

        except Exception as e:
            log.error("Could not send MMS MT request to partner. "
                      "Request URL: {0}."
                      "Error: {1}."
                      "Operation Hash: {2}."
                      .format(request_url, e, self.MMS_MT_HASH))
            return self.error({"message": "Could not access Claro service: {0}".format(e), "success": 0}, 500)

        # Get Signature response text and parse it to XML
        try:
            response_xml = etree.XML(response.body)

        except Exception as e:
            log.error("Claro sent an invalid response XML: {0}."
                      "Request URL: {1}."
                      "Error: {2}."
                      "Operation Hash: {3}."
                      .format(response.body, request_url, e, self.MMS_MT_HASH))
            return self.error({"message": "Claro sent an invalid response XML", "success": 0}, 500)

        # Build json return
        try:
            backend_response = BackendService.parse_response_to_json(response_xml, mode)

        except Exception as e:
            log.error("Could not parse XML Response: {0}."
                      "Reason: {1}."
                      "Request URL: {2}."
                      "Operation Hash: {3}.".format(response.body, e, request_url, self.MMS_MT_HASH))
            return self.error({"message": "Could not parse XML Response", "success": 0}, 500)

        # Sending response
        log.info("MMS MT request sent to partner. "
                 "Request URL: {0}."
                 "Response code: {1}."
                 "Response body: {2}."
                 "Operation Hash: {3}."
                 .format(request_url, response.code, response.body, self.MMS_MT_HASH))
        return self.success({"message": backend_response, "success": backend_response["status"]})


# Sends SMS with Link
class WapMtHandler(APIHandler):
    __urls__ = [r"/{0}/{1}/backend/mt/wap".format(partner_name, api_version),
                r"/{0}/{1}/backend/mt/wap/".format(partner_name, api_version)]
    # Service DI
    service = WapMtService()

    # Wap MT Hash Code for log identification
    WAP_MT_HASH = LOG_HASH["wap_mt"]

    @tornado.gen.coroutine
    @request
    @authenticate
    @validate_wap_mt
    # @tps
    def post(self):
        try:
            # Getting body
            body = json_decode(self.request.body)

            # Getting vars
            message = body['message']
            msisdn = body['msisdn']
            url = body['url']
            mode = body['mode']

            # Getting optional parameters
            try:
                expiration = body['expiration']
            except KeyError:
                expiration = None

            # Getting access configs
            configs = self.service.get_configs(self.application.settings)

            # Building request object
            request_url = self.service.get_url(configs, message, msisdn, url, mode, expiration)
            request = self.service.get_request(request_url)

        except Exception as e:
            log.error("Internal Server Error: {0}".format(e))
            return self.error({"message": "Internal Server Error", "success": 0}, 500)

        # Sending request to Claro asynchronously
        try:
            response = yield AsyncHTTPClient().fetch(request)

        except HTTPError as httpe:
            try:
                response_code = httpe.response.code
            except:
                response_code = 500
            log.error("Could not send WAP MT request to partner. "
                      "Request URL: {0}."
                      "Error: {1}."
                      "Operation Hash: {2}."
                      .format(request_url, httpe, self.WAP_MT_HASH))
            return self.error({"message": "Could not access Claro service: {0}".format(httpe), "success": 0}, response_code)

        except Exception as e:
            log.error("Could not send WAP MT request to partner. "
                      "Request URL: {0}."
                      "Error: {1}."
                      "Operation Hash: {2}."
                      .format(request_url, e, self.WAP_MT_HASH))
            return self.error({"message": "Could not access Claro service: {0}".format(e), "success": 0}, 500)

        # Get Signature response text and parse it to XML
        try:
            response_xml = etree.XML(response.body)

        except Exception as e:
            log.error("Claro sent an invalid response XML: {0}."
                      "Request URL: {1}."
                      "Error: {2}."
                      "Operation Hash: {3}."
                      .format(response.body, request_url, e, self.WAP_MT_HASH))
            return self.error({"message": "Claro sent an invalid response XML: {0}"
                              .format(response.body), "success": 0}, 500)

        # Build json return
        try:
            backend_response = BackendService.parse_response_to_json(response_xml, mode)

        except Exception as e:
            log.error("Could not parse XML Response: {0}."
                      "Reason: {1}."
                      "Request URL: {2}."
                      "Operation Hash: {3}."
                      .format(response.body, e, request_url, self.WAP_MT_HASH))
            return self.error({"message": "Could not parse XML Response", "success": 0}, 500)

        # Sending response
        log.info("WAP MT request sent to partner. "
                 "Mode: {0}."
                 "Request URL: {1}."
                 "Response code: {2}."
                 "Response body: {3}."
                 "Operation Hash: {4}."
                 .format(mode, request_url, response.code, response.body, self.WAP_MT_HASH))
        return self.success({"message": backend_response, "success": backend_response["status"]})


# Checks if a customer has enough credit
class CheckCreditHandler(APIHandler):
    __urls__ = [r"/{0}/{1}/backend/check-credit".format(partner_name, api_version),
                r"/{0}/{1}/backend/check-credit/".format(partner_name, api_version)]
    # Service DI
    service = CheckCreditService()

    # Check Credit Hash Code for log identification
    CHECK_CREDIT_HASH = LOG_HASH["check_credit"]

    @tornado.gen.coroutine
    @request
    @authenticate
    @validate_check_credit
    # @tps
    def post(self):
        try:
            # Getting body
            body = json_decode(self.request.body)

            # Getting vars
            amount = body['amount']
            msisdn = body['msisdn']

            # Getting access configs
            configs = self.service.get_configs(self.application.settings)

            # Building request object
            request_url = self.service.get_url(configs, amount, msisdn)
            request = self.service.get_request(request_url)

        except Exception as e:
            log.error("Internal Server Error: {0}".format(e))
            return self.error({"message": "Internal Server Error", "success": 0}, 500)

        # Sending request to Claro asynchronously
        try:
            response = yield AsyncHTTPClient().fetch(request)

        except HTTPError as httpe:
            try:
                response_code = httpe.response.code
            except:
                response_code = 500
            log.error("Could not send CHECK CREDIT request to partner. "
                      "Request URL: {0}."
                      "Error: {1}."
                      "Operation Hash: {2}."
                      .format(request_url, httpe, self.CHECK_CREDIT_HASH))
            return self.error({"message": "Could not access Claro service: {0}".format(httpe), "success": 0}, response_code)

        except Exception as e:
            log.error("Could not send CHECK CREDIT request to partner. "
                      "Request URL: {0}."
                      "Error: {1}."
                      "Operation Hash: {2}."
                      .format(request_url, e, self.CHECK_CREDIT_HASH))
            return self.error({"message": "Could not access Claro service: {0}".format(e), "success": 0}, 500)

        # Get Signature response text and parse it to XML
        try:
            response_xml = etree.XML(response.body)

        except Exception as e:
            log.error("Claro sent an invalid response XML: {0}."
                      "Request URL: {1}."
                      "Error: {2}."
                      "Operation Hash: {3}."
                      .format(response.body, request_url, e, self.CHECK_CREDIT_HASH))
            return self.error({"message": "Claro sent an invalid response XML: {0}"
                              .format(response.body), "success": 0}, 500)

        # Build json return
        try:
            backend_response = BackendService.parse_response_to_json(response_xml)

        except Exception as e:
            log.error("Could not parse XML Response: {0}."
                      "Reason: {1}."
                      "Request URL: {2}."
                      "Operation Hash: {3}.".format(response.body, e, request_url, self.CHECK_CREDIT_HASH))
            return self.error({"message": "Could not parse XML Response", "success": 0}, 500)

        # Sending response
        log.info("CHECK CREDIT request sent to partner. "
                 "Request URL: {0}."
                 "Response code: {1}."
                 "Response body: {2}."
                 "Operation Hash: {3}."
                 .format(request_url, response.code, response.body, self.CHECK_CREDIT_HASH))
        return self.success({"message": backend_response, "success": backend_response["status"]})


# Sends a billing request to a given customer
class BillingHandler(APIHandler):
    __urls__ = [r"/{0}/{1}/backend/billing".format(partner_name, api_version),
                r"/{0}/{1}/backend/billing/".format(partner_name, api_version)]
    # Service DI
    service = BillingService()

    # Billing Hash Code for log identification
    BILLING_HASH = LOG_HASH["billing"]

    @tornado.gen.coroutine
    @request
    @authenticate
    @validate_billing
    # @tps
    def post(self):
        try:
            # Getting body
            body = json_decode(self.request.body)

            # Getting vars
            billing_code = body['billing_code']
            msisdn = body['msisdn']

            # Getting access configs
            configs = self.service.get_configs(self.application.settings)

            # Building request object
            request_url = self.service.get_url(configs, billing_code, msisdn)
            request = self.service.get_request(request_url)

        except Exception as e:
            log.error("Internal Server Error: {0}".format(e))
            return self.error({"message": "Internal Server Error", "success": 0}, 500)

        # Sending request to Claro asynchronously
        try:
            response = yield AsyncHTTPClient().fetch(request)

        except HTTPError as httpe:
            try:
                response_code = httpe.response.code
            except:
                response_code = 500
            log.error("Could not send BILLING request to partner. "
                      "Request URL: {0}."
                      "Error: {1}."
                      "Operation Hash: {2}."
                      .format(request_url, httpe, self.BILLING_HASH))
            return self.error({"message": "Could not access Claro service: {0}".format(httpe), "success": 0}, response_code)

        except Exception as e:
            log.error("Could not send BILLING request to partner. "
                      "Request URL: {0}."
                      "Error: {1}."
                      "Operation Hash: {2}."
                      .format(request_url, e, self.BILLING_HASH))
            return self.error({"message": "Could not access Claro service: {0}".format(e), "success": 0}, 500)

        # Get Signature response text and parse it to XML
        try:
            response_xml = etree.XML(response.body)

        except Exception as e:
            log.error("Claro sent an invalid response XML: {0}."
                      "Request URL: {1}."
                      "Error: {2}."
                      "Operation Hash: {3}."
                      .format(response.body, request_url, e, self.BILLING_HASH))
            return self.error({"message": "Claro sent an invalid response XML: {0}"
                              .format(response.body), "success": 0}, 500)

        # Build json return
        try:
            backend_response = BackendService.parse_response_to_json(response_xml)

        except Exception as e:
            log.error("Could not parse XML Response: {0}."
                      "Reason: {1}."
                      "Request URL: {2}."
                      "Operation Hash: {3}.".format(response.body, e, request_url, self.BILLING_HASH))
            return self.error({"message": "Could not parse XML Response", "success": 0}, 500)

        # Sending response
        log.info("BILLING request sent to partner. "
                 "Request URL: {0}."
                 "Response code: {1}."
                 "Response body: {2}."
                 "Operation Hash: {3}."
                 .format(request_url, response.code, response.body, self.BILLING_HASH))
        return self.success({"message": backend_response, "success": backend_response["status"]})


# Sends a wib push request to a given customer
class WibPushHandler(APIHandler):
    __urls__ = [r"/{0}/{1}/backend/wib-push".format(partner_name, api_version),
                r"/{0}/{1}/backend/wib-push/".format(partner_name, api_version)]
    # Service DI
    service = WibPushService()

    # Wib Push Hash Code for log identification
    WIB_PUSH_HASH = LOG_HASH["wib_push"]

    @tornado.gen.coroutine
    @request
    @authenticate
    @validate_wib_push
    # @tps
    def post(self):
        try:
            # Getting body
            body = json_decode(self.request.body)

            # Getting vars
            wml_push_code = body['wml_push_code']
            wml_push_code = self.service.get_xml(wml_push_code)
            msisdn = body['msisdn']
            mode = body['mode']

            # Getting access configs
            configs = self.service.get_configs(self.application.settings)

            # Building request object
            request_url = self.service.get_url(configs, wml_push_code, msisdn, mode)
            request = self.service.get_request(request_url)

        except Exception as e:
            log.error("Internal Server Error: {0}".format(e))
            return self.error({"message": "Internal Server Error", "success": 0}, 500)

        # Sending request to Claro asynchronously
        try:
            response = yield AsyncHTTPClient().fetch(request)

        except HTTPError as httpe:
            try:
                response_code = httpe.response.code
            except:
                response_code = 500
            log.error("Could not send WIB PUSH request to partner. "
                      "Request URL: {0}."
                      "Error: {1}."
                      "Operation Hash: {2}."
                      .format(request_url, httpe, self.WIB_PUSH_HASH))
            return self.error({"message": "Could not access Claro service: {0}".format(httpe), "success": 0}, response_code)

        except Exception as e:
            log.error("Could not send WIB PUSH request to partner. "
                      "Request URL: {0}."
                      "Error: {1}."
                      "Operation Hash: {2}."
                      .format(request_url, e, self.WIB_PUSH_HASH))
            return self.error({"message": "Could not access Claro service: {0}".format(e), "success": 0}, 500)

        # Get Signature response text and parse it to XML
        try:
            response_xml = etree.XML(response.body)

        except Exception as e:
            log.error("Claro sent an invalid response XML: {0}."
                      "Request URL: {1}."
                      "Error: {2}."
                      "Operation Hash: {3}."
                      .format(response.body, request_url, e, self.WIB_PUSH_HASH))
            return self.error({"message": "Claro sent an invalid response XML: {0}"
                              .format(response.body), "success": 0}, 500)

        # Build json return
        try:
            backend_response = BackendService.parse_response_to_json(response_xml)

        except Exception as e:
            log.error("Could not parse XML Response: {0}."
                      "Reason: {1}."
                      "Request URL: {2}."
                      "Operation Hash: {3}.".format(response.body, e, request_url, self.WIB_PUSH_HASH))
            return self.error({"message": "Could not parse XML Response", "success": 0}, 500)

        # Sending response
        log.info("WIB PUSH request sent to partner. "
                 "Request URL: {0}."
                 "Response code: {1}."
                 "Response body: {2}."
                 "Operation Hash: {3}."
                 .format(request_url, response.code, response.body, self.WIB_PUSH_HASH))
        return self.success({"message": backend_response, "success": backend_response["status"]})
