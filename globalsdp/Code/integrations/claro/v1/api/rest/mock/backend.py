"""
    This file intends to simulate all Backend's API behaviours which will be accessed by the SDP.
"""
from application.src.rewrites import APIHandler

partner_name = 'claro'
api_version = 'v1'


class MockMtNotificationHandler(APIHandler):
    __urls__ = [r"/{0}-mock/backend/{1}/notification/mt".format(partner_name, api_version)]

    def post(self):
        return self.success({"success": "1", "message": "MT notification received."})


class MockMmsMtNotificationHandler(APIHandler):
    __urls__ = [r"/{0}-mock/backend/{1}/notification/mms".format(partner_name, api_version)]

    def post(self):
        return self.success({"success": "1", "message": "MMS MT notification received."})


class MockWapMtNotificationHandler(APIHandler):
    __urls__ = [r"/{0}-mock/backend/{1}/notification/wap".format(partner_name, api_version)]

    def post(self):
        return self.success({"success": "1", "message": "WAP MT notification received."})


class MockWibPushNotificationHandler(APIHandler):
    __urls__ = [r"/{0}-mock/backend/{1}/notification/wib-push".format(partner_name, api_version)]

    def post(self):
        return self.success({"success": "1", "message": "WIB PUSH notification received."})


class MockMoHandler(APIHandler):
    __urls__ = [r"/{0}-mock/backend/{1}/mo".format(partner_name, api_version)]

    def post(self):
        return self.success({"success": "1", "message": "MO notification received."})


class MockMmsMoHandler(APIHandler):
    __urls__ = [r"/{0}-mock/backend/{1}/mms".format(partner_name, api_version)]

    def post(self):
        return self.success({"success": "1", "message": "MMS MO notification received."})
