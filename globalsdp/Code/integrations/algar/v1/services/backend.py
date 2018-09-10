"""
Backend services
"""

import logging
import time
from lxml import etree
from application.src.exceptions import InvalidRequestException
from tornado.httpclient import HTTPRequest


# Logging handler
log = logging.getLogger(__name__)


##### SIGNATURE #####
#####################
class SignatureService(object):

    def get_configs(self, settings, la):
        """
        Gets cached configs for signature on application.settings['config'] object

        :param settings: Cache object application.settings['config']
        :param la:: Large Account number
        :return: json
        """

        return {
            'host': settings['config']['algar/v1/host']['value'],
            'url': settings['config']['algar/v1/signature/url']['value'],
            'company_id': settings['config']['algar/v1/company/id']['value'],
            'operation_code': settings['config']['algar/v1/signature/code']['value'],
            'operation_description': settings['config']['algar/v1/signature/description']['value'],
            'auth_type': settings['config']['algar/v1/signature/auth/type']['value'],
            'notification_type': settings['config']['algar/v1/signature/notification/type']['value'],
            'notification_calltype': settings['config']['algar/v1/signature/notification/calltype']['value'],
            'notification_callback': settings['config']['algar/v1/signature/notification/callback']['value'],
            'user': settings['config']['algar/v1/{0}/user'.format(la)]['value'],
            'password': settings['config']['algar/v1/{0}/password'.format(la)]['value'],
            'service_id': settings['config']['algar/v1/{0}/service-id'.format(la)]['value'],
        }

    def get_url(self, configs):
        """
        Gets request URL

        :param configs: Cache object application.settings['config']
        :return: String
        """
        return '{0}/{1}'.format(configs['host'], configs['url'])

    def get_request(self, request_url, headers, body):
        """
        Gets request object

        :param request_url: request URL
        :param headers: request json headers
        :param body: request json body
        :return: HTTPRequest object
        """
        return HTTPRequest(
            url=request_url,
            method="POST",
            body=body,
            request_timeout=10,
            headers=headers)

    def get_body(self, configs, channel_id, la, msisdn, app_specific, interface, subscription_type):
        """
        Builds xml request body

        :param configs: Cache object application.settings['config']
        :param channel_id: Channel id number
        :param la: Large Account number
        :param msisdn: Telephone number
        :param app_specific: App number
        :param interface: Interface number
        :param subscription_type: Subscription type number
        :return: xml
        """

        body = etree.Element('tangram_request',
                             company_id=str(configs['company_id']),
                             service_id=str(configs['service_id']),
                             user=str(configs['user']))
        if interface:
            body.attrib['interface'] = str(interface)

        provisioning = etree.SubElement(body, "provisioning")
        channel = etree.SubElement(provisioning, "channel_id")
        channel.text = str(channel_id)
        operation = etree.SubElement(provisioning, "operation", code=str(configs['operation_code']))
        operation.text = configs['operation_description']
        source = etree.SubElement(provisioning, "source")
        source.text = str(la)
        destination = etree.SubElement(provisioning, "destination")
        destination.text = str(msisdn)
        if subscription_type:
            destination.attrib['subscription_type'] = str(subscription_type)

        authentication = etree.SubElement(provisioning, "authentication", type=str(configs['auth_type']))
        notification = etree.SubElement(provisioning, "notification", type=str(configs['notification_type']),
                                        calltype=str(configs['notification_calltype']))
        notification.text = configs['notification_callback']
        request_datetime = etree.SubElement(provisioning, "request_datetime")
        request_datetime.text = str(int(time.time()))

        if app_specific:
            appspecific = etree.SubElement(provisioning, "app_specific")
            appspecific.text = str(app_specific)

        return etree.tounicode(body)


    def parse_response_to_json(self, xml_response):
        """
        Parses algar's xml response to json

        :param xml_response: xml response body from algar
        :return: Json
        """

        provisioning = xml_response.find("provisioning")
        description = provisioning.find("description")
        destination = provisioning.find("destination")

        try:
            channel_id = provisioning.find("channel_id").text
        except:
            channel_id = ""

        json_response = {
            "signature_status": provisioning.get("code"),
            "channel_id": channel_id,
            "description": {
                "code": description.get("code"),
                "text": description.text
            },
            "destination": {
                "code": destination.get("code"),
                "description": destination.get("description"),
                "value": destination.text
            },
            "response_datetime": provisioning.find("response_datetime").text
        }
        return json_response


