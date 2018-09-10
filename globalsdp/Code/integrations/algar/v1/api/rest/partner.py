from application.src.rewrites import APIHandler
from application.src.request import request
from integrations.algar.v1.services import partner as PartnerService
from integrations.algar.v1.validators.partner import validate_notification, validate_mo
from lxml import etree
import logging
import application.settings as settings


# Logging handler
log = logging.getLogger(__name__)

partner_name = 'algar'
api_version = 'v1'
LOG_HASH = settings.LOG_HASHES[partner_name]


class SignatureNotificationHandler(APIHandler):
    __urls__ = [r"/{0}/{1}/notification/signature".format(partner_name, api_version),
                r"/{0}/{1}/notification/signature/".format(partner_name, api_version)]

    # Notification Hash Code for log identification
    NOTIFICATION_HASH = LOG_HASH["signature_notification"]
    NOTIFICATION_TYPE = "signature"

    @request
    @validate_notification(type=NOTIFICATION_TYPE)
    def post(self):
        try:
            # Getting body
            try:
                xml = etree.XML(PartnerService.prepare_xml(str(self.request.body.decode("utf-8"))))
            except:
                xml = etree.XML(PartnerService.prepare_xml(str(self.request.body)))

            # Getting configs
            configs = PartnerService.get_signature_configs(self.settings)

            # Parse XML to Json
            json = PartnerService.get_notification_body(xml)

            # Processing request
            try:
                PartnerService.notify.delay(configs=configs, headers={"Content-Type": "application/json"}, body=json, type=self.NOTIFICATION_TYPE)
                xml_response = PartnerService.get_notification_response(configs['description_text'], json, "true", 0)
                return self.success(xml_response)

            except Exception as e:
                log.error("Internal Server Error: {0}."
                          "Operation Hash: {1}."
                          .format(e, self.NOTIFICATION_HASH))
                xml_response = PartnerService.get_notification_error_response(configs['description_error_text'], "false", 500)
                return self.error(xml_response, 500)

        except Exception as e:
            log.error("Internal Server Error: {0}."
                      "Operation Hash: {1}."
                      .format(e, self.NOTIFICATION_HASH))
            xml_response = PartnerService.get_notification_error_response(configs['description_error_text'], "false", 500)
            return self.error(xml_response, 500)


class CancellationNotificationHandler(APIHandler):
    __urls__ = [r"/{0}/{1}/notification/cancellation".format(partner_name, api_version),
                r"/{0}/{1}/notification/cancellation/".format(partner_name, api_version)]

    # Notification Hash Code for log identification
    NOTIFICATION_HASH = LOG_HASH["cancellation_notification"]
    NOTIFICATION_TYPE = "cancellation"

    @request
    @validate_notification(type=NOTIFICATION_TYPE)
    def post(self):
        try:
            # Getting body
            try:
                xml = etree.XML(PartnerService.prepare_xml(str(self.request.body.decode("utf-8"))))
            except:
                xml = etree.XML(PartnerService.prepare_xml(str(self.request.body)))

            # Getting configs
            configs = PartnerService.get_cancellation_configs(self.settings)

            # Parse XML to Json
            json = PartnerService.get_notification_body(xml)

            # Processing request
            try:
                PartnerService.notify.delay(configs=configs, headers={"Content-Type": "application/json"}, body=json, type=self.NOTIFICATION_TYPE)
                xml_response = PartnerService.get_notification_response(configs['description_text'], json, "true", 0)
                return self.success(xml_response)

            except Exception as e:
                log.error("Internal Server Error: {0}."
                          "Operation Hash: {1}."
                          .format(e, self.NOTIFICATION_HASH))
                xml_response = PartnerService.get_notification_error_response(configs['description_error_text'], "false", 500)
                return self.error(xml_response, 500)

        except Exception as e:
            log.error("Internal Server Error: {0}."
                      "Operation Hash: {1}."
                      .format(e, self.NOTIFICATION_HASH))
            xml_response = PartnerService.get_notification_error_response(configs['description_error_text'], "false", 500)
            return self.error(xml_response, 500)


class AuthenticationNotificationHandler(APIHandler):
    __urls__ = [r"/{0}/{1}/notification/authentication".format(partner_name, api_version),
                r"/{0}/{1}/notification/authentication/".format(partner_name, api_version)]

    # Notification Hash Code for log identification
    NOTIFICATION_HASH = LOG_HASH["auth_notification"]
    NOTIFICATION_TYPE = "auth"

    @request
    @validate_notification(type=NOTIFICATION_TYPE)
    def post(self):
        try:
            # Getting body
            try:
                xml = etree.XML(PartnerService.prepare_xml(str(self.request.body.decode("utf-8"))))
            except:
                xml = etree.XML(PartnerService.prepare_xml(str(self.request.body)))

            # Getting configs
            configs = PartnerService.get_authentication_configs(self.settings)

            # Parse XML to Json
            json = PartnerService.get_notification_body(xml)

            # Processing request
            try:
                PartnerService.notify.delay(configs=configs, headers={"Content-Type": "application/json"}, body=json, type=self.NOTIFICATION_TYPE)
                xml_response = PartnerService.get_notification_response(configs['description_text'], json, "true", 0)
                return self.success(xml_response)
            except Exception as e:
                log.error("Internal Server Error: {0}."
                          "Operation Hash: {1}."
                          .format(e, self.NOTIFICATION_HASH))
                xml_response = PartnerService.get_notification_error_response(configs['description_error_text'], "false", 500)
                return self.error(xml_response, 500)

        except Exception as e:
            log.error("Internal Server Error: {0}."
                      "Operation Hash: {1}."
                      .format(e, self.NOTIFICATION_HASH))
            xml_response = PartnerService.get_notification_error_response(configs['description_error_text'], "false", 500)
            return self.error(xml_response, 500)


class MoHandler(APIHandler):
    __urls__ = [r"/{0}/{1}/mo".format(partner_name, api_version),
                r"/{0}/{1}/mo/".format(partner_name, api_version)]

    # MO Hash Code for log identification
    MO_HASH = LOG_HASH["mo"]

    @request
    @validate_mo
    def post(self):
        try:
            # Getting body
            try:
                xml = etree.XML(PartnerService.prepare_xml(str(self.request.body.decode("utf-8"))))
            except:
                xml = etree.XML(PartnerService.prepare_xml(str(self.request.body)))

            # Getting configs
            configs = PartnerService.get_mo_configs(self.settings)

            # Parse XML to Json
            json = PartnerService.get_mo_body(xml)

            # Processing request asynchronously
            try:
                PartnerService.send_mo.delay(configs=configs, headers={"Content-Type": "application/json"}, body=json)
            except Exception as e:
                log.error("Internal Server Error: {0}."
                          "Operation Hash: {1}."
                          .format(e, self.MO_HASH))
                response_xml = PartnerService.get_mo_fail_response(configs['fail_description_text'], '', 500)
                return self.error(response_xml, 500)

            # Sending response
            response_xml = PartnerService.get_mo_response(configs, json)
            return self.success(response_xml)

        except Exception as e:
            response_xml = PartnerService.get_mo_fail_response(configs['fail_description_text'], '', 500)
            log.error("Internal Server Error: {0}."
                      "Operation Hash: {1}."
                      .format(e, self.MO_HASH))
            return self.error(response_xml, 500)
