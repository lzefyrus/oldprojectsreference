"""
Backend services
"""

from tornado.httpclient import HTTPRequest
from urllib.parse import quote_plus
from application.src.exceptions import LaNotFoundException
import re


##### MT ###############
########################
class MtService(object):

    @staticmethod
    def get_configs(settings, la):
        """
        Gets cached configs for MT on application.settings['config'] object

        :param settings: Cache object application.settings['config']
        :param la:: Large Account number
        :return: json
        """

        configs = {
            'host': settings['config']['oi/v1/host']['value'],
            'url': settings['config']['oi/v1/mt/url']['value'],
            'charset': settings['config']['oi/v1/mt/charset/default']['value'],
            'smsc': settings['config']['oi/v1/mt/smsc']['value'],
        }
        try:
            la_user = settings['config']['oi/v1/mt/{0}/user'.format(la)]['value']
            la_password = settings['config']['oi/v1/mt/{0}/password'.format(la)]['value']
        except KeyError:
            try:
                la_user = settings['config']['oi/v1/mt/default-la/user'.format(la)]['value']
                la_password = settings['config']['oi/v1/mt/default-la/password'.format(la)]['value']
            except KeyError:
                raise LaNotFoundException("Default MT user/pass not found on Oi configs".format(la))

        configs['la_user'] = la_user
        configs['la_password'] = la_password

        return configs

    @staticmethod
    def get_url(configs, la, msisdn, text, charset, udh, dlrmask, dlrurl, validity, mclass):
        """
        Gets request URL

        :param configs: Cache object application.settings['config']
        :param la: Large Account number
        :param msisdn: Telephone number
        :param msisdn: Message text
        :param charset: Message charset (default UTF-8)
        :param udh: User Data Header (for binary messages only)
        :param dlrmask: Delivery report requesting
        :param dlrurl: In case of dlrmask requesting, this is the delivery report URL (encoded)
        :param validity: Message validity in minutes
        :param mclass: Defines if message is sent to the message inbox (0 - default) or device screen (1)
        :return: String
        """

        url = "{0}/{1}?".format(configs['host'], configs['url'])
        parameters = "username={0}&password={1}&from={2}&to={3}&text={4}&smsc={5}"\
            .format(configs['la_user'], configs['la_password'], la, msisdn, quote_plus(text), configs['smsc'])

        # optional parameters
        parameters += "&charset={0}".format(charset or configs['charset'])
        parameters += "&udh={0}".format(udh) if udh else ""
        parameters += "&dlrmask={0}".format(dlrmask) if dlrmask else ""
        parameters += "&dlrurl={0}".format(dlrurl) if dlrurl else ""
        parameters += "&validity={0}".format(validity) if validity else ""
        parameters += "&mclass={0}".format(mclass) if mclass else ""

        return url+parameters


##### BILLING ##########
########################
class BillingService(object):
    def get_configs(self, settings, service_id):
        """
        Gets cached configs for billing on application.settings['config'] object

        :param settings: Cache object application.settings['config']
        :param service_id:: Service Id number
        :return: json
        """
        return {
            'wsdl_billing': settings['config']['oi/v1/billing/wsdl']['value'],
            'provider_code': settings['config']['oi/v1/billing/{0}/user'.format(service_id)]['value'],
            'password': settings['config']['oi/v1/billing/{0}/password'.format(service_id)]['value'],
        }

    def prepare_xml(self, xml):
        """
        Prepares Oi's xml response by removing some unused tags and spaces

        :param xml: XML object
        :param service_id:: Service Id number
        :return: json
        """

        prepared = re.sub('ver[0-9]:', '', xml)
        prepared = re.sub('ns[0-9]:', '', prepared)
        prepared = prepared.replace("efet:", "")\
                           .replace("soapenv:", "")\
                           .replace("\n", "")\
                           .replace("""<?xml version="1.0" encoding="UTF-8"?>""", "")
        return prepared

    def parse_response_to_json(self, xml_response):
        """
        Parses Oi's xml response to json

        :param xml_response: xml response body from Oi
        :return: json
        """

        xml_response = xml_response.find("Body")
        xml_response = xml_response.find("EfetuarDebitoSemReservaSaldoOCSResponse")

        status_code = None
        try:
            status_code = xml_response.find("codigoStatus").text
        except:
            pass

        session_id = None
        try:
            session_id = xml_response.find("identificadorSessao").text
        except:
            pass

        last_status = None
        try:
            last_status = xml_response.find("ultimoStatus").text
        except:
            pass

        pre_pos_code = None
        try:
            pre_pos_code = xml_response.find("codigoPrePos").text
        except:
            pass

        amount = None
        try:
            amount = xml_response.find("saldo").text
        except:
            pass

        transaction_id = None
        try:
            transaction_id = xml_response.find("identificadorTransacao").text
        except:
            pass

        return {
            "codigoStatus": status_code,
            "identificadorSessao": session_id,
            "ultimoStatus": last_status,
            "codigoPrePos": pre_pos_code,
            "saldo": amount,
            "identificadorTransacao": transaction_id,
        }

    def parse_error_response_to_json(self, xml_response):
        """
        Parses Oi's xml error response to json. It contains the 'Fault' tag.

        :param xml_response: xml response body from Nextel
        :return: Json
        """

        xml_response = xml_response.find("Body")
        xml_response = xml_response.find("Fault")
        return {
            "code": xml_response.find("faultcode").text,
            "reason": xml_response.find("faultstring").text,
        }

    def get_request_body(self, provider_code, password, msisdn, service_id, session_id):
        """
        Gets billing xml.

        **SOAP get method was not available, for that reason, the xml is manually written here.

        :param provider_code: Provider code number
        :param password: Operation password
        :param msisdn: Telephone number
        :param service_id: Service id number
        :param session_id: Session id number
        :return: String (xml)
        """

        xml = "<soapenv:Envelope xmlns:soapenv='http://schemas.xmlsoap.org/soap/envelope/' xmlns:efet='http://alsb.telemar/xsd/EfetuarDebitoSemReservaSaldoOCSRequest'>" \
                "<soapenv:Header/>" \
                "<soapenv:Body>" \
                  "<efet:EfetuarDebitoSemReservaSaldoOCSRequest>" \
                     "<efet:usuarioParceiro>{0}</efet:usuarioParceiro>" \
                     "<efet:senhaParceiro>{1}</efet:senhaParceiro>" \
                     "<efet:msisdn>{2}</efet:msisdn>" \
                     "<efet:codigoServico>{3}</efet:codigoServico>" \
                     "<efet:identificadorSessao>{4}</efet:identificadorSessao>" \
                  "</efet:EfetuarDebitoSemReservaSaldoOCSRequest>" \
                "</soapenv:Body>" \
            "</soapenv:Envelope>"\
            .format(provider_code, password, msisdn, service_id, session_id)

        return xml

    def save(self, settings, body, success):
        """
        Persists billing request informations somewhere.
        Ex: files, streamings (Keneasis) etc, generally used by B.I Team

        :param settings: application settings (configs)
        :param body: billing request body
        :param success: success status for billing request
        :return: None
        """
        pass


