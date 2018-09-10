from application.src.rewrites import APIHandler
from application.src.auth import authenticate
# from application.src.tps import tps
from application.src.request import request
from application.src.exceptions import InvalidRequestException
from tornado.escape import json_decode
from integrations.algar.v1.services import backend as BackendService
from integrations.algar.v1.validators.backend import validate_signature, validate_cancellation, validate_mt, \
    validate_billing
import logging
import tornado.gen
from tornado.httpclient import AsyncHTTPClient
from lxml import etree
from tornado.httpclient import HTTPError
import application.settings as settings
import uuid

# Logging handler
log = logging.getLogger(__name__)

# Settings
partner_name = 'algar'
api_version = 'v1'
LOG_HASH = settings.LOG_HASHES[partner_name]


class SignatureHandler(APIHandler):
    __urls__ = [r"/{0}/{1}/backend/signature".format(partner_name, api_version),
                r"/{0}/{1}/backend/signature/".format(partner_name, api_version)]
    # Service DI
    service = BackendService.SignatureService()

    # Signature Hash Code for log identification
    SIGNATURE_HASH = LOG_HASH["signature"]

    @tornado.gen.coroutine
    @request
    @authenticate
    @validate_signature
    # @tps
    def post(self):
        try:
            # Getting body
            body = json_decode(self.request.body)

            # Getting vars
            channel_id = body['channel_id']
            la = body['la']
            msisdn = body['msisdn']

            # Getting optional parameters
            try:
                app_specific = body['app_specific']
            except KeyError:
                app_specific = None
            try:
                subscription_type = body['subscription_type']
            except KeyError:
                subscription_type = None
            try:
                interface = body['interface']
            except KeyError:
                interface = None

            # Getting access configs
            configs = self.service.get_configs(self.application.settings, la)

            # Building request object
            request_url = self.service.get_url(configs)
            headers = BackendService.get_headers(configs)
            xml = self.service.get_body(configs, channel_id, la, msisdn, app_specific, interface, subscription_type)
            request = self.service.get_request(request_url, headers, xml)

        except Exception as e:
            log.error("Internal Server Error. "
                      "Error: {0}."
                      "Operation Hash: {1}."
                      .format(e, self.SIGNATURE_HASH))
            return self.error({"message": "Internal Server Error", "success": 0}, 500)

        # Sending request to Tangram asynchronously
        try:
            response = yield AsyncHTTPClient().fetch(request)

        except HTTPError as httpe:
            try:
                response_code = httpe.response.code
            except:
                response_code = 500
            log.error("Could not access algar service. "
                      "Request URL: {0}."
                      "Request Headers: {1}."
                      "Request Body: {2}."
                      "Error: {3}."
                      "Operation Hash: {4}."
                      .format(request_url, headers, xml, httpe, self.SIGNATURE_HASH))
            return self.error({"message": "Could not access the algar service: {0}".format(httpe), "success": 0}, response_code)

        except Exception as e:
            log.error("Could not access algar service. "
                      "Request URL: {0}."
                      "Request Headers: {1}."
                      "Request Body: {2}."
                      "Error: {3}."
                      "Operation Hash: {4}."
                      .format(request_url, headers, xml, e, self.SIGNATURE_HASH))
            return self.error({"message": "Could not access the algar service: {0}".format(e), "success": 0}, 500)

        # Get Signature response text and parse it to XML
        try:
            response_xml = etree.XML(response.body)

        except Exception as e:
            log.error("Tangram sent an invalid response XML. "
                      "Request URL: {0}."
                      "Request Headers: {1}."
                      "Request Body: {2}."
                      "Response Body: {3}."
                      "Error: {4}."
                      "Operation Hash: {5}."
                      .format(request_url, headers, xml, response.body, e, self.SIGNATURE_HASH))
            return self.error({"message": "Tangram sent an invalid response XML", "success": 0}, 500)

        # Check if occurred some Bad request
        response_has_errors = BackendService.response_has_errors(response_xml)
        if response_has_errors:
            log.error("Signature request was not sent from backend to partner. "
                      "Request URL: {0}."
                      "Request Headers: {1}."
                      "Request Body: {2}."
                      "Response Body: {3}."
                      "Error: {4}."
                      "Operation Hash: {5}."
                      .format(request_url, headers, xml, response.body, response_has_errors, self.SIGNATURE_HASH))
            return self.error({"message": response_has_errors, "success": 0}, 400)

        # Build json return
        try:
            backend_response = self.service.parse_response_to_json(response_xml)

        except Exception as e:
            log.error("Could not parse XML Response to Json. "
                      "Request URL: {0}."
                      "Request Headers: {1}."
                      "Request Body: {2}."
                      "Response Body: {3}."
                      "Error: {4}."
                      "Operation Hash: {5}."
                      .format(request_url, headers, xml, response.body, e, self.SIGNATURE_HASH))
            return self.error({"message": "Could not parse XML Response to Json", "success": 0}, 500)

        # Sending response
        log.info("Signature request asynchronously sent to partner. "
                 "Request URL: {0}."
                 "Request Headers: {1}."
                 "Request Body: {2}."
                 "Response Code: {3}."
                 "Response Body: {4}."
                 "Operation Hash: {5}."
                 .format(request_url, headers, xml, response.code, response.body, self.SIGNATURE_HASH))

        return self.success({"message": backend_response, "success": 1})


