"""
Backend services
"""

import logging
from tornado.httpclient import HTTPRequest
from urllib.parse import quote_plus
from lxml import etree


# Logging handler
log = logging.getLogger(__name__)


##### MT #####
##############
class MtService(object):

    def get_configs(self, settings):
        return {
            'host': settings['config']['claro/v1/host']['value'],
            'url': settings['config']['claro/v1/mt/url']['value'],
            'user': settings['config']['claro/v1/backend/user']['value'],
            'password': settings['config']['claro/v1/backend/password']['value'],
        }

    def get_url(self, configs, message, msisdn, mode, source, expiration):
        url = "{0}/{1}?".format(configs['host'], configs['url'])
        parameters = "profile={0}&pwd={1}&mode={2}&BNUM={3}&TEXT={4}"\
            .format(configs['user'], configs['password'], mode, msisdn,  quote_plus(message))

        if source:
            parameters += "&ANUM={0}".format(source)

        if expiration:
            parameters += "&VALPERIOD={0}".format(parse_expiration(expiration))

        return url+parameters

    def get_request(self, request_url):
        return HTTPRequest(
            url=request_url,
            method="GET",
            request_timeout=10)


##### MMS MT #####
##################
class MmsMtService(object):

    def get_configs(self, settings):
        return {
            'host': settings['config']['claro/v1/host']['value'],
            'url': settings['config']['claro/v1/mmsmt/url']['value'],
            'user': settings['config']['claro/v1/backend/user']['value'],
            'password': settings['config']['claro/v1/backend/password']['value'],
        }

    def get_url(self, configs, message, msisdn, mode):
        url = "{0}/{1}?".format(configs['host'], configs['url'])
        parameters = "profile={0}&pwd={1}&mode={2}&CTN={3}&MMS={4}"\
            .format(configs['user'], configs['password'], mode, msisdn, quote_plus(message))

        return url+parameters

    def get_request(self, request_url):
        return HTTPRequest(
            url=request_url,
            method="POST",
            request_timeout=10,
            allow_nonstandard_methods=True)


##### WAP MT #####
##################
class WapMtService(object):

    def get_configs(self, settings):
        return {
            'host': settings['config']['claro/v1/host']['value'],
            'url': settings['config']['claro/v1/wapmt/url']['value'],
            'user': settings['config']['claro/v1/backend/user']['value'],
            'password': settings['config']['claro/v1/backend/password']['value'],
        }

    def get_url(self, configs, message, msisdn, url, mode, expiration):
        wap_url = "{0}/{1}?".format(configs['host'], configs['url'])
        parameters = "profile={0}&pwd={1}&mode={2}&BNUM={3}&TEXT={4}&URL={5}"\
            .format(configs['user'], configs['password'], mode, msisdn,  quote_plus(message),  quote_plus(url))

        if expiration:
            parameters += "&VALPERIOD={0}".format(parse_expiration(expiration))

        return wap_url+parameters

    def get_request(self, request_url):
        return HTTPRequest(
            url=request_url,
            method="GET",
            request_timeout=10)


##### CHECK CREDIT #####
########################
class CheckCreditService(object):

    def get_configs(self, settings):
        return {
            'host': settings['config']['claro/v1/host']['value'],
            'url': settings['config']['claro/v1/checkcredit/url']['value'],
            'user': settings['config']['claro/v1/backend/user']['value'],
            'password': settings['config']['claro/v1/backend/password']['value'],
        }


    def get_url(self, configs, amount, msisdn, mode='sync'):
        url = "{0}/{1}?".format(configs['host'], configs['url'])
        parameters = "profile={0}&pwd={1}&mode={2}&CTN={3}&AMOUNT={4}"\
            .format(configs['user'], configs['password'], mode, msisdn, amount)

        return url+parameters


    def get_request(self, request_url):
        return HTTPRequest(
            url=request_url,
            method="GET",
            request_timeout=10)


##### BILLING #####
###################
class BillingService(object):

    def get_configs(self, settings):
        return {
            'host': settings['config']['claro/v1/host']['value'],
            'url': settings['config']['claro/v1/billing/url']['value'],
            'user': settings['config']['claro/v1/backend/user']['value'],
            'password': settings['config']['claro/v1/backend/password']['value'],
        }

    def get_url(self, configs, billing_code, msisdn, mode='sync'):
        url = "{0}/{1}?".format(configs['host'], configs['url'])
        parameters = "profile={0}&pwd={1}&mode={2}&billingCode={3}&CTN={4}"\
            .format(configs['user'], configs['password'], mode, billing_code, msisdn)

        return url+parameters

    def get_request(self, request_url):
        return HTTPRequest(
            url=request_url,
            method="GET",
            request_timeout=10)



##### WIB PUSH #####
####################
class WibPushService(object):

    def get_configs(self, settings):
        return {
            'host': settings['config']['claro/v1/host']['value'],
            'url': settings['config']['claro/v1/wibpush/url']['value'],
            'user': settings['config']['claro/v1/backend/user']['value'],
            'password': settings['config']['claro/v1/backend/password']['value'],
        }

    def get_url(self, configs, wml_push_code, msisdn, mode):
        url = "{0}/{1}?".format(configs['host'], configs['url'])
        parameters = "profile={0}&pwd={1}&mode={2}&MSISDN={3}&WML={4}"\
            .format(configs['user'], configs['password'], mode, msisdn,  quote_plus(wml_push_code.encode('ISO-8859-1')))

        return url+parameters

    def get_request(self, request_url):
        return HTTPRequest(
            url=request_url,
            method="GET",
            request_timeout=10)

    def get_xml(self, wml_push_code):
        body = etree.Element('wml')
        body.text = wml_push_code
        return etree.tostring(body, xml_declaration=True, encoding="ISO-8859-1", pretty_print=True).decode('ISO-8859-1')


#######GENERAL########
######################
def parse_expiration(expiration):
    return expiration


def parse_response_to_json(xml_response, mode="sync"):
    try:
        status = xml_response.find("status-code").text
    except:
        status = None
    try:
        profile = xml_response.find("profile").text
    except:
        profile = None
    try:
        transaction_id = xml_response.find("transaction-id").text
    except:
        transaction_id = None
    try:
        error_message = xml_response.find("error-message").text
    except:
        error_message = None

    json_response = {
        "status": status,
        "profile": profile,
        "transaction_id": transaction_id,
        "error_message": error_message
    }

    if mode.lower() == "sync":
        parameters = {}
        xml_parameters = xml_response.find("parameters")
        if xml_parameters is not None:
            for parameter in xml_parameters:
                parameters[parameter.find("param-name").text] = parameter.find("param-value").text

            json_response["parameters"] = parameters

    return json_response
