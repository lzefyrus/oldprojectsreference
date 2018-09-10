# -*- encoding: utf-8 -*-

import os
import json
import base64
import boto3
import datetime
from lxml import etree
from tornado.httpclient import HTTPRequest
from integrations.tim.v1.utils import ssl


class CancellationService(object):
    """
    Cancellation service.
    """

    @staticmethod
    def get_configs(settings):
        """
        Returns useful configs.
        :param settings: dict
        :return: dict
        """
        return {
            'host': settings['config']['tim/v1/host']['value'],
            'url': settings['config']['tim/v1/cancellation/url']['value'],
            'bearertoken': settings['config']['tim/v1/bearertoken']['value'],
        }

    @staticmethod
    def get_token(configs, subscription_id):
        """
        Returns authorization token.
        :param configs: dict
        :param subscription_id: str
        :return: str
        """
        return '{0} {1}'.format(configs['bearertoken'], subscription_id)

    @staticmethod
    def get_url(configs, subscription_id):
        """
        Returns request URL.
        :param configs: dict
        :param subscription_id: str
        :return: str
        """
        return '{0}/{1}/{2}'.format(configs['host'], configs['url'], subscription_id)

    @staticmethod
    def get_header(token):
        """
        Returns request header.
        :param token: str
        :return: dict
        """
        return {'Authorization': token, 'Accept': 'application/json', 'Content-Type': 'application/json'}

    @staticmethod
    def get_request(request_url, request_header):
        """
        Returns request object.
        :param request_url: str
        :param request_header: dict
        :return: tornado.httpclient.HTTPRequest
        """
        return HTTPRequest(
            url=request_url,
            method="DELETE",
            request_timeout=30,
            headers=request_header,
            ca_certs=ssl.get_cert_file(),
            validate_cert=ssl.verify(),
        )


class MtService(object):
    """
    MT service.
    """

    @staticmethod
    def get_configs(settings):
        """
        Returns useful configs.
        :param settings: dict
        :return: dict
        """
        return {
            'host': settings['config']['tim/v1/host']['value'],
            'url': settings['config']['tim/v1/mt/url']['value'],
            'bearertoken': settings['config']['tim/v1/bearertoken']['value'],
            'basictoken': settings['config']['tim/v1/basictoken']['value'],
            'user': settings['config']['tim/v1/user']['value'],
            'password': settings['config']['tim/v1/password']['value'],
        }

    @staticmethod
    def get_token(configs, subscription_id, client_correlator):
        """
        Returns authorization token.
        :param configs: dict
        :param subscription_id: str
        :param client_correlator: str
        :return: str
        """
        if not client_correlator:
            return '{0} {1}'.format(configs['bearertoken'], subscription_id)

        credentials = "{0}:{1}".format(configs['user'], configs['password'])
        based64 = base64.b64encode(credentials.encode('utf8')).decode('utf8')
        return '{0} {1}'.format(configs['basictoken'], based64)

    @staticmethod
    def get_url(configs, la):
        """
        Returns request URL.
        :param configs: dict
        :param la: int
        :return: str
        """
        request_url = '{0}/{1}'.format(configs['host'], configs['url'])
        return request_url.replace('SENDERADDRESS', "tel:{0}".format(str(la)))

    @staticmethod
    def get_body(msisdn, la, message, client_correlator):
        """
        Returns request body.
        :param msisdn: int
        :param la: int
        :param message: str
        :param client_correlator: str
        :return: dict
        """
        body = {
            "outboundSMSMessageRequest": {
                "address": ["tel:{0}".format(msisdn)],
                "senderAddress": "tel:{0}".format(la),
                "outboundSMSTextMessage": {
                    "message": message
                }
            }
        }
        if client_correlator:
            body['outboundSMSMessageRequest']['clientCorrelator'] = client_correlator

        return body

    @staticmethod
    def get_header(token):
        """
        Returns request header.
        :param token: str
        :return: dict
        """
        return {'Authorization': token, 'Accept': 'application/json', 'Content-Type': 'application/json'}

    @staticmethod
    def get_request(request_url, request_body, request_header):
        """
        Returns request object.
        :param request_url: str
        :param request_body: dict
        :param request_header: dict
        :return: tornado.httpclient.HTTPRequest
        """
        return HTTPRequest(
            url=request_url,
            method="POST",
            request_timeout=30,
            headers=request_header,
            body=json.dumps(request_body),
            ca_certs=ssl.get_cert_file(),
            validate_cert=ssl.verify(),
        )

    @staticmethod
    def replace_la(la):
        """
        Replaces LA according to environment.
        :param la: int
        :return: int
        """
        if os.environ['GATEWAY_ENV'] == 'prod':
            return la
        if la in ['5511', '5512', '5515']:
            return '323'
        if la == '5503':
            return '324'
        return la


