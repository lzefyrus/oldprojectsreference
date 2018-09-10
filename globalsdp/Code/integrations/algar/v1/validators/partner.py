from functools import wraps
import logging
from lxml import etree
from integrations.algar.v1.services import partner as PartnerService
import application.settings as settings

# Logging handler
log = logging.getLogger(__name__)
partner_name = 'algar'

# Status
SIGNATURE_SUCCEEDED = 12
SIGNATURE_FAILED = 7
AUTHENTICATION_SUCCEEDED = 10
AUTHENTICATION_FAILED = 11
LOG_HASH = settings.LOG_HASHES[partner_name]

def validate_notification(type):
    """
    Decorator which validates notification request.
    :param type: notification type
    """
    def wrap(func):
        @wraps(func)
        def wrapped_f(self, *args):

            # Notification Hash Code for log identification
            NOTIFICATION_HASH = LOG_HASH["{0}_notification".format(type)]

            # Validating body
            try:
                xml = etree.XML(PartnerService.prepare_xml(str(self.request.body.decode("utf-8"))))
            except Exception as e:
                try:
                    xml = etree.XML(PartnerService.prepare_xml(str(self.request.body)))
                except:
                    log.error("Invalid XML object: {0}"
                              "Operation Hash: {1}."
                              .format(e, NOTIFICATION_HASH))
                    xml_response = PartnerService.get_notification_error_response("Invalid XML object: {0}".format(e), "false", 400)
                    return self.error(xml_response)

            # Validating status
            try:
                status = int(xml.get("status"))
            except:
                message = "Missing status attribute on notification_request tag" \
                          "Operation Hash: {0}."\
                          .format(NOTIFICATION_HASH)
                log.error(message)
                xml_response = PartnerService.get_notification_error_response(message, "false", 400)
                return self.error(xml_response)

            # if status not in (SIGNATURE_SUCCEEDED, SIGNATURE_FAILED, AUTHENTICATION_SUCCEEDED, AUTHENTICATION_FAILED):
            #     message = "Unknown status for notification: status={0}." \
            #               "Operation Hash: {1}."\
            #               .format(status, NOTIFICATION_HASH)
            #     log.error(message)
            #     xml_response = PartnerService.get_notification_error_response(message, "false", 400)
            #     return self.error(xml_response)

            # Validating application_id
            if not xml.get("application_id"):
                message = "Missing application_id attribute on notification_request tag." \
                          "Operation Hash: {0}."\
                          .format(NOTIFICATION_HASH)
                log.error(message)
                xml_response = PartnerService.get_notification_error_response(message, "false", 400)
                return self.error(xml_response)

            # Validating parameters
            error_list = []
            try:
                if not xml.find('dispatcher_id').text:
                    raise Exception
            except:
                error_list.append('dispatcher_id')

            try:
                if not xml.find('message_id').text:
                    raise Exception
            except:
                error_list.append('message_id')

            try:
                if not xml.find('smsc_message_id').text:
                    raise Exception
            except:
                error_list.append('smsc_message_id')

            try:
                if not xml.find('source').text:
                    raise Exception
            except:
                error_list.append('source')

            try:
                if not xml.find('destination').text:
                    raise Exception
            except:
                error_list.append('destination')

            try:
                if not xml.find('request_datetime').text:
                    raise Exception
            except:
                error_list.append('request_datetime')

            try:
                if not xml.find('notification_datetime').text:
                    raise Exception
            except:
                error_list.append('notification_datetime')

            try:
                if not xml.find('app_specific_id').text:
                    raise Exception
            except:
                error_list.append('app_specific_id')

            try:
                if not xml.find('description').text:
                    raise Exception
            except:
                error_list.append('description')

            if error_list:
                message = "Missing mandatory parameters: {0}" \
                          "Operation Hash: {1}."\
                          .format(error_list, NOTIFICATION_HASH)
                log.error(message)
                xml_response = PartnerService.get_notification_error_response(message, "false", 400)
                return self.error(xml_response)

            # Validating configs
            try:
                host = self.application.settings['config']['algar/v1/backend/host']['value']
                url_signature = self.application.settings['config']['algar/v1/backend/url/notification/signature']['value']
                url_authentication = self.application.settings['config']['algar/v1/backend/url/notification/authentication']['value']
                url_cancellation = self.application.settings['config']['algar/v1/backend/url/notification/cancellation']['value']
                description_text = self.application.settings['config']['algar/v1/backend/notification/message']['value']
                description_error_text = self.application.settings['config']['algar/v1/backend/notification/error/message']['value']

            except:
                log.error("Could not find configs (host or url) for notification."
                          "Operation Hash: {0}."
                          .format(NOTIFICATION_HASH))
                xml_response = PartnerService.get_notification_error_response("Could not proceed with your request. Internal Error.", "false", 500)
                return self.error(xml_response)

            return func(self, *args)
        return wrapped_f
    return wrap


