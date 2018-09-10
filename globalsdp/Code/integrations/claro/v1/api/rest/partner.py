import logging

from lxml import etree

from application.src.rewrites import APIHandler
from application.src.request import request
from integrations.claro.v1.services import partner as PartnerService
from integrations.claro.v1.services import backend as BackendService
from integrations.claro.v1.validators.partner import validate_mt_notification, validate_mms_mt_notification, \
    validate_wap_mt_notification, validate_wib_push_notification, validate_mo, validate_mms_mo
from integrations.claro.v1.utils.auth import authenticate
import application.settings as settings


# Logging handler
log = logging.getLogger(__name__)

partner_name = 'claro'
api_version = 'v1'
LOG_HASH = settings.LOG_HASHES[partner_name]


class MtNotificationHandler(APIHandler):
    __urls__ = [r"/{0}/{1}/notification/mt".format(partner_name, api_version),
                r"/{0}/{1}/notification/mt/".format(partner_name, api_version)]

    # MT Notification Hash Code for log identification
    MT_NOTIFICATION_HASH = LOG_HASH["mt_notification"]

    @request
    @validate_mt_notification
    @authenticate
    def post(self):
        try:
            # Getting body
            xml = etree.XML(self.request.body.decode('utf-8'))

            # Getting configs
            configs = PartnerService.get_mt_notification_configs(self.settings)

            # Parse XML to Json
            json = BackendService.parse_response_to_json(xml, 'sync')

            # Processing request
            try:
                PartnerService.notify_mt.delay(configs=configs, headers=None, body=json)
                return self.success({"success": "1", "message": "MT notification successfully received."})
            except Exception as e:
                log.error("Internal Server Error: {0}. "
                          "Operation Hash: {1}."
                          .format(e, self.MT_NOTIFICATION_HASH))
                return self.error({"success": "0", "message": "Could not send request. Internal error."}, 500)

        except Exception as e:
            log.error("Internal Server Error: {0}. "
                      "Operation Hash: {1}."
                      .format(e, self.MT_NOTIFICATION_HASH))
            return self.error({"success": 0, "message": "Internal Server Error"}, 500)


class MmsMtNotificationHandler(APIHandler):
    __urls__ = [r"/{0}/{1}/notification/mms".format(partner_name, api_version),
                r"/{0}/{1}/notification/mms/".format(partner_name, api_version)]

    # MMS MT Notification Hash Code for log identification
    MMS_MT_NOTIFICATION_HASH = LOG_HASH["mms_mt_notification"]

    @request
    @validate_mms_mt_notification
    @authenticate
    def post(self):
        try:
            # Getting body
            xml = etree.XML(self.request.body.decode('utf-8'))

            # Getting configs
            configs = PartnerService.get_mms_mt_notification_configs(self.settings)

            # Parse XML to Json
            json = BackendService.parse_response_to_json(xml, 'sync')

            # Processing request
            try:
                PartnerService.notify_mms_mt.delay(configs=configs, headers=None, body=json)
                return self.success({"success": "1", "message": "MMS MT notification successfully received."})
            except Exception as e:
                log.error("Internal Server Error: {0}. "
                          "Operation Hash: {1}."
                          .format(e, self.MMS_MT_NOTIFICATION_HASH))
                return self.error({"success": "0", "message": "Could not send request. Internal error."}, 500)

        except Exception as e:
            log.error("Internal Server Error: {0}. "
                      "Operation Hash: {1}."
                      .format(e, self.MMS_MT_NOTIFICATION_HASH))
            return self.error({"success": 0, "message": "Internal Server Error"}, 500)


class WapMtNotificationHandler(APIHandler):
    __urls__ = [r"/{0}/{1}/notification/wap".format(partner_name, api_version),
                r"/{0}/{1}/notification/wap/".format(partner_name, api_version)]

    # WAP MT Notification Hash Code for log identification
    WAP_MT_NOTIFICATION_HASH = LOG_HASH["wap_mt_notification"]

    @request
    @validate_wap_mt_notification
    @authenticate
    def post(self):
        try:
            # Getting body
            xml = etree.XML(self.request.body.decode('utf-8'))

            # Getting configs
            configs = PartnerService.get_wap_mt_notification_configs(self.settings)

            # Parse XML to Json
            json = BackendService.parse_response_to_json(xml, 'sync')

            # Processing request
            try:
                PartnerService.notify_wap_mt.delay(configs=configs, headers=None, body=json)
                return self.success({"success": "1", "message": "WAP MT notification successfully received."})
            except Exception as e:
                log.error("Internal Server Error: {0}. "
                          "Operation Hash: {1}."
                          .format(e, self.WAP_MT_NOTIFICATION_HASH))
                return self.error({"success": "0", "message": "Could not send request. Internal error."}, 500)

        except Exception as e:
            log.error("Internal Server Error: {0}. "
                      "Operation Hash: {1}."
                      .format(e, self.WAP_MT_NOTIFICATION_HASH))
            return self.error({"success": 0, "message": "Internal Server Error"}, 500)


