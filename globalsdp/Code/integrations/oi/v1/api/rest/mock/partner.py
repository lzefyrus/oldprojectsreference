"""
    This file intends to simulate all TIM API behaviours which will be accessed by the Gateway.
"""
from application.src.rewrites import APIHandler
from tornado.escape import json_decode
import logging
import time

# Logging handler
log = logging.getLogger(__name__)

partner_name = 'oi'
api_version = 'v1'


class MockCancellationHandler(APIHandler):
    __urls__ = [r"/{0}-mock/{1}/mt".format(partner_name, api_version)]

    def get(self):
        return self.success({"message": "success"})