def validate_mo(func):
    """
    Validates algar MO request (mandatory params only)
    """
    @wraps(func)
    def with_mo(self):
        # MO Hash Code for log identification
        MO_HASH = LOG_HASH["mo"]

        # Validating body
        try:
            xml = etree.XML(PartnerService.prepare_xml(str(self.request.body.decode("utf-8"))))
        except Exception as e:
            try:
                xml = etree.XML(PartnerService.prepare_xml(str(self.request.body)))
            except:
                log.error("Invalid XML object: {0}"
                          "Operation Hash: {1}."
                          .format(e, MO_HASH))
                xml_response = PartnerService.get_mo_fail_response("Invalid XML object: {0}".format(e), "false", 400)
                return self.error(xml_response)

        # Validating parameters
        error_list = []
        try:
            if not xml.find('carrier_id').text:
                raise Exception
        except:
            error_list.append('carrier_id')
        try:
            if not xml.find('dispatcher_id').text:
                raise Exception
        except:
            error_list.append('dispatcher_id')
        try:
            if not xml.find('application_id').text:
                raise Exception
        except:
            error_list.append('application_id')
        try:
            if not xml.find('large_account').text:
                raise Exception
        except:
            error_list.append('large_account')
        try:
            if not xml.find('source').text:
                raise Exception
        except:
            error_list.append('source')
        try:
            if not xml.find('request_datetime').text:
                raise Exception
        except:
            error_list.append('request_datetime')
        try:
            if not xml.find('text').text:
                raise Exception
        except:
            error_list.append('text')

        if error_list:
            message = "Missing mandatory parameters: {0}."\
                      "Operation Hash: {1}."\
                      .format(error_list, MO_HASH)
            log.error(message)
            xml_response = PartnerService.get_mo_fail_response(message, "false", 400)
            return self.error(xml_response)

        # Validating backend access configs:
        try:
            configs = {
                'host': self.application.settings['config']['algar/v1/backend/host'],
                'url': self.application.settings['config']['algar/v1/backend/mo/url'],
                'ack': self.application.settings['config']['algar/v1/mo/ack'],
                'is_billing': self.application.settings['config']['algar/v1/mo/is_billing'],
                'keep_session': self.application.settings['config']['algar/v1/mo/keep_session'],
                'description_code': self.application.settings['config']['algar/v1/mo/description/code'],
                'description_text': self.application.settings['config']['algar/v1/mo/description/text'],
                'fail_description_text': self.application.settings['config']['algar/v1/mo/fail/description/text'],
            }
        except KeyError:
            message = "Could not find access configs for algar" \
                      "Operation Hash: {0}."\
                      .format(MO_HASH)
            log.error(message)
            xml_response = PartnerService.get_mo_fail_response(message, "false", 500)
            return self.error(xml_response, 500)

        return func(self)
    return with_mo