class WibPushNotificationHandler(APIHandler):
    __urls__ = [r"/{0}/{1}/notification/wib-push".format(partner_name, api_version),
                r"/{0}/{1}/notification/wib-push/".format(partner_name, api_version)]

    # Wib Push Notification Hash Code for log identification
    WIB_PUSH_NOTIFICATION_HASH = LOG_HASH["wib_push_notification"]

    @request
    @validate_wib_push_notification
    @authenticate
    def post(self):
        try:
            # Getting body
            xml = etree.XML(self.request.body.decode('utf-8'))

            # Getting configs
            configs = PartnerService.get_wib_push_notification_configs(self.settings)

            # Parse XML to Json
            json = BackendService.parse_response_to_json(xml, 'sync')

            # Processing request
            try:
                PartnerService.notify_wib_push.delay(configs=configs, headers=None, body=json)
                return self.success({"success": "1", "message": "WIB PUSH notification successfully received."})
            except Exception as e:
                log.error("Internal Server Error: {0}. "
                          "Operation Hash: {1}."
                          .format(e, self.WIB_PUSH_NOTIFICATION_HASH))
                return self.error({"success": "0", "message": "Could not send request. Internal error."}, 500)

        except Exception as e:
            log.error("Internal Server Error: {0}. "
                      "Operation Hash: {1}."
                      .format(e, self.WIB_PUSH_NOTIFICATION_HASH))
            return self.error({"success": 0, "message": "Internal Server Error"}, 500)


class MoHandler(APIHandler):
    __urls__ = [r"/{0}/{1}/mo".format(partner_name, api_version),
                r"/{0}/{1}/mo/".format(partner_name, api_version)]

    # MO Hash Code for log identification
    MO_HASH = LOG_HASH["mo"]

    @request
    @validate_mo
    @authenticate
    def get(self):
        try:
            # Getting query string arguments
            text = self.get_argument('TEXT')
            id = self.get_argument('ID')
            msisdn = self.get_argument('ANUM')
            la = self.get_argument('BNUM')

            # Getting configs
            configs = PartnerService.get_mo_configs(self.settings)

            # Parse to Json
            json = PartnerService.get_mo_body(text, id, msisdn, la)

            # Processing request
            try:
                PartnerService.send_mo.delay(configs=configs, headers=None, body=json)
                return self.success({"success": "1", "message": "MO successfully received."})
            except Exception as e:
                log.error("Internal Server Error: {0}. "
                          "Operation Hash: {1}."
                          .format(e, self.MO_HASH))
                return self.error({"success": "0", "message": "Could not send request. Internal error."}, 500)

        except Exception as e:
            log.error("Internal Server Error: {0}. "
                      "Operation Hash: {1}."
                      .format(e, self.MO_HASH))
            return self.error({"success": 0, "message": "Internal Server Error"}, 500)


class MmsMoHandler(APIHandler):
    __urls__ = [r"/{0}/{1}/mo/mms".format(partner_name, api_version),
                r"/{0}/{1}/mo/mms/".format(partner_name, api_version)]

    # MO Hash Code for log identification
    MMS_MO_HASH = LOG_HASH["mms_mo"]

    @request
    @validate_mms_mo
    @authenticate
    def post(self):
        try:
            # Getting body
            xml = etree.XML(self.request.body.decode('utf-8'))

            # Getting configs
            configs = PartnerService.get_mms_mo_configs(self.settings)

            # Parse XML to Json
            json = PartnerService.get_mms_mo_body(xml)

            # Processing request
            try:
                PartnerService.send_mms_mo.delay(configs=configs, headers=None, body=json)
                return self.success({"success": "1", "message": "MMS MO successfully received."})
            except Exception as e:
                log.error("Internal Server Error: {0}. "
                          "Operation Hash: {1}."
                          .format(e, self.MMS_MO_HASH))
                return self.error({"success": "0", "message": "Could not send request. Internal error."}, 500)

        except Exception as e:
            log.error("Internal Server Error: {0}. "
                      "Operation Hash: {1}."
                      .format(e, self.MMS_MO_HASH))
            return self.error({"success": 0, "message": "Internal Server Error"}, 500)
