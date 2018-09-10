from application.src.rewrites import APIHandler
from tornado.escape import json_decode
from integrations.__example__.v1.services import partner as PartnerService
from integrations.__example__.v1.validators.partner import validate_signature, validate_mo
import logging

# Logging handler
log = logging.getLogger(__name__)

partner_name = '__example__'
api_version = 'v1'


class SignatureHandler(APIHandler):
    __urls__ = [r"/{0}/{1}/signature".format(partner_name, api_version),
                r"/{0}/{1}/signature/".format(partner_name, api_version)]

    @validate_signature
    def post(self):
        # Getting header
        headers = self.request.headers

        # Getting body
        body = json_decode(self.request.body)

        # Getting vars
        param1 = body['param1']
        param2 = body['param2']

        # Processing request asynchronously
        PartnerService.signature.delay(param1, param2)

        # Sending response
        log.info("Signature successfully sent.")
        return self.success({"status": "OK", "message": "Signature successfully sent."})


class MoHandler(APIHandler):
    __urls__ = [r"/{0}/{1}/mo".format(partner_name, api_version),
                r"/{0}/{1}/mo/".format(partner_name, api_version)]

    @validate_mo
    def post(self):
        # Getting header
        headers = self.request.headers

        # Getting body
        body = json_decode(self.request.body)

        # Getting vars
        param1 = body['param1']
        param2 = body['param2']

        # Processing request asynchronously
        PartnerService.send_mo.delay(param1, param2)

        # Sending response
        log.info("Mo successfully sent.")
        return self.success({"status": "OK", "message": "Mo successfully sent."})
