from application.src.rewrites import APIHandler
from application.src.auth import authenticate
from application.src.request import request
from application.src.exceptions import LaNotFoundException
from application.src import databases
from application.src.tps import tps
from application.src.request_id import request_id
from tornado.escape import json_decode
from integrations.oi.v1.services import backend as BackendService
from integrations.oi.v1.validators.backend import validate_mt, validate_billing
from integrations.oi.v1.utils.tps import has_available_tps, has_available_tps_for_mt
from integrations.oi.v1.utils.request_id import get_request_uid_func
from application.src.prebilling import prebilling
from tornado.httpclient import AsyncHTTPClient
from tornado.httpclient import HTTPError
from lxml import etree
import application.settings as settings
import logging
import tornado.gen
import requests
import time
from requests.exceptions import Timeout as TimeoutException

# Logging handler
log = logging.getLogger(__name__)

# Settings
partner_name = 'oi'
api_version = 'v1'
LOG_HASH = settings.LOG_HASHES[partner_name]

# 0 = "transação efetuada com sucesso" for Oi Billing system, all the other codes are linked to an error.
BILLING_SUCCESS_STATUS = 0


class MtHandler(APIHandler):
    __urls__ = [r"/{0}/{1}/backend/mt".format(partner_name, api_version),
                r"/{0}/{1}/backend/mt/".format(partner_name, api_version)]

    # MT Hash Code for log identification
    MT_HASH = LOG_HASH["mt"]

    @authenticate
    @validate_mt
    @request_id(get_request_uid_func, MT_HASH)
    @tps(tps_func=has_available_tps_for_mt)
    def get(self):
        # Redis for request Id
        try:
            redis = databases.Redis.get_instance("redis-request-id")
        except Exception as e:
            log.error("Could not send request to partner. Failed to connect to Redis. "
                      "Error: {0}. "
                      "Requested URL: {1}. "
                      "Operation Hash: {2}. "
                      .format(e, self.request.uri, self.MT_HASH).replace('\n',' '))
            return self.error({"success": 0, "message": "Failed to check or create request id. Request aborted."}, 500)

        # Get request_id
        uid = get_request_uid_func(self)

        try:
            # Service
            service = BackendService.MtService

            # Getting arguments
            la = self.get_argument('la', None, strip=True)
            msisdn = self.get_argument('msisdn', None, strip=True)
            text = self.get_argument('text', None, strip=True)
            charset = self.get_argument('charset', None, strip=True)
            udh = self.get_argument('udh', None, strip=True)
            dlrmask = self.get_argument('dlrmask', None, strip=True)
            dlrurl = self.get_argument('dlrurl', None, strip=True)
            validity = self.get_argument('validity', None, strip=True)
            mclass = self.get_argument('mclass', None, strip=True)

            # Getting configs
            try:
                configs = service.get_configs(self.application.settings, la)
            except LaNotFoundException as lanf:
                log.error("Could not send MT request to partner. "
                          "Error: {0}. "
                          "Request Id: {1}. "
                          "Operation Hash: {2}."
                          .format(lanf.__str__(), uid, self.MT_HASH).replace('\n',' '))
                redis.delete(uid)
                return self.error({"message": lanf.__str__(), "success": 0}, 500)

            # Building request object
            request_url = service.get_url(configs, la, msisdn, text, charset, udh, dlrmask, dlrurl,
                                          validity, mclass)

        except Exception as e:
            log.error("Could not send MT request to partner. "
                      "Error: {0}. "
                      "Request Id: {1}. "
                      "Operation Hash: {2}."
                      .format(e, uid, self.MT_HASH).replace('\n',' '))
            redis.delete(uid)
            return self.error({"message": "Internal Server Error", "success": 0}, 500)

        # Sending request to OI synchronously
        now = time.time()
        try:
            response = requests.get(url=request_url, timeout=10)

        except TimeoutException as te:
            log.error("Could not send MT request to partner: Timeout."
                      "Request URL: {0}. "
                      "Error: {1}. "
                      "Response time: {2}. "
                      "Request Id: {3}. "
                      "Operation Hash: {4}."
                      .format(request_url, te, time.time() - now, uid, self.MT_HASH).replace('\n',' '))

            # Solicitação do Denis, considerar como "sucesso" em caso de Timeout na plataforma da Oi para não duplicar envio de MT.
            redis.setex(uid, 1, settings.REQUEST_ID_PERIODICITY)
            return self.success({"success": 1, 'message': "Operation completed with timeout."})

        except Exception as e:
            log.error("Could not send MT request to partner. "
                      "Request URL: {0}. "
                      "Error: {1}. "
                      "Response time: {2}. "
                      "Request Id: {3}. "
                      "Operation Hash: {4}."
                      .format(request_url, e, time.time() - now, uid, self.MT_HASH).replace('\n',' '))

            redis.delete(uid)
            return self.error({"message": "Could not access the OI service: {0}".format(e), "success": 0}, 500)

        # Handling response
        try:
            log.info("MT request sent to partner. "
                     "Request URL: {0}. "
                     "Response body: {1}. "
                     "Response code: {2}. "
                     "Response time: {3}. "
                     "Request Id: {4}. "
                     "Operation Hash: {5}."
                     .format(request_url, str(response.text).replace("\n", "").replace(" ", ""),
                             response.status_code, time.time() - now, uid, self.MT_HASH).replace('\n',' '))
            try:
                json_response = response.text.decode('utf-8')
            except:
                json_response = response.text

            redis.setex(uid, 1, settings.REQUEST_ID_PERIODICITY)
            return self.success({"success": 1, 'message': json_response})

        except Exception as e:
            log.error("MT request sent to partner. But could not parse response. "
                      "Request URL: {0}. "
                      "Response body: {1}. "
                      "Response code: {2}. "
                      "Error: {3}. "
                      "Response time: {4}. "
                      "Request Id: {5}. "
                      "Operation Hash: {6}."
                      .format(request_url, str(response.text).replace("\n", "").replace(" ", ""),
                              response.status_code, e, time.time() - now, uid, self.MT_HASH).replace('\n',' '))
            redis.setex(uid, 1, settings.REQUEST_ID_PERIODICITY)
            return self.error({
                "success": 1,
                "message": "MT request sent to partner. But could not parse response. "}, response.status_code)


