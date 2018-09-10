from application.src.rewrites import SoapHandler
from application.src.rewrites import wsdl
from application.src.request import request
import logging


# Log
log = logging.getLogger(__name__)

# Settings
partner_name = 'tim'
api_version = 'v1'


class TestSoapHandler(SoapHandler):
    __urls__ = [r"/{0}/{1}/test".format(partner_name, api_version),
                r"/{0}/{1}/test/".format(partner_name, api_version)]

    @request
    @wsdl(
        _args=['event-id', 'msisdn', 'partner-id', 'value', 'date', 'time', 'tariff-id', 'subsys'],
        _params=[int, int, int, float, str, str, int, str],
        _returns=int,
        _name='testando')
    def test(self, *args):
        try:
            log.info("Test notification received: {0}|{1}|{2}|{3}|{4}|{5}|{6}|{7}".format(
                args[0], args[1], args[2], args[3], args[4], args[5], args[6], args[7],
            ))
        except:
            self.set_status(400)
        finally:
            return self.get_status()