class BillingService(object):
    """
    Billing service.
    """

    @staticmethod
    def get_configs(settings):
        """
        Returns useful configs.
        :param settings: dict
        :return: dict
        """
        return {
            'host': settings['config']['tim/v1/host']['value'],
            'url': settings['config']['tim/v1/billing/url']['value'],
            'bearertoken': settings['config']['tim/v1/bearertoken']['value'],
        }

    @staticmethod
    def get_token(configs, subscription_id):
        """
        Returns authorization token.
        :param configs: dict
        :param subscription_id: str
        :return: str
        """
        return '{0} {1}'.format(configs['bearertoken'], subscription_id)

    @staticmethod
    def get_url(configs, msisdn):
        """
        Returns request URL.
        :param configs: dict
        :param msisdn: int
        :return: str
        """
        request_url = '{0}/{1}'.format(configs['host'], configs['url'])
        return request_url.replace('ENDUSERID', "tel:{0}".format(str(msisdn)))

    @staticmethod
    def get_header(token):
        """
        Returns request header.
        :param token: str
        :return: dict
        """
        return {'Authorization': token, 'Accept': 'application/json', 'Content-Type': 'application/json'}

    @staticmethod
    def get_body(msisdn, description, amount, code, tax_amount, mandate_id, service_id, product_id,
                 transaction_status, reference_code):
        """
        Returns request body.
        :param msisdn:
        :param description:
        :param amount:
        :param code:
        :param tax_amount:
        :param mandate_id:
        :param service_id:
        :param product_id:
        :param transaction_status:
        :param reference_code:
        :return: dict
        """
        return {
            "amountTransaction": {
                "endUserId": "tel:{0}".format(msisdn),
                "paymentAmount": {
                    "chargingInformation": {
                        "description": "{0}".format(description),
                        "amount": "{0}".format(amount),
                        "code": "{0}".format(code)
                    },
                    "chargingMetaData": {
                        "taxAmount": "{0}".format(tax_amount),
                        "mandateId": "{0}".format(mandate_id),
                        "serviceId": "{0}".format(service_id),
                        "productId": "{0}".format(product_id)
                    }
                },
                "transactionOperationStatus": "{0}".format(transaction_status),
                "referenceCode": "{0}".format(reference_code)
            }
        }

    @staticmethod
    def get_request(request_url, request_body, request_header):
        """
        Returns request object.
        :param request_url: str
        :param request_body: dict
        :param request_header: dict
        :return: tornado.httpclient.HTTPRequest
        """
        return HTTPRequest(
            url=request_url,
            method="POST",
            request_timeout=30,
            headers=request_header,
            body=json.dumps(request_body),
            ca_certs=ssl.get_cert_file(),
            validate_cert=ssl.verify(),
        )

    @staticmethod
    def get_account_type(headers):
        """
        Returns account type post(1) or pre(0) paid.
        :param headers: dict
        :return: str
        """
        try:
            xplugin = headers["X-Plugin-Param-Values"]
            start_tag = xplugin.find('<')
            end_tag = xplugin.rfind('>')+1
            xml = etree.XML(xplugin[start_tag:end_tag])
            account_type = xml.find('Service-Parameter-Info').find('Service-Parameter-Value').text

        except:
            account_type = ""

        return account_type

    @staticmethod
    def get_resource_url(json_response):
        """
        Returns URL used to check billing result.
        :param json_response: dict
        :return: str
        """
        try:
            resource_url = json_response["amountTransaction"]["resourceURL"]
        except:
            resource_url = ""

        return resource_url

    @staticmethod
    def get_code(json_response):
        """
        Returns exception code.
        :param json_response: dict
        :return: str
        """
        try:
            if "serviceException" in json_response["requestError"]:
                exception = json_response["requestError"]["serviceException"]
                if exception["messageId"] == "SVC0270" and "variables" in exception:
                    if "DIAMETER" in exception["variables"][0].upper():
                        return exception["variables"][0]

                return exception["messageId"]

            if "policyException" in json_response["requestError"]:
                exception = json_response["requestError"]["policyException"]
                if exception["messageId"] == "SVC0270" and "variables" in exception:
                    if "DIAMETER" in exception["variables"][0].upper():
                        return exception["variables"][0]

                return exception["messageId"]

            return ""

        except:
            return ""

    @classmethod
    def add_to_file(cls, settings, body, success):
        """
        Adds billing information to a file.
        :param settings: dict
        :param body: dict
        :param success: int
        :return: bool
        """
        try:
            path = settings["config"]["tim/v1/billing/file/path"]["value"]
            data = cls.get_formated_parameters(body, success)

            with open(path, "a") as file:
                file.write(data)
            return True

        except:
            return False

    @classmethod
    def add_to_stream(cls, settings, body, success):
        """
        Adds billing information to a stream service (Kinesis).
        :param settings: dict
        :param body: dict
        :param success: int
        :return: bool
        """
        try:
            kinesis = boto3.client(
                'kinesis',
                aws_access_key_id=settings["config"]["tim/v1/billing/kinesis/aws_access_key_id"]["value"],
                aws_secret_access_key=settings["config"]["tim/v1/billing/kinesis/aws_secret_access_key"]["value"],
                region_name=settings["config"]["tim/v1/billing/kinesis/region_name"]["value"]
            )

            response = kinesis.get_shard_iterator(
                StreamName=settings["config"]["tim/v1/billing/kinesis/stream"]["value"],
                ShardId=settings["config"]["tim/v1/billing/kinesis/shard"]["value"],
                ShardIteratorType=settings["config"]["tim/v1/billing/kinesis/iterator"]["value"],
            )

            response = kinesis.put_record(
                StreamName=settings["config"]["tim/v1/billing/kinesis/stream"]["value"],
                Data=cls.get_formated_parameters(body, success),
                PartitionKey=response['ShardIterator'],
            )

            return True if 'ShardId' in response else False

        except:
            return False

    @staticmethod
    def get_formated_parameters(body, success):
        """
        Formats billing information to be saved to the file/stream.
        :param body: dict
        :param success: int
        :return: str
        """
        try:
            return "{0}|{1}|{2}|{3}|{4}|{5}|{6}|{7}|{8}|{9}|{10}|{11}\n".format(
                body['amount'], body['code'], body['msisdn'], body['mandate_id'],
                body['product_id'], body['reference_code'], body['service_id'],
                body['tax_amount'], body['transaction_status'], body['subscription_id'],
                datetime.datetime.now(), success
            )

        except:
            return ""