class BillingHandler(APIHandler):
    __urls__ = [r"/{0}/{1}/backend/billing".format(partner_name, api_version),
                r"/{0}/{1}/backend/billing/".format(partner_name, api_version)]

    # Billing Hash Code for log identification
    BILLING_HASH = LOG_HASH["billing"]

    # Service
    service = BackendService.BillingService()

    # Redis for prebilling
    redis = databases.Redis.get_instance("redis-prebilling")

    @authenticate
    @validate_billing
    # @prebilling(partner=partner_name, service=service, keys=['session_id'])
    @tps(tps_func=has_available_tps)
    def post(self):

        def finish_billing(self, key, status):
            if status == 0:
                self.redis.delete(key)
            self.service.save(self.application.settings, json_decode(self.request.body), status)

        try:
            # Getting body
            body = json_decode(self.request.body)

            # Getting mandatory parameters
            msisdn = body['msisdn']
            service_id = body['service_id']
            session_id = body['session_id']

            # Getting configs
            configs = self.service.get_configs(self.application.settings, service_id)

        except Exception as e:
            log.error("Could not send Billing request to partner. "
                      "Error: {0}. "
                      "Operation Hash: {1}. "
                      .format(e, self.BILLING_HASH).replace('\n',' '))
            finish_billing(self, '{0}:{1}'.format(msisdn, service_id), 0)
            return self.error({"message": "Internal Server Error", "success": 0}, 500)

        now = time.time()
        xml = self.service.get_request_body(str(configs['provider_code']), str(configs['password']),
                                            str(msisdn), str(service_id), str(session_id))
        url = configs['wsdl_billing']
        try:
            # Sending request to OI synchronously
            response = requests.post(
                url=url,
                data=xml,
                timeout=10)
        except Exception as e:
            log.error("Could not send Billing request to partner. "
                      "Request URL: {0}. "
                      "Request body: {1}. "
                      "Error: {2}. "
                      "Response time: {3}. "
                      "Operation Hash: {4}."
                      .format(url, xml, e, time.time() - now, self.BILLING_HASH).replace('\n',' '))
            finish_billing(self, '{0}:{1}'.format(msisdn, service_id), 0)
            return self.error({"message": str(e), "success": 0})

        # Handling response
        if response.status_code == 200:
            # Get response text and parse it to XML
            try:
                response_xml = etree.XML(self.service.prepare_xml(response.text))
            except Exception as e:
                log.error("Oi sent an invalid response XML: {0}. "
                          "Error: {1}. "
                          "Response time: {2}. "
                          "Operation Hash: {3}."
                          .format(response.text.replace("\n", ""), e, time.time() - now, self.BILLING_HASH).replace('\n',' '))
                finish_billing(self, '{0}:{1}'.format(msisdn, service_id), 0)
                return self.error({"message": "Oi sent an invalid response XML. "
                                              "Could not parse: {0}".format(response.text.replace("\n", "")), "success": 0}, 500)

            # Build json return
            try:
                backend_response = self.service.parse_response_to_json(response_xml)
            except Exception as e:
                log.error("Could not parse XML Response to JSON: {0}. "
                          "Reason: {1}."
                          "Response time: {2}. "
                          "Operation Hash: {3}"
                          .format(response.text.replace("\n", ""), e, time.time() - now, self.BILLING_HASH).replace('\n',' '))
                finish_billing(self, '{0}:{1}'.format(msisdn, service_id), 0)
                return self.error({"message": "Could not parse XML Response to Json", "success": 0}, 500)

            log.info("Billing request sent to partner. "
                     "Request URL: {0}. "
                     "Request body: {1}. "
                     "Response body: {2}. "
                     "Response code: {3}. "
                     "Response time: {4}. "
                     "Operation Hash: {5}."
                     .format(url, xml, response.text.replace("\n", ""), 200, time.time() - now, self.BILLING_HASH).replace('\n',' '))

            billing_status = 1 if int(backend_response['codigoStatus']) == BILLING_SUCCESS_STATUS else 0

            finish_billing(self, '{0}:{1}'.format(msisdn, service_id), billing_status)
            return self.success({"success": 1, "message": backend_response})
        else:
            log.info("Could not bill. "
                     "Request URL: {0}. "
                     "Request body: {1}. "
                     "Response body: {2}. "
                     "Response code: {3}. "
                     "Response time: {4}. "
                     "Operation Hash: {5}."
                     .format(url, xml, response.text.replace("\n", ""), 400, time.time() - now, self.BILLING_HASH).replace('\n',' '))
            finish_billing(self, '{0}:{1}'.format(msisdn, service_id), 0)
            try:
                response_xml = etree.XML(self.service.prepare_xml(response.text))
                backend_response = self.service.parse_error_response_to_json(response_xml)
            except:
                backend_response = 'Could not bill: {0}'.format(response.text.replace("\n", ""))
            return self.error({"success": 0, 'message': backend_response})