##### CANCELLATION #####
########################
class CancellationService(object):

    def get_configs(self, settings, la):
        """
        Gets cached configs for cancellation on application.settings['config'] object

        :param settings: Cache object application.settings['config']
        :param la:: Large Account number
        :return: json
        """
        return {
            'host': settings['config']['algar/v1/host']['value'],
            'url': settings['config']['algar/v1/cancellation/url']['value'],
            'company_id': settings['config']['algar/v1/company/id']['value'],
            'operation_code': settings['config']['algar/v1/cancellation/code']['value'],
            'operation_description': settings['config']['algar/v1/cancellation/description']['value'],
            'user': settings['config']['algar/v1/{0}/user'.format(la)]['value'],
            'password': settings['config']['algar/v1/{0}/password'.format(la)]['value'],
            'service_id': settings['config']['algar/v1/{0}/service-id'.format(la)]['value'],
            'notification_type': settings['config']['algar/v1/cancellation/notification/type']['value'],
            'notification_calltype': settings['config']['algar/v1/cancellation/notification/calltype']['value'],
            'notification_callback': settings['config']['algar/v1/cancellation/notification/callback']['value'],
        }

    def get_url(self, configs):
        """
        Gets request URL

        :param configs: Cache object application.settings['config']
        :return: String
        """
        return '{0}/{1}'.format(configs['host'], configs['url'])

    def get_request(self, request_url, headers, body):
        """
        Gets request object

        :param request_url: request URL
        :param headers: request json headers
        :param body: request json body
        :return: HTTPRequest object
        """
        return HTTPRequest(
            url=request_url,
            method="POST",
            body=body,
            request_timeout=10,
            headers=headers)

    def get_body(self, configs, channel_id, msisdn, interface, subscription_type):
        """
        Builds xml request body

        :param configs: Cache object application.settings['config']
        :param channel_id: Channel id number
        :param msisdn: Telephone number
        :param interface: Interface number
        :param subscription_type: Subscription type number
        :return: xml
        """

        body = etree.Element('tangram_request',
                             company_id=str(configs['company_id']),
                             service_id=str(configs['service_id']),
                             user=str(configs['user']))
        if interface:
            body.attrib['interface'] = str(interface)

        provisioning = etree.SubElement(body, "provisioning")
        operation = etree.SubElement(provisioning, "operation", code=str(configs['operation_code']))
        operation.text = configs['operation_description']
        channel = etree.SubElement(provisioning, "channel_id")
        channel.text = str(channel_id)
        destination = etree.SubElement(provisioning, "destination")
        destination.text = str(msisdn)
        if subscription_type:
            destination.attrib['subscription_type'] = str(subscription_type)

        notification = etree.SubElement(provisioning, "notification", type=str(configs['notification_type']),
                                        calltype=str(configs['notification_calltype']))
        notification.text = configs['notification_callback']
        request_datetime = etree.SubElement(provisioning, "request_datetime")
        request_datetime.text = str(int(time.time()))

        return etree.tounicode(body)

    def parse_response_to_json(self, xml_response):
        """
        Parses algar's xml response to json

        :param xml_response: xml response body from algar
        :return: Json
        """

        provisioning = xml_response.find("provisioning")
        description = provisioning.find("description")
        try:
            destination = provisioning.find("destination")
        except:
            destination = None

        try:
            channel_id = provisioning.find("channel_id").text
        except:
            channel_id = ""

        json_response = {
            "cancellation_status": provisioning.get("code"),
            "channel_id": channel_id,
            "description": {
                "code": description.get("code"),
                "text": description.text
            },
            "response_datetime": provisioning.find("response_datetime").text
        }

        if destination:
            destination_json = {
                "destination": {
                    "code": destination.get("code"),
                    "description": destination.get("description"),
                    "value": destination.text
                }
            }
            json_response.update(destination_json)

        return json_response


