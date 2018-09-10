from application.src.rewrites import APIHandler
from application.src.auth import authenticate
# from application.src.tps import tps
from tornado.escape import json_decode
from integrations.__example__.v1.services import backend as BackendService
from integrations.__example__.v1.validators.backend import validate_cancellation, validate_mt
import logging

# Logging handler
log = logging.getLogger(__name__)

# Settings
partner_name = '__example__'
api_version = 'v1'


class CancellationHandler(APIHandler):
    __urls__ = [r"/{0}/{1}/backend/cancellation".format(partner_name, api_version),
                r"/{0}/{1}/backend/cancellation/".format(partner_name, api_version)]

    @authenticate
    @validate_cancellation
    # @tps
    def post(self):
        # Service DI
        service = BackendService.CancellationService()

        # Getting body
        body = json_decode(self.request.body)

        # Getting vars
        param1 = body['param1']
        param2 = body['param2']

        # Getting access configs
        configs = {
            'host': self.application.settings['config']['__example__/v1/host']['value'],
            'url': self.application.settings['config']['__example__/v1/cancellation/url']['value'],
        }

        # Processing request synchronously
        response = service.cancel(configs, param1, param2)

        # Sending response
        log.info("Cancellation request synchronously sent from backend to partner: {0}".format(param1))
        return self.success(response.json())


class MtHandler(APIHandler):
    __urls__ = [r"/{0}/{1}/backend/mt".format(partner_name, api_version),
                r"/{0}/{1}/backend/mt/".format(partner_name, api_version)]

    @authenticate
    @validate_mt
    # @tps
    def post(self):
        # Service DI
        service = BackendService.MtService()

        # Getting body
        body = json_decode(self.request.body)

        # Getting vars
        param1 = body['param1']
        param2 = body['param2']

        # Getting access configs
        configs = {
            'host': self.application.settings['config']['__example__/v1/host']['value'],
            'url': self.application.settings['config']['__example__/v1/mt/url']['value'],
        }

        # Processing request synchronously
        response = service.send_mt(configs, param1, param2)

        # Sending response
        log.info("Mt request synchronously sent from backend to partner: {0}")
        return self.success(response.json())