##### CHECK CREDIT #####
########################
class CheckCreditService(object):
    def get_configs(self, settings, service_id):
        """
        Gets cached configs for check credit on application.settings['config'] object

        :param settings: Cache object application.settings['config']
        :param service_id:: Service Id number
        :return: json
        """
        return {
            'wsdl_checkcredit': settings['config']['oi/v1/checkcredit/wsdl']['value'],
            'provider_code': settings['config']['oi/v1/billing/{0}/user'.format(service_id)]['value'],
            'password': settings['config']['oi/v1/billing/{0}/password'.format(service_id)]['value'],
        }

    def prepare_xml(self, xml):
        """
        Prepares Oi's xml response by removing some unused tags and spaces

        :param xml: XML object
        :return: json
        """
        prepared = re.sub('ver[0-9]:', '', xml)
        prepared = re.sub('ns[0-9]:', '', prepared)
        prepared = prepared.replace("soapenv:", "")\
                           .replace("ver:", "")\
                           .replace("esb:", "")\
                           .replace("\n", "")\
                           .replace("""<?xml version="1.0" encoding="UTF-8"?>""", "")
        return prepared

    def parse_response_to_json(self, xml_response):
        """
        Parses Oi's xml response to json

        :param xml_response: xml response body from Oi
        :return: json
        """

        xml_response = xml_response.find("Body")
        xml_check_response = xml_response.find("VerificarDisponibilidadeSaldoClienteResponse")
        xml_response = xml_check_response if xml_check_response else xml_response.find("EfetuarDebitoSemReservaSaldoOCSResponse")

        status_code = None
        try:
            status_code = xml_response.find("codigoStatus").text
        except:
            pass

        session_id = None
        try:
            session_id = xml_response.find("identificadorSessao").text
        except:
            pass

        pre_pos_code = None
        try:
            pre_pos_code = xml_response.find("codigoPrePos").text
        except:
            pass

        amount = None
        try:
            amount = xml_response.find("saldo").text
        except:
            pass

        return {
            "codigoStatus": status_code,
            "codigoPrePos":pre_pos_code,
            "saldo": amount,
            "identificadorSessao": session_id,
        }

    def parse_error_response_to_json(self, xml_response):
        """
        Parses Oi's xml error response to json. It contains the 'Fault' tag.

        :param xml_response: xml response body from Nextel
        :return: Json
        """

        xml_response = xml_response.find("Body")
        xml_response = xml_response.find("Fault")

        return {
            "code": xml_response.find("faultcode").text,
            "reason": xml_response.find("faultstring").text,
        }

    def get_request_body(self, provider_code, password, msisdn, service_id, session_id):
        """
        Gets billing xml.

        **SOAP get method was not available, for that reason, the xml is manually written here.

        :param provider_code: Provider code number
        :param password: Operation password
        :param msisdn: Telephone number
        :param service_id: Service id number
        :param session_id: Session id number
        :return: String (xml)
        """

        xml = "<soapenv:Envelope xmlns:soapenv='http://schemas.xmlsoap.org/soap/envelope/' xmlns:ver='http://alsb.telemar/xsd/VerificarDisponibilidadeSaldoClienteRequest'> " \
                "<soapenv:Header/>" \
                "<soapenv:Body>" \
                    "<ver:VerificarDisponibilidadeSaldoClienteRequest>" \
                        "<ver:usuarioParceiro>{0}</ver:usuarioParceiro>" \
                        "<ver:senhaParceiro>{1}</ver:senhaParceiro>" \
                        "<ver:msisdn>{2}</ver:msisdn>" \
                        "<ver:codigoServico>{3}</ver:codigoServico>" \
                        "<ver:identificadorSessao>{4}</ver:identificadorSessao>" \
                    "</ver:VerificarDisponibilidadeSaldoClienteRequest>" \
                "</soapenv:Body>" \
            "</soapenv:Envelope>"\
            .format(provider_code, password, msisdn, service_id, session_id)

        return xml

