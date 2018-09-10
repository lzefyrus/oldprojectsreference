import logging

from application.src.rewrites import SoapHandler
from application.src.rewrites import wsdl
from application.src.request import request
from application.src.auth import basic_auth
from integrations.tim.v1.utils.etl import etl



# Log
log = logging.getLogger(__name__)

# Settings
partner_name = 'tim'
api_version = 'v1'


def check_credentials(handler, user, password):
    return user == handler.application.settings['config']['tim/v1/recharge/auth/user']['value'] \
           and password == handler.application.settings['config']['tim/v1/recharge/auth/password']['value']


@basic_auth(check_credentials)
class RechargeHandler(SoapHandler):
    __urls__ = [r"/{0}/{1}/recharge".format(partner_name, api_version),
                r"/{0}/{1}/recharge/".format(partner_name, api_version)]

    @request
    @etl
    @wsdl(
        _args=['event-id', 'msisdn', 'partner-id', 'value', 'date', 'time', 'tariff-id', 'subsys'],
        _params=[int, int, int, float, str, str, int, str],  # TODO: criar tuplas com o parametro de cima
        _returns=int,
        _name='enviaNotificacaoRecarga')
    def recharge(self, *args):
        try:
            log.info("Recharge notification received: {0}|{1}|{2}|{3}|{4}|{5}|{6}|{7}".format(
                args[0], args[1], args[2], args[3], args[4], args[5], args[6], args[7],
            ))
        except Exception as e:
            log.error(e)
            self.set_status(400)
        finally:
            return self.get_status()