class CancellationHandler(APIHandler):
    __urls__ = [r"/{0}/{1}/backend/cancellation".format(partner_name, api_version),
                r"/{0}/{1}/backend/cancellation/".format(partner_name, api_version)]
    # Service DI
    service = BackendService.CancellationService()

    # Cancellation Hash Code for log identification
    CANCELLATION_HASH = LOG_HASH["cancellation"]

    @tornado.gen.coroutine
    @request
    @authenticate
    @validate_cancellation
    # @tps
    def post(self):
        try:
            # Getting body
            body = json_decode(self.request.body)

            # Getting vars
            channel_id = body['channel_id']
            msisdn = body['msisdn']
            la = body['la']

            # Getting optional parameters
            try:
                subscription_type = body['subscription_type']
            except KeyError:
                subscription_type = None
            try:
                interface = body['interface']
            except KeyError:
                interface = None

            # Getting access configs
            configs = self.service.get_configs(self.application.settings, la)

            # Building request object
            request_url = self.service.get_url(configs)
            headers = BackendService.get_headers(configs)
            xml = self.service.get_body(configs, channel_id, msisdn, interface, subscription_type)
            request = self.service.get_request(request_url, headers, xml)

        except Exception as e:
            log.error("Internal Server Error. "
                      "Error: {0}."
                      "Operation Hash: {1}."
                      .format(e, self.CANCELLATION_HASH))
            return self.error({"message": "Internal Server Error", "success": 0}, 500)

        # Sending request to Tangram asynchronously
        try:
            response = yield AsyncHTTPClient().fetch(request)

        except HTTPError as httpe:
            try:
                response_code = httpe.response.code
            except:
                response_code = 500
            log.error("Could not access the algar service. "
                      "Request URL: {0}."
                      "Request Headers: {1}."
                      "Request Body: {2}."
                      "Error: {3}."
                      "Operation Hash: {4}."
                      .format(request_url, headers, xml, httpe, self.CANCELLATION_HASH))
            return self.error({"message": "Could not access the algar service: {0}".format(httpe), "success": 0}, response_code)

        except Exception as e:
            log.error("Could not access the algar service: {0}."
                      "Operation Hash: {1}"
                      .format(e, self.CANCELLATION_HASH))
            return self.error({"message": "Could not access the algar service: {0}".format(e), "success": 0}, 500)

        # Get Signature response text and parse it to XML
        try:
            response_xml = etree.XML(response.body)

        except Exception as e:
            log.error("Tangram sent an invalid response XML. "
                      "Request URL: {0}."
                      "Request Headers: {1}."
                      "Request Body: {2}."
                      "Error: {3}."
                      "Operation Hash: {4}."
                      .format(request_url, headers, xml, response.body, e, self.CANCELLATION_HASH))
            return self.error({"message": "Tangram sent an invalid response XML", "success": 0}, 500)

        # Check if occurred some Bad request
        response_has_errors = BackendService.response_has_errors(response_xml)
        if response_has_errors:
            log.error("Cancellation request was not sent to partner. "
                      "Request URL: {0}."
                      "Request Headers: {1}."
                      "Request Body: {2}."
                      "Response Body: {3}."
                      "Error: {4}."
                      "Operation Hash: {5}."
                      .format(request_url, headers, xml, response.body, response_has_errors, self.CANCELLATION_HASH))
            return self.error({"message": response_has_errors, "success": 0}, 400)

        # Build json return
        try:
            backend_response = self.service.parse_response_to_json(response_xml)
        except Exception as e:
            log.error("Could not parse XML Response to Json. "
                      "Request URL: {0}."
                      "Request Headers: {1}."
                      "Request Body: {2}."
                      "Response Body: {3}."
                      "Error: {4}."
                      "Operation Hash: {5}."
                      .format(request_url, headers, xml, response.body, e, self.CANCELLATION_HASH))
            return self.error({"message": "Could not parse XML Response to Json", "success": 0}, 500)

        # Sending response
        log.info("Cancellation request asynchronously sent to partner. "
                 "Request URL: {0}."
                 "Request Headers: {1}."
                 "Request Body: {2}."
                 "Response Body: {3}."
                 "Error: {4}."
                 "Operation Hash: {5}."
                 .format(request_url, headers, xml, response.code, response.body, self.CANCELLATION_HASH))
        return self.success({"message": backend_response, "success": 1})


