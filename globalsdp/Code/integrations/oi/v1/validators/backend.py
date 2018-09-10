from functools import wraps
from tornado.escape import json_decode
from application.src.exceptions import ProviderCodeNotFoundException
import logging

# Logging handler
log = logging.getLogger(__name__)


def validate_mt(func):
    """
    Validates Oi MT request (mandatory params only)
    """
    @wraps(func)
    def with_mt(self):

        error_list = []
        la = self.get_argument('la', None, strip=True)
        if not la:
            error_list.append('la')

        msisdn = self.get_argument('msisdn', None, strip=True)
        if not msisdn:
            error_list.append('msisdn')

        text = self.get_argument('text', None, strip=True)
        if not text:
            error_list.append('text')

        dlrmask = self.get_argument('dlrmask', None, strip=True)
        dlrurl = self.get_argument('dlrurl', None, strip=True)
        if dlrmask and not dlrurl:
                message = "Parameter dlrurl is mandatory when dlrmask is set"
                log.error(message)
                return self.error({"status": 0, "message": message})
        if dlrurl and not dlrmask:
                message = "Parameter dlrurl is only valid when dlrmask is set"
                log.error(message)
                return self.error({"status": 0, "message": message})

        if error_list:
            log.error("Missing mandatory parameters inside body: {0}".format(error_list).replace('\n',' '))
            return self.error({"status": 0, "message": "Missing mandatory parameters on URL: {0}"
                              .format(error_list)})

        # Validating Oi access configs:
        try:
            configs = {
                'host': self.application.settings['config']['oi/v1/host']['value'],
                'url': self.application.settings['config']['oi/v1/mt/url']['value'],
                'charset': self.application.settings['config']['oi/v1/mt/charset/default']['value'],
                'smsc': self.application.settings['config']['oi/v1/mt/smsc']['value'],
            }
        except KeyError:
            log.error("Could not find access configs for Oi.")
            return self.error({"message": "Could not find access configs for Oi."})

        return func(self)
    return with_mt


def validate_billing(func):
    """
    Validates Oi Billing/Check Credit request (mandatory params only)
    """
    @wraps(func)
    def with_billing(self):
        # Validating body
        try:
            body = json_decode(self.request.body)
        except Exception as e:
            log.error("Invalid JSON object: {0}".format(e))
            return self.error({"message": "Invalid JSON object"})

        error_list = []
        try:
            msisdn = body['msisdn']
        except KeyError:
            error_list.append('msisdn')
        try:
            service_id = body['service_id']
        except KeyError:
            error_list.append('service_id')
        try:
            session_id = body['session_id']
        except KeyError:
            error_list.append('session_id')

        if error_list:
            log.error("Missing mandatory parameters inside body: {0}".format(error_list).replace('\n',' '))
            return self.error({"success": 0, "message": "Missing mandatory parameters inside body: {0}"
                              .format(error_list)})

        # Validating Oi access configs:
        try:
            configs = {
                'wsdl_billing': self.settings['config']['oi/v1/billing/wsdl']['value'],
                'wsdl_checkcredit': self.settings['config']['oi/v1/checkcredit/wsdl']['value'],
            }

            try:
                provider_code = self.settings['config']['oi/v1/billing/{0}/user'.format(service_id)]['value']
                password = self.settings['config']['oi/v1/billing/{0}/password'.format(service_id)]['value']
            except KeyError:
                raise ProviderCodeNotFoundException("ProviderCode user/pass not found for service_id {0} on Oi configs"
                                                    .format(service_id))

        except ProviderCodeNotFoundException as pcnfe:
            log.error(pcnfe.__str__())
            return self.error({"message": pcnfe.__str__()}, 500)
        except KeyError:
            log.error("Could not find configs for Oi: {0} or {1}".format('oi/v1/billing/wsdl', 'oi/v1/checkcredit/wsdl'))
            return self.error({"message": "Could not find access configs for Oi"}, 500)

        return func(self)
    return with_billing

