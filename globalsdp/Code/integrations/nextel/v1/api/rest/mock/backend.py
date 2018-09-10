"""
    This file intends to simulate all Backend's API behaviours which will be accessed by the SDP.
"""
from application.src.rewrites import APIHandler

partner_name = 'nextel'
api_version = 'v1'


class MockSignatureNotificationHandler(APIHandler):
    __urls__ = [r"/{0}-mock/backend/{1}/notification/signature".format(partner_name, api_version)]

    def post(self):
        return self.success({"success": "1", "message": "Signature notification received."})


class MockAuthenticationNotificationHandler(APIHandler):
    __urls__ = [r"/{0}-mock/backend/{1}/notification/authentication".format(partner_name, api_version)]

    def post(self):
        return self.success({"success": "1", "message": "Authentication notification received."})


class MockMOHandler(APIHandler):
    __urls__ = [r"/{0}-mock/backend/{1}/mo".format(partner_name, api_version)]

    def post(self):
        return self.success({"success": "1", "message": "Authentication notification received."})
