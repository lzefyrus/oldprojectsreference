from functools import wraps
import logging
from lxml import etree
from integrations.claro.v1.services import backend as BackendService
from integrations.claro.v1.services import partner as PartnerService


# Logging handler
log = logging.getLogger(__name__)


def validate_mt_notification(func):
    """
    Validates notification request.
    """
    @wraps(func)
    def with_register(self):
        # Validating body
        try:
            xml = etree.XML(self.request.body.decode('utf-8'))
        except Exception as e:
            log.error("Invalid XML object: {0}".format(e))
            return self.error({"success": "0", "message": "Invalid XML object"})

        # Validating status
        try:
            json = BackendService.parse_response_to_json(xml, 'sync')
        except Exception as e:
            log.error("Could not parse XML: {0}. Error: {1}".format(xml, e))
            return self.error({"success": "0", "message": "Could not parse XML"})

        # Validating configs
        try:
            host = self.application.settings['config']['claro/v1/backend/host']
            url = self.application.settings['config']['claro/v1/backend/notification/mt/url']
            user = self.application.settings['config']['claro/v1/user']
            password = self.application.settings['config']['claro/v1/password']
        except:
            log.error("Could not find configs for MT notification")
            return self.error({"success": "0", "message": "Could not proceed with your request. Internal Error."}, 500)

        return func(self)
    return with_register


def validate_mms_mt_notification(func):
    """
    Validates MMS notification request.
    """
    @wraps(func)
    def with_register(self):
        # Validating body
        try:
            xml = etree.XML(self.request.body.decode('utf-8'))
        except Exception as e:
            log.error("Invalid XML object: {0}".format(e))
            return self.error({"success": "0", "message": "Invalid XML object"})

        # Validating status
        try:
            json = BackendService.parse_response_to_json(xml, 'sync')
        except Exception as e:
            log.error("Could not parse XML: {0}. Error: {1}".format(xml, e))
            return self.error({"success": "0", "message": "Could not parse XML"})

        # Validating configs
        try:
            host = self.application.settings['config']['claro/v1/backend/host']
            url = self.application.settings['config']['claro/v1/backend/notification/mms/url']
            user = self.application.settings['config']['claro/v1/user']
            password = self.application.settings['config']['claro/v1/password']
        except:
            log.error("Could not find configs for MMS MT notification")
            return self.error({"success": "0", "message": "Could not proceed with your request. Internal Error."}, 500)

        return func(self)
    return with_register


def validate_wap_mt_notification(func):
    """
    Validates WAP MT notification request.
    """
    @wraps(func)
    def with_register(self):
        # Validating body
        try:
            xml = etree.XML(self.request.body.decode('utf-8'))
        except Exception as e:
            log.error("Invalid XML object: {0}".format(e))
            return self.error({"success": "0", "message": "Invalid XML object"})

        # Validating status
        try:
            json = BackendService.parse_response_to_json(xml, 'sync')
        except Exception as e:
            log.error("Could not parse XML: {0}. Error: {1}".format(xml, e))
            return self.error({"success": "0", "message": "Could not parse XML"})

        # Validating configs
        try:
            host = self.application.settings['config']['claro/v1/backend/host']
            url = self.application.settings['config']['claro/v1/backend/notification/mms/url']
            user = self.application.settings['config']['claro/v1/user']
            password = self.application.settings['config']['claro/v1/password']
        except:
            log.error("Could not find configs for WAP notification")
            return self.error({"success": "0", "message": "Could not proceed with your request. Internal Error."}, 500)

        return func(self)
    return with_register


def validate_wib_push_notification(func):
    """
    Validates WIB PUSH notification request.
    """
    @wraps(func)
    def with_register(self):
        # Validating body
        try:
            xml = etree.XML(self.request.body.decode('utf-8'))
        except Exception as e:
            log.error("Invalid XML object: {0}".format(e))
            return self.error({"success": "0", "message": "Invalid XML object"})

        # Validating status
        try:
            json = BackendService.parse_response_to_json(xml, 'sync')
        except Exception as e:
            log.error("Could not parse XML: {0}. Error: {1}".format(xml, e))
            return self.error({"success": "0", "message": "Could not parse XML"})

        # Validating configs
        try:
            host = self.application.settings['config']['claro/v1/backend/host']
            url = self.application.settings['config']['claro/v1/backend/notification/wib-push/url']
            user = self.application.settings['config']['claro/v1/user']
            password = self.application.settings['config']['claro/v1/password']
        except:
            log.error("Could not find configs for WIB Push notification")
            return self.error({"success": "0", "message": "Could not proceed with your request. Internal Error."}, 500)

        return func(self)
    return with_register


def validate_mo(func):
    """
    Validates MO request.
    """
    @wraps(func)
    def with_register(self):
        # Validating query string arguments
        error_list = []

        text = self.get_argument('TEXT', None)
        if not text:
            error_list.append('TEXT')

        id = self.get_argument('ID', None)
        if not id:
            error_list.append('ID')

        msisdn = self.get_argument('ANUM', None)
        if not msisdn:
            error_list.append('ANUM')

        la = self.get_argument('BNUM', None)
        if not la:
            error_list.append('BNUM')

        if error_list:
            message = "Invalid Query String. Missing arguments: {0}".format(error_list)
            log.error(message)
            return self.error({"success": "0", "message": message})

        # Validating configs
        try:
            host = self.application.settings['config']['claro/v1/backend/host']
            url = self.application.settings['config']['claro/v1/backend/mo/url']
            user = self.application.settings['config']['claro/v1/user']
            password = self.application.settings['config']['claro/v1/password']
        except:
            log.error("Could not find configs for MO")
            return self.error({"success": "0", "message": "Could not proceed with your request. Internal Error."}, 500)

        return func(self)
    return with_register


def validate_mms_mo(func):
    """
    Validates MMS MO notification request.
    """
    @wraps(func)
    def with_register(self):
        # Validating body
        try:
            xml = etree.XML(self.request.body.decode('utf-8'))
        except Exception as e:
            log.error("Invalid XML object: {0}".format(e))
            return self.error({"success": "0", "message": "Invalid XML object"})

        # Validating status
        try:
            json = PartnerService.get_mms_mo_body(xml)
        except Exception as e:
            log.error("Could not parse XML: {0}. Error: {1}".format(xml, e))
            return self.error({"success": "0", "message": "Could not parse XML"})

        # Validating configs
        try:
            host = self.application.settings['config']['claro/v1/backend/host']
            url = self.application.settings['config']['claro/v1/backend/mo/mms/url']
            user = self.application.settings['config']['claro/v1/user']
            password = self.application.settings['config']['claro/v1/password']
        except:
            log.error("Could not find configs for MMS MO")
            return self.error({"success": "0", "message": "Could not proceed with your request. Internal Error."}, 500)

        return func(self)
    return with_register