class MtHandler(APIHandler):
    __urls__ = [r"/{0}/{1}/backend/mt".format(partner_name, api_version),
                r"/{0}/{1}/backend/mt/".format(partner_name, api_version)]
    # Service DI
    service = BackendService.MtService()

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
            la = body['la']
            msisdns = body['msisdns']
            channel_id = body['channel_id']
            message = body['message']
            app_request_id = uuid.uuid4().hex
            # app_request_id = '02038834'

            # Getting optional parameters
            try:
                message_header = body['message_header']
            except KeyError:
                message_header = ""
            try:
                # Dict with "relative" value (true or false) and "validity" itself (an int representing seconds in case
                # of relative=true or date when relative=false)
                validity = body['validity']
            except KeyError:
                validity = {
                    "validity": "",
                    "relative": ""
                }
            try:
                # Dict with "relative" value (true or false) and "validity" itself (an int representing seconds in case
                # of relative=true or date when relative=false)
                schedule = body['schedule']
            except KeyError:
                schedule = {
                    "schedule": "",
                    "relative": ""
                }
            try:
                # Boolean, send later MT notification or not
                notification = body['notification']
            except KeyError:
                notification = ""
            try:
                # Dict with "max" (int) and "interval" (int in seconds)
                retries = body['retries']
            except KeyError:
                retries = {
                    "max": "",
                    "interval": ""
                }
            try:
                mo_message_id = body['mo_message_id']
            except KeyError:
                mo_message_id = ""
            try:
                app_specific = body['app_specific']
            except KeyError:
                app_specific = ""

            # Getting access configs
            configs = self.service.get_configs(self.application.settings, la)

            # Building request object
            request_url = self.service.get_url(configs)
            headers = BackendService.get_headers(configs)
            try:
                xml = self.service.get_body(configs, la, msisdns, channel_id, message, message_header,
                                                 validity, schedule, notification, retries, mo_message_id, app_specific, app_request_id)
            except InvalidRequestException as ire:
                log.error("Invalid Request. "
                          "Error: {0}."
                          "Operation Hash: {1}."
                          .format(ire, self.MT_HASH))
                return self.error({"message": "Invalid Request: {0}".format(ire), "success": 0}, 400)

            request = self.service.get_request(request_url, headers, xml)

        except Exception as e:
            log.error("Internal Server Error. "
                      "Error: {0}."
                      "Operation Hash: {1}."
                      .format(e, self.MT_HASH))
            return self.error({"message": "Internal Server Error", "success": 0}, 500)

        # Sending request to Tangram asynchronously
        try:
            response = yield AsyncHTTPClient().fetch(request)

        except HTTPError as httpe:
            try:
                response_code = httpe.response.code
            except:
                response_code = 500
            log.error("Could not access the algar service. "
                      "Request URL: {0}."
                      "Request Headers: {1}."
                      "Request Body: {2}"
                      "Error: {3}."
                      "Operation Hash: {4}."
                      .format(request_url, headers, xml, httpe, self.MT_HASH))
            return self.error({"message": "Could not access the algar service: {0}".format(httpe), "success": 0}, response_code)

        except Exception as e:
            log.error("Could not access the algar service. "
                      "Request URL: {0}."
                      "Request Headers: {1}."
                      "Request Body: {2}"
                      "Error: {3}."
                      "Operation Hash: {4}."
                      .format(request_url, headers, xml, e, self.MT_HASH))
            return self.error({"message": "Could not access the algar service: {0}".format(e), "success": 0}, 500)

        # Get Signature response text and parse it to XML
        try:
            response_xml = etree.XML(response.body.decode('utf-8'))

        except Exception as e:
            log.error("Tangram sent an invalid response XML. "
                      "Request URL: {0}."
                      "Request Headers: {1}."
                      "Request Body: {2}."
                      "Response Body: {3}."
                      "Error: {4}."
                      "Operation Hash: {5}."
                      .format(request_url, headers, xml, response.body, e, self.MT_HASH))
            return self.error({"message": "Tangram sent an invalid response XML", "success": 0}, 500)

        # Check if occurred some Bad request
        response_has_errors = BackendService.response_has_errors(response_xml)
        if response_has_errors:
            log.error("MT request was not sent to partner. "
                      "Request URL: {0}."
                      "Request Headers: {1}."
                      "Request Body: {2}."
                      "Response Body: {3}."
                      "Error: {4}."
                      "Operation Hash: {5}."
                      .format(request_url, headers, xml, response.body, response_has_errors, self.MT_HASH))
            return self.error({"message": response_has_errors, "success": 0}, 400)

        # Build json return
        try:
            backend_response = self.service.parse_response_to_json(response_xml)

        except Exception as e:
            log.error("Could not parse XML Response to Json. "
                      "Request URL: {0}."
                      "Request Headers: {1}."
                      "Request Body: {2}."
                      "Response Body: {3}."
                      "Error: {4}."
                      "Operation Hash: {5}."
                      .format(request_url, headers, xml, response.body, e, self.MT_HASH))
            return self.error({"message": "Could not parse XML Response to Json", "success": 0}, 500)

        # Sending response
        log.info("MT request synchronously sent to partner. "
                 "Request URL: {0}."
                 "Request Headers: {1}."
                 "Request Body: {2}."
                 "Response Code: {3}."
                 "Response Body: {4}."
                 "Operation Hash: {5}."
                 .format(request_url, headers, xml, response.code, response.body, self.MT_HASH))
        return self.success({"message": backend_response, "success": 1})