class BillingStatusService(object):
    """
    Billing service.
    """

    @staticmethod
    def get_configs(settings):
        """
        Returns useful configs.
        :param settings: dict
        :return: dict
        """
        return {
            'host': settings['config']['tim/v1/host']['value'],
            'url': settings['config']['tim/v1/billing/status/url']['value'],
        }

    @staticmethod
    def get_url(configs, msisdn, transaction_id):
        """
        Returns request URL.
        :param configs: dict
        :param msisdn: int
        :param transaction_id: str
        :return: str
        """
        request_url = '{0}/{1}'.format(configs['host'], configs['url'])
        request_url = request_url.replace('ENDUSERID', str(msisdn))
        return request_url.replace('TRANSACTIONID', str(transaction_id))

    @staticmethod
    def get_header():
        """
        Returns request header.
        :return: dict
        """
        return {'Accept': 'application/json', 'Content-Type': 'application/json'}

    @staticmethod
    def get_request(request_url, request_header):
        """
        Returns request object.
        :param request_url: str
        :param request_header: dict
        :return: tornado.httpclient.HTTPRequest
        """
        return HTTPRequest(
            url=request_url,
            method="GET",
            request_timeout=30,
            headers=request_header,
            ca_certs=ssl.get_cert_file(),
            validate_cert=ssl.verify(),
        )


class MigrationService(object):
    """
    Migration service.
    """

    @staticmethod
    def get_configs(settings):
        """
        Returns useful configs.
        :param settings: dict
        :return: dict
        """
        return {
            'host': settings['config']['tim/v1/host']['value'],
            'url': settings['config']['tim/v1/migration/url']['value'],
            'user': settings['config']['tim/v1/migration/user']['value'],
            'password': settings['config']['tim/v1/migration/password']['value'],
            'basictoken': settings['config']['tim/v1/basictoken']['value'],
        }

    @staticmethod
    def get_token(configs):
        """
        Returns authorization token.
        :param configs: dict
        :return: str
        """
        credentials = "{0}:{1}".format(configs['user'], configs['password'])
        based64 = base64.b64encode(credentials.encode('utf8')).decode('utf8')
        return '{0} {1}'.format(configs['basictoken'], based64)

    @staticmethod
    def get_url(configs):
        """
        Returns request URL.
        :param configs: dict
        :return: str
        """
        return '{0}/{1}'.format(configs['host'], configs['url'])

    @staticmethod
    def get_header(token):
        """
        Returns request header.
        :param token: dict
        :return: dict
        """
        return {'Authorization': token, 'Accept': 'application/json', 'Content-Type': 'application/json'}

    @staticmethod
    def get_body(msisdn, application_id):
        """
        Returns request body.
        :param msisdn:
        :param application_id:
        :return:
        """
        return {"subscription": {"msisdn": msisdn, "applicationId": application_id}}

    @staticmethod
    def get_request(request_url, request_body, request_header):
        """
        Returns request object.
        :param request_url: str
        :param request_body: dict
        :param request_header: dict
        :return: tornado.httpclient.HTTPRequest
        """
        return HTTPRequest(
            url=request_url,
            method="POST",
            request_timeout=30,
            headers=request_header,
            body=json.dumps(request_body),
            ca_certs=ssl.get_cert_file(),
            validate_cert=ssl.verify(),
        )