class CheckCreditHandler(APIHandler):
    __urls__ = [r"/{0}/{1}/backend/check-credit".format(partner_name, api_version),
                r"/{0}/{1}/backend/check-credit/".format(partner_name, api_version)]

    # Billing Hash Code for log identification
    CHECK_HASH = LOG_HASH["check_credit"]

    # Service
    service = BackendService.CheckCreditService()

    @authenticate
    @validate_billing
    @tps(tps_func=has_available_tps)
    def post(self):
        try:
            # Getting body
            body = json_decode(self.request.body)

            # Getting mandatory parameters
            msisdn = body['msisdn']
            service_id = body['service_id']
            session_id = body['session_id']

            # Getting configs
            configs = self.service.get_configs(self.application.settings, service_id)

        except Exception as e:
            log.error("Could not send Check Credit request to partner. "
                      "Error: {0}."
                      "Operation Hash: {1}"
                      .format(e, self.CHECK_HASH).replace('\n',' '))
            return self.error({"message": "Internal Server Error", "success": 0}, 500)

        now = time.time()
        xml = self.service.get_request_body(str(configs['provider_code']), str(configs['password']),
                                                str(msisdn), str(service_id), str(session_id))
        url = configs['wsdl_checkcredit']
        try:
            # Sending request to OI synchronously
            response = requests.post(
                url=url,
                data=xml,
                timeout=10)
        except Exception as e:
            log.error("Could not send Check Credit request to partner. "
                      "Request URL: {0}. "
                      "Request body: {1}. "
                      "Error: {2}. "
                      "Response time: {3}. "
                      "Operation Hash: {4}."
                      .format(url, xml, e, time.time() - now, self.CHECK_HASH).replace('\n',' '))
            return self.error({"message": str(e), "success": 0})

        # Handling response
        if response.status_code == 200:
            # Get response text and parse it to XML
            try:
                response_xml = etree.XML(self.service.prepare_xml(response.text))
            except Exception as e:
                log.error("Oi sent an invalid response XML: {0}."
                          "Error: {1}. "
                          "Response time: {2}. "
                          "Operation Hash: {3}."
                          .format(response.text.replace("\n", ""), e, time.time() - now, self.CHECK_HASH).replace('\n',' '))
                return self.error({"message": "Oi sent an invalid response XML. "
                                              "Could not parse: {0}".format(response.text.replace("\n", "")), "success": 0}, 500)

            # Build json return
            try:
                backend_response = self.service.parse_response_to_json(response_xml)
            except Exception as e:
                log.error("Could not parse XML Response to Json: {0}."
                          "Reason: {1}."
                          "Response time: {2}. "
                          "Operation Hash: {3}"
                          .format(response.text.replace("\n", ""), e, time.time() - now, self.CHECK_HASH).replace('\n',' '))
                return self.error({"message": "Could not parse XML Response to Json", "success": 0}, 500)

            log.info("Check Credit request sent to partner. "
                     "Request URL: {0}. "
                     "Request body: {1}. "
                     "Response body: {2}. "
                     "Response code: {3}. "
                     "Response time: {4}. "
                     "Operation Hash: {5}."
                     .format(url, xml, response.text.replace("\n", ""), 200, time.time() - now, self.CHECK_HASH).replace('\n',' '))
            return self.success({"success": 1, "message": backend_response})
        else:
            log.info("Could not check credit. "
                     "Request URL: {0}. "
                     "Request body: {1}. "
                     "Response body: {2}. "
                     "Response code: {3}. "
                     "Response time: {4}. "
                     "Operation Hash: {5}."
                     .format(url, xml, response.text.replace("\n", ""), 400, time.time() - now, self.CHECK_HASH).replace('\n',' '))
            try:
                response_xml = etree.XML(self.service.prepare_xml(response.text))
                backend_response = self.service.parse_error_response_to_json(response_xml)
            except:
                backend_response = 'Could not check credit: {0}'.format(response.text.replace("\n", ""))

            return self.error({"success": 0, 'message': backend_response})