class BillingHandler(APIHandler):
    __urls__ = [r"/{0}/{1}/backend/billing".format(partner_name, api_version),
                r"/{0}/{1}/backend/billing/".format(partner_name, api_version)]
    # Service DI
    service = BackendService.BillingService()

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
            channel_id = body['channel_id']
            la = body['la']
            msisdn = body['msisdn']

            # Getting optional parameters
            try:
                subscription_type = body['subscription_type']
            except KeyError:
                subscription_type = None
            try:
                interface = body['interface']
            except KeyError:
                interface = None
            try:
                item = body['item']
            except KeyError:
                item = None

            # Getting access configs
            configs = self.service.get_configs(self.application.settings, la)

            # Building request object
            request_url = self.service.get_url(configs)
            headers = BackendService.get_headers(configs)

            try:
                xml = self.service.get_body(configs, channel_id, la, msisdn, item, subscription_type, interface)

            except Exception as ire:
                log.error("Invalid Request. "
                          "Error: {0}."
                          "Operation Hash: {1}."
                          .format(ire, self.BILLING_HASH))
                return self.error({"message": "Invalid Request: {0}".format(ire), "success": 0}, 400)

            request = self.service.get_request(request_url, headers, xml)
        except Exception as e:
            log.error("Internal Server Error. "
                      "Error: {0}."
                      "Operation Hash: {1}."
                      .format(e, self.BILLING_HASH))
            return self.error({"message": "Internal Server Error", "success": 0}, 500)

        # Sending request to Tangram asynchronously
        try:
            response = yield AsyncHTTPClient().fetch(request)

        except HTTPError as httpe:
            try:
                response_code = httpe.response.code
            except:
                response_code = 500
            log.error("Could not access the algar service. "
                      "Request URL: {0}."
                      "Request Headers: {1}."
                      "Request Body: {2}."
                      "Error: {3}."
                      "Operation Hash: {4}"
                      .format(request_url, headers, xml, httpe, self.BILLING_HASH))
            return self.error({"message": "Could not access the algar service: {0}".format(httpe), "success": 0}, response_code)

        except Exception as e:
            log.error("Could not access the algar service. "
                      "Request URL: {0}."
                      "Request Headers: {1}."
                      "Request Body: {2}."
                      "Error: {3}."
                      "Operation Hash: {4}."
                      .format(request_url, headers, xml, e, self.BILLING_HASH))
            return self.error({"message": "Could not access the algar service: {0}".format(e), "success": 0}, 500)

        # Get Signature response text and parse it to XML
        try:
            response_xml = etree.XML(response.body)

        except Exception as e:
            log.error("Tangram sent an invalid response XML. "
                      "Request URL: {0}."
                      "Request Headers: {1}."
                      "Request Body: {2}."
                      "Response Body: {3}."
                      "Error: {4}."
                      "Operation Hash: {5}."
                      .format(request_url, headers, xml, response.body, e, self.BILLING_HASH))
            return self.error({"message": "Tangram sent an invalid response XML", "success": 0}, 500)

        # Check if occurred some Bad request
        response_has_errors = BackendService.response_has_errors(response_xml)
        if response_has_errors:
            log.error("Billing request was not sent to partner. "
                      "Request URL: {0}."
                      "Request Headers: {1}."
                      "Request Body: {2}."
                      "Response Body: {3}."
                      "Error: {4}."
                      "Operation Hash: {5}."
                      .format(request_url, headers, xml, response.body, response_has_errors, self.BILLING_HASH))
            return self.error({"message": response_has_errors, "success": 0}, 400)

        # Build json return
        try:
            backend_response = self.service.parse_response_to_json(response_xml)

        except Exception as e:
            log.error("Could not parse XML Response to Json. "
                      "Request URL: {0}."
                      "Request Headers: {1}."
                      "Request Body: {2}."
                      "Response Body: {3}."
                      "Error: {4}."
                      "Operation Hash: {5}."
                      .format(request_url, headers, xml, response.body, e, self.BILLING_HASH))
            return self.error({"message": "Could not parse XML Response to Json", "success": 0}, 500)

        # Sending response
        log.info("Billing request synchronously sent to partner. "
                 "Request URL: {0}."
                 "Request Headers: {1}."
                 "Request Body: {2}."
                 "Response Code: {3}."
                 "Response Body: {4}."
                 "Operation Hash: {5}."
                 .format(request_url, headers, xml, response.code, response.body, self.BILLING_HASH))
        return self.success({"message": backend_response, "success": 1})
