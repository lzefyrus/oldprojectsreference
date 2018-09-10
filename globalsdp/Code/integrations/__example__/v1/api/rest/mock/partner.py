"""
    This file intends to simulate all Partner's API behaviours which will be accessed by the SDP.
"""
from application.src.rewrites import APIHandler
from tornado.escape import json_decode
import logging

# Logging handler
log = logging.getLogger(__name__)

partner_name = '__example__'
api_version = 'v1'


class MockSignatureHandler(APIHandler):
    __urls__ = [r"/__example__-mock/v1/signature"]

    def post(self):
        log.info("Cancellation successfully done.")
        return self.success({"message": "success"})


class MockMtHandler(APIHandler):
    __urls__ = [r"/__example__-mock/v1/mt"]

    def post(self):
        log.info("Mt successfully sent.")
        return self.success({"message": "success"}, 201)