##### MT #####
##############
class MtService(object):

    def get_configs(self, settings, la):
        """
        Gets cached configs for MT on application.settings['config'] object

        :param settings: Cache object application.settings['config']
        :param la:: Large Account number
        :return: json
        """
        return {
            'host': settings['config']['algar/v1/host']['value'],
            'url': settings['config']['algar/v1/mt/url']['value'],
            'company_id': settings['config']['algar/v1/company/id']['value'],
            'keep_session': settings['config']['algar/v1/mt/keepsession']['value'],
            'notification_type': settings['config']['algar/v1/mt/notification/type']['value'],
            'notification_calltype': settings['config']['algar/v1/mt/notification/calltype']['value'],
            'notification_callback': settings['config']['algar/v1/mt/notification/callback']['value'],
            'user': settings['config']['algar/v1/{0}/user'.format(la)]['value'],
            'password': settings['config']['algar/v1/{0}/password'.format(la)]['value'],
            'service_id': settings['config']['algar/v1/{0}/service-id'.format(la)]['value'],
        }

    def get_url(self, configs):
        """
        Gets request URL

        :param configs: Cache object application.settings['config']
        :return: String
        """
        return '{0}/{1}'.format(configs['host'], configs['url'])

    def get_request(self, request_url, headers, body):
        """
        Gets request object

        :param request_url: request URL
        :param headers: request json headers
        :param body: request json body
        :return: HTTPRequest object
        """
        return HTTPRequest(
            url=request_url,
            method="POST",
            body=body,
            request_timeout=10,
            headers=headers)

    def get_body(self, configs, la, msisdns, channel_id, message, message_header,
                 validity, schedule, notification, retries, mo_message_id, app_specific, app_request_id):
        """
        Builds xml request body

        :param configs: Cache object application.settings['config']
        :param la: Large Account number
        :param msisdn: Telephone number
        :param channel_id: Channel id number
        :param message: Message text
        :param message_header: Message Header text
        :param validity: Message validity json
        :param schedule: Message schedule json
        :param notification: Message notification
        :param retries: Message retries approach (json)
        :param mo_message_id: MO id number
        :param app_specific: App number
        :param app_request_id: Request id number
        :return: xml
        """

        body = etree.Element('tangram_request',
                             company_id=str(configs['company_id']),
                             service_id=str(configs['service_id']),
                             user=str(configs['user']))
        send = etree.SubElement(body, "send", keep_session=str(configs['keep_session']))
        source = etree.SubElement(send, "source")
        source.text = str(la)
        if type(msisdns) is not list:
            etree.SubElement(send, "destination").text = str(msisdns)
        else:
            for msisdn in msisdns:
                etree.SubElement(send, "destination").text = str(msisdn)
        channel = etree.SubElement(send, "channel_id")
        channel.text = str(channel_id)
        text = etree.SubElement(send, "text", binary="false", udh="", method="")
        text.text = str(message)
        if message_header:
            text_header = etree.SubElement(send, "text", binary="false", udh="", method="truncate")
            text_header.text = str(message_header)

        user_data_header = etree.SubElement(send, "user_data_header")
        user_data_header.text = ""

        try:
            validity_tag = etree.SubElement(send, "validity")
            validity_tag.text = str(validity['validity'])
            validity_tag.attrib['relative'] = str(validity['relative'])
        except KeyError:
            raise InvalidRequestException("Validity parameter must be a key/value element containing the following "
                                          "keys: 'relative': 'boolean' and 'validity': 'int(seconds) or date'")
        try:
            schedule_tag = etree.SubElement(send, "schedule")
            schedule_tag.text = str(schedule['schedule'])
            schedule_tag.attrib['relative'] = str(schedule['relative'])
        except KeyError:
            raise InvalidRequestException("Schedule parameter must be a key/value element containing the following "
                                          "keys: 'relative': 'boolean' and 'schedule': 'int(seconds) or date'")
        notification = etree.SubElement(send, "notification", type=str(configs['notification_type']),
                                        calltype=str(configs['notification_calltype']))
        notification.text = str(configs['notification_callback'])

        package = etree.SubElement(send, "package", external_id="", name="", description="", interface="",owner_ctn="",
                                   copyright="", contract="")

        try:
            retries_tag = etree.SubElement(send, "retries")
            retries_tag.attrib['max'] = str(retries['max'])
            retries_tag.attrib['interval'] = str(retries['interval'])
        except KeyError:
            raise InvalidRequestException("Retries parameter must be a key/value element containing the following "
                                          "keys: 'max': 'int' and 'interval': 'int(seconds)'")

        service_type = etree.SubElement(send, "service_type")
        service_type.text = ""

        mo_message_id_tag = etree.SubElement(send, "mo_message_id")
        mo_message_id_tag.text = str(mo_message_id)

        app_specific_tag = etree.SubElement(send, "app_specific")
        app_specific_tag.text = str(app_specific)

        app_request_id_tag = etree.SubElement(send, "app_request_id")
        app_request_id_tag.text = str(app_request_id)

        request_datetime = etree.SubElement(send, "request_datetime")
        request_datetime.text = str(int(time.time()))

        xml_declaration = """<?xml version="1.0" encoding="ISO-8859-1"?>"""

        return xml_declaration + etree.tounicode(body)


    def parse_response_to_json(self, xml_response):
        """
        Parses algar's xml response to json

        :param xml_response: xml response body from algar
        :return: Json
        """

        send = xml_response.find("send")

        json_response = {
            "mt_status": send.get("code"),
            "company_id": xml_response.get("company_id"),
            "service_id": xml_response.get("service_id")
        }
        return json_response


##### BILLING #####
###################
class BillingService(object):

    def get_configs(self, settings, la):
        """
        Gets cached configs for billing on application.settings['config'] object

        :param settings: Cache object application.settings['config']
        :param la:: Large Account number
        :return: json
        """
        return {
            'host': settings['config']['algar/v1/host']['value'],
            'url': settings['config']['algar/v1/billing/url']['value'],
            'company_id': settings['config']['algar/v1/company/id']['value'],
            'operation_code': settings['config']['algar/v1/billing/code']['value'],
            'operation_description': settings['config']['algar/v1/billing/description']['value'],
            'transaction_type': settings['config']['algar/v1/billing/transaction/type']['value'],
            'transaction_description': settings['config']['algar/v1/billing/transaction/description']['value'],
            'user': settings['config']['algar/v1/{0}/user'.format(la)]['value'],
            'password': settings['config']['algar/v1/{0}/password'.format(la)]['value'],
            'service_id': settings['config']['algar/v1/{0}/service-id'.format(la)]['value'],
        }

    def get_url(self, configs):
        """
        Gets request URL

        :param configs: Cache object application.settings['config']
        :return: String
        """
        return '{0}/{1}'.format(configs['host'], configs['url'])

    def get_request(self, request_url, headers, body):
        """
        Gets request object

        :param request_url: request URL
        :param headers: request json headers
        :param body: request json body
        :return: HTTPRequest object
        """
        return HTTPRequest(
            url=request_url,
            method="POST",
            body=body,
            request_timeout=10,
            headers=headers)

    def get_body(self, configs, channel_id, la, msisdn, item, subscription_type, interface):
        """
        Builds xml request body

        :param configs: Cache object application.settings['config']
        :param channel_id: Channel id number
        :param la: Large Account number
        :param msisdn: Telephone number
        :param item: item json specification
        :param app_specific: App number
        :param app_request_id: Request id number
        :return: xml
        """

        body = etree.Element('tangram_request',
                             company_id=str(configs['company_id']),
                             service_id=str(configs['service_id']),
                             user=str(configs['user']))
        if interface:
            body.attrib['interface'] = str(interface)

        billing = etree.SubElement(body, "billing")
        channel = etree.SubElement(billing, "channel_id")
        channel.text = str(channel_id)
        operation = etree.SubElement(billing, "operation", code=str(configs['operation_code']))
        operation.text = str(configs['operation_description'])
        transaction = etree.SubElement(billing, "transaction", type=str(configs['transaction_type']))
        transaction.text = str(configs['transaction_description'])
        source_ = etree.SubElement(billing, "source")
        source_.text = str(la)
        destination = etree.SubElement(billing, "destination")
        destination.text = str(msisdn)
        if subscription_type:
            destination.attrib['subscription_type'] = str(subscription_type)

        if item:
            if type(item) is not dict:
                log.error("'Item parameter is an invalid JSON object: {0}")
                raise InvalidRequestException({"success": 0, "message": "Item parameter is an invalid JSON object"})
            item_ = etree.SubElement(billing, "item")
            try:
                if item['external_id']:
                    external_id = etree.SubElement(item_, "external_id")
                    external_id.text = str(item['external_id'])
            except KeyError:
                pass
            try:
                if item['name']:
                    name = etree.SubElement(item_, "name")
                    name.text = str(item['name'])
            except KeyError:
                pass
            try:
                if item['description']:
                    description = etree.SubElement(item_, "description")
                    description.text = str(item['description'])
            except KeyError:
                pass
            try:
                if item['interface']:
                    try:
                        interface_code = item['interface']['code']
                        interface_text = item['interface']['text']
                    except:
                        raise InvalidRequestException({"success": 0, "message": "Interface parameter must be a key/value element "
                                                "containing the following keys: 'code': 'int' and 'text': 'string'"})
                    interface = etree.SubElement(item_, "interface", code=str(interface_code))
                    interface.text = str(interface_text)
            except KeyError:
                pass

            try:
                if item['copyright']:
                    copyright = etree.SubElement(item_, "copyright")
                    copyright.text = str(item['copyright'])
            except KeyError:
                pass
            try:
                if item['value']:
                    value = etree.SubElement(item_, "value")
                    value.text = str(item['value'])
            except KeyError:
                pass
            try:
                if item['size']:
                    size = etree.SubElement(item_, "size")
                    size.text = str(item['size'])
            except KeyError:
                pass
            try:
                if item['owner_ctn']:
                    owner_ctn = etree.SubElement(item_, "owner_ctn")
                    owner_ctn.text = str(item['owner_ctn'])
            except KeyError:
                pass
            try:
                if item['ex_info']:
                    ex_info = etree.SubElement(item_, "ex_info")
                    ex_info.text = str(item['ex_info'])
            except KeyError:
                pass
            try:
                if item['original_request_id']:
                    original_request_id = etree.SubElement(item_, "original_request_id")
                    original_request_id.text = str(item['original_request_id'])
            except KeyError:
                pass
            try:
                if item['session_id']:
                    session_id = etree.SubElement(item_, "session_id")
                    session_id.text = str(item['session_id'])
            except KeyError:
                pass
            try:
                if item['app_specific']:
                    app_specific = etree.SubElement(item_, "app_specific")
                    app_specific.text = str(item['app_specific'])
            except KeyError:
                pass

            try:
                if item['app_request_id']:
                    app_request_id = etree.SubElement(item_, "app_request_id")
                    app_request_id.text = str(item['app_request_id'])
            except KeyError:
                pass

        request_datetime = etree.SubElement(billing, "request_datetime")
        request_datetime.text = str(int(time.time()))

        return etree.tounicode(body)

    def parse_response_to_json(self, xml_response):
        """
        Parses algar's xml response to json

        :param xml_response: xml response body from algar
        :return: Json
        """

        billing = xml_response.find("billing")
        destination = billing.find("destination")
        description = billing.find("description")

        try:
            company_id = xml_response.get("company_id")
        except:
            company_id = ""

        try:
            service_id = xml_response.get("service_id")
        except:
            service_id = ""

        try:
            session_id = destination.get("session_id")
        except:
            session_id = ""

        try:
            request_id = destination.find("request_id").text
        except:
            request_id = ""

        json_response = {
            "billing_status": billing.get("code"),
            "company_id": company_id,
            "service_id": service_id,
            "destination": {
                "code": destination.get("code"),
                "description": destination.get("description"),
                "session_id": session_id,
                "request_id": request_id,
                "value": destination.text
            },
            "description": {
                "code": description.get("code"),
                "text": description.text
            },
            "response_datetime": billing.find("response_datetime").text
        }
        return json_response


##### GENERAL #####
###################
def response_has_errors(response_content):
    """
    Checks if algar's response contains some error message or Bad Request
    (An "error" tag is returned inside response XML)

    :param response_content: response xml
    :return: String or None
    """

    error_response = response_content.find('error')
    if error_response is not None:
        return error_response.find('description').text

    return None

def get_headers(configs):
    """
    Builds request headers

    :param configs: Cache object application.settings['config']
    :return: json
    """
    return {
        'TANGRAM_USER': configs['user'],
        'TANGRAM_PASSWORD': configs['password'],
        'Content-Type': 'application/xml'
    }



